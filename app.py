#!/usr/bin/env python3
"""
Sitespeed.io Runner Service
Provides HTTP API to run sitespeed.io scans via Docker
"""

import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
REPORTS_DIR = Path("/reports")
HOST_REPORTS_DIR = os.getenv("HOST_REPORTS_DIR", "/srv/docker/n8n/local_files/sitespeed-reports")
SITESPEED_IMAGE = os.getenv("SITESPEED_IO_CONTAINER", "sitespeedio/sitespeed.io:38.6.0-plus1")

# In-memory store for scan status
scans: Dict[str, Dict] = {}


def parse_sitespeed_report(scan_id: str) -> Optional[Dict]:
    """Parse the sitespeed.io report and return a summary."""
    report_dir = REPORTS_DIR / scan_id
    
    if not report_dir.exists():
        return None
    
    # Build response with available data
    # Handle case where scan might not be in memory (after restart)
    scan_data = scans.get(scan_id, {})
    summary = {
        "scanId": scan_id,
        "url": scan_data.get("url", ""),
        "timestamp": scan_data.get("started_at", ""),
        "completed_at": scan_data.get("completed_at", ""),
        "reports": {},
        "metrics": {}
    }
    
    # Check for HTML report
    index_html = report_dir / "index.html"
    if index_html.exists():
        summary["reports"]["html"] = f"/reports/{scan_id}/index.html"
    
    # Check for detailed HTML
    detailed_html = report_dir / "detailed.html"
    if detailed_html.exists():
        summary["reports"]["detailed_html"] = f"/reports/{scan_id}/detailed.html"
    
    # Look for JSON data from analysisstorer plugin
    # Individual page data is stored in data/pages/$PAGE/data/
    data_dir = report_dir / "data"
    if data_dir.exists():
        # Look for browsertime page summary
        browsertime_files = list(data_dir.glob("**/browsertime.pageSummary.json"))
        if browsertime_files:
            try:
                with open(browsertime_files[0], 'r') as f:
                    browsertime_data = json.load(f)
                
                # Extract metrics from browsertime data
                summary["metrics"]["browsertime"] = {
                    "statistics": browsertime_data.get("statistics", {}),
                    "info": browsertime_data.get("info", {})
                }
                
                summary["reports"]["browsertime_json"] = f"/reports/{scan_id}/{browsertime_files[0].relative_to(report_dir)}"
            except Exception as e:
                app.logger.warning(f"Could not parse browsertime.pageSummary.json for {scan_id}: {e}")
        
        # Look for coach page summary
        coach_files = list(data_dir.glob("**/coach.pageSummary.json"))
        if coach_files:
            try:
                with open(coach_files[0], 'r') as f:
                    coach_data = json.load(f)
                
                summary["metrics"]["coach"] = {
                    "advice": coach_data.get("advice", {}),
                    "score": coach_data.get("advice", {}).get("score")
                }
                
                summary["reports"]["coach_json"] = f"/reports/{scan_id}/{coach_files[0].relative_to(report_dir)}"
            except Exception as e:
                app.logger.warning(f"Could not parse coach.pageSummary.json for {scan_id}: {e}")
        
        # Look for pagexray page summary
        pagexray_files = list(data_dir.glob("**/pagexray.pageSummary.json"))
        if pagexray_files:
            try:
                with open(pagexray_files[0], 'r') as f:
                    pagexray_data = json.load(f)
                
                summary["metrics"]["pagexray"] = {
                    "transferSize": pagexray_data.get("transferSize"),
                    "contentSize": pagexray_data.get("contentSize"),
                    "requests": pagexray_data.get("requests"),
                    "contentTypes": pagexray_data.get("contentTypes", {})
                }
                
                summary["reports"]["pagexray_json"] = f"/reports/{scan_id}/{pagexray_files[0].relative_to(report_dir)}"
            except Exception as e:
                app.logger.warning(f"Could not parse pagexray.pageSummary.json for {scan_id}: {e}")
    
    # Look for HAR file
    har_files = list(report_dir.glob("**/browsertime.har"))
    if har_files:
        summary["reports"]["har"] = f"/reports/{scan_id}/{har_files[0].relative_to(report_dir)}"
    
    # Check for video
    video_files = list(report_dir.glob("**/video/*.mp4"))
    if video_files:
        summary["reports"]["video"] = f"/reports/{scan_id}/{video_files[0].relative_to(report_dir)}"
    
    # Check for screenshots
    screenshots = list(report_dir.glob("**/screenshots/**/*.png"))
    if screenshots:
        summary["reports"]["screenshots"] = [
            f"/reports/{scan_id}/{s.relative_to(report_dir)}" for s in screenshots[:5]
        ]
    
    return summary if summary["reports"] or summary["metrics"] else None


def run_sitespeed_scan(scan_id: str, url: str, extra_args: list):
    """Run sitespeed.io scan in a separate thread."""
    try:
        scans[scan_id]["status"] = "running"
        
        output_dir = f"/reports/{scan_id}"
        
        # Build docker command
        # Use HOST_REPORTS_DIR because docker socket runs containers on the host
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{HOST_REPORTS_DIR}:/sitespeed.io",
            SITESPEED_IMAGE,
            url,
            "--outputFolder", scan_id,
            "--plugins.add", "analysisstorer"  # Enable JSON output
        ]
        
        # Add extra arguments if provided
        if extra_args:
            docker_cmd.extend(extra_args)
        
        app.logger.info(f"Running command: {' '.join(docker_cmd)}")
        
        # Run the command
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            scans[scan_id]["status"] = "completed"
            scans[scan_id]["completed_at"] = datetime.utcnow().isoformat()
            scans[scan_id]["output"] = result.stdout
            app.logger.info(f"Scan {scan_id} completed successfully")
        else:
            scans[scan_id]["status"] = "failed"
            scans[scan_id]["error"] = result.stderr
            app.logger.error(f"Scan {scan_id} failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        scans[scan_id]["status"] = "failed"
        scans[scan_id]["error"] = "Scan timeout (10 minutes exceeded)"
        app.logger.error(f"Scan {scan_id} timed out")
    except Exception as e:
        scans[scan_id]["status"] = "failed"
        scans[scan_id]["error"] = str(e)
        app.logger.error(f"Scan {scan_id} error: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "sitespeed-runner"})


@app.route('/run-sitespeed', methods=['POST'])
def run_sitespeed():
    """
    Start a new sitespeed.io scan.
    
    Request body:
    {
        "url": "https://example.com",
        "options": ["-b", "firefox", "--mobile", "--video"]  // optional
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    
    url = data['url']
    extra_args = data.get('options', [])
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return jsonify({"error": "URL must start with http:// or https://"}), 400
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())
    
    # Initialize scan record
    scans[scan_id] = {
        "scanId": scan_id,
        "url": url,
        "status": "queued",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
        "output": None
    }
    
    # Start scan in background thread
    thread = threading.Thread(
        target=run_sitespeed_scan,
        args=(scan_id, url, extra_args),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        "scanId": scan_id,
        "status": "queued",
        "statusUrl": f"/status/{scan_id}",
        "reportUrl": f"/report/{scan_id}"
    }), 202


@app.route('/status/<scan_id>', methods=['GET'])
def get_status(scan_id: str):
    """Get the status of a scan."""
    if scan_id not in scans:
        return jsonify({"error": "Scan not found"}), 404
    
    scan = scans[scan_id]
    
    response = {
        "scanId": scan_id,
        "status": scan["status"],
        "url": scan["url"],
        "started_at": scan["started_at"],
        "completed_at": scan.get("completed_at")
    }
    
    if scan["status"] == "failed":
        response["error"] = scan.get("error")
    elif scan["status"] == "completed":
        response["reportUrl"] = f"/report/{scan_id}"
    
    return jsonify(response)


@app.route('/report/<scan_id>', methods=['GET'])
def get_report(scan_id: str):
    """Get the parsed report for a completed scan."""
    # Check if report exists on disk (works even after restart)
    report_dir = REPORTS_DIR / scan_id
    if not report_dir.exists():
        return jsonify({"error": "Scan not found"}), 404
    
    # If scan is in memory, check its status
    if scan_id in scans:
        scan = scans[scan_id]
        if scan["status"] != "completed":
            return jsonify({
                "error": f"Report not available. Scan status: {scan['status']}"
            }), 400
    
    # Parse and return the report
    report = parse_sitespeed_report(scan_id)
    
    if report is None:
        return jsonify({
            "error": "Report file not found",
            "scanId": scan_id,
            "hint": "Check if sitespeed.io generated output files"
        }), 404
    
    return jsonify(report)


@app.route('/scans', methods=['GET'])
def list_scans():
    """List all scans."""
    scan_list = []
    for scan_id, scan_data in scans.items():
        scan_list.append({
            "scanId": scan_id,
            "url": scan_data["url"],
            "status": scan_data["status"],
            "started_at": scan_data["started_at"]
        })
    
    return jsonify({"scans": scan_list, "total": len(scan_list)})


if __name__ == '__main__':
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5679, debug=False)

