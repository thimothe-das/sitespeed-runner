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
from typing import Dict, List, Optional

from flask import Flask, jsonify, request


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO 8601 with milliseconds and Z suffix."""
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

app = Flask(__name__)

# Configuration
REPORTS_DIR = Path("/reports")
HOST_REPORTS_DIR = os.getenv("HOST_REPORTS_DIR", "/srv/docker/n8n/local_files/sitespeed-reports")
HOST_SCRIPTS_DIR = os.getenv("HOST_SCRIPTS_DIR", "/srv/docker/n8n/sitespeed-runner/scripts")
SITESPEED_IMAGE = os.getenv("SITESPEED_IO_CONTAINER", "sitespeedio/sitespeed.io:38.6.0-plus1")

# Browser-side JS that removes full-screen overlays (age gates, cookie banners, etc.)
OVERLAY_REMOVAL_JS = r"""
(function() {
  var vw = window.innerWidth, vh = window.innerHeight, removed = 0;

  // Remove fixed/absolute elements with high z-index covering >80% of viewport
  var allEls = document.querySelectorAll('div, section, dialog, aside, [role="dialog"], [role="alertdialog"]');
  for (var i = 0; i < allEls.length; i++) {
    var el = allEls[i], style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (style.position !== 'fixed' && style.position !== 'absolute') continue;
    var z = parseInt(style.zIndex) || 0;
    if (z < 10) continue;
    var rect = el.getBoundingClientRect();
    if (rect.width >= vw * 0.8 && rect.height >= vh * 0.8) { el.remove(); removed++; }
  }

  // Remove backdrop / overlay elements
  var backdrops = document.querySelectorAll(
    '.modal-backdrop, .overlay-backdrop, .popup-overlay, .popup-voile, ' +
    '[class*="backdrop"], [class*="overlay"]:not(nav):not(header)'
  );
  for (var b = 0; b < backdrops.length; b++) {
    var bs = window.getComputedStyle(backdrops[b]);
    if ((bs.position === 'fixed' || bs.position === 'absolute') && (parseInt(bs.zIndex) || 0) >= 10) {
      backdrops[b].remove(); removed++;
    }
  }

  // Restore scrolling
  document.documentElement.style.overflow = '';
  document.body.style.overflow = '';
  document.documentElement.style.position = '';
  document.body.style.position = '';
  document.body.classList.remove('modal-open', 'no-scroll', 'noscroll', 'overflow-hidden', 'popup-open');

  return removed;
})();
""".strip()


def generate_age_gate_script(url: str) -> str:
    """Generate a sitespeed.io script that navigates to URL, removes overlays, then measures."""
    # json.dumps produces a safely escaped JS string literal (with quotes)
    safe_url = json.dumps(url)
    js_code = OVERLAY_REMOVAL_JS.replace('`', '\\`').replace('${', '\\${')
    return f"""'use strict';

module.exports = async function(context, commands) {{
  var url = {safe_url};

  // 1. Navigate to the URL (triggers any age gate / overlay)
  await commands.navigate(url);

  // 2. Wait for overlays to fully render
  await commands.wait.byTime(3000);

  // 3. Remove all full-screen overlays from the DOM
  await commands.js.run(`{js_code}`);

  // 4. Brief wait for DOM to settle
  await commands.wait.byTime(1000);

  // 5. Measure the now-clean page (no reload, measures current state)
  return commands.measure.start(url);
}};
"""

# In-memory store for scan status
scans: Dict[str, Dict] = {}


def safe_get(data: Dict, *keys, default=None):
    """Safely navigate nested dictionaries."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def remove_null_values(data):
    """
    Recursively remove keys with None values from dictionaries.
    Also handles lists containing dictionaries.
    """
    if isinstance(data, dict):
        return {
            key: remove_null_values(value)
            for key, value in data.items()
            if value is not None and remove_null_values(value) != {}
        }
    elif isinstance(data, list):
        return [
            remove_null_values(item)
            for item in data
            if item is not None
        ]
    else:
        return data


def parse_page_metrics(page_dir: Path) -> Optional[Dict]:
    """
    Parse metrics for a single page directory.
    Returns standardized metrics structure for the requested fields.
    """
    metrics = {
        "page": str(page_dir.name),
        "browsertime": {
            "fullyLoaded": None,
            "firstContentfulPaint": None,
            "largestContentfulPaint": None
        },
        "coach": {
            "score": None,
            "performance": None,
            "accessibility": None,
            "bestPractice": None,
            "privacy": None
        },
        "lighthouse": {
            "performance": None,
            "seo": None,
            "bestPractices": None,
            "accessibility": None,
            "fullyLoaded": None,
            "firstContentfulPaint": None,
            "largestContentfulPaint": None
        }
    }
    
    # Parse browsertime data
    browsertime_file = page_dir / "data" / "browsertime.pageSummary.json"
    if browsertime_file.exists():
        try:
            with open(browsertime_file, 'r') as f:
                bt_data = json.load(f)
            
            stats = bt_data.get("statistics", {})
            timings = stats.get("timings", {})
            
            # Fully loaded time
            metrics["browsertime"]["fullyLoaded"] = safe_get(timings, "fullyLoaded", "median")
            
            # First Contentful Paint
            metrics["browsertime"]["firstContentfulPaint"] = safe_get(timings, "paintTiming", "first-contentful-paint", "median")
            if metrics["browsertime"]["firstContentfulPaint"] is None:
                metrics["browsertime"]["firstContentfulPaint"] = safe_get(timings, "firstPaint", "median")
            
            # Largest Contentful Paint
            metrics["browsertime"]["largestContentfulPaint"] = safe_get(timings, "largestContentfulPaint", "renderTime", "median")
            if metrics["browsertime"]["largestContentfulPaint"] is None:
                metrics["browsertime"]["largestContentfulPaint"] = safe_get(timings, "largestContentfulPaint", "median")
                
        except Exception as e:
            app.logger.warning(f"Could not parse browsertime for {page_dir}: {e}")
    
    # Parse coach data
    coach_file = page_dir / "data" / "coach.pageSummary.json"
    if coach_file.exists():
        try:
            with open(coach_file, 'r') as f:
                coach_data = json.load(f)
            
            advice = coach_data.get("advice", {})
            metrics["coach"]["score"] = advice.get("score")
            metrics["coach"]["performance"] = safe_get(advice, "performance", "score")
            metrics["coach"]["accessibility"] = safe_get(advice, "accessibility", "score")
            metrics["coach"]["bestPractice"] = safe_get(advice, "bestpractice", "score")
            metrics["coach"]["privacy"] = safe_get(advice, "privacy", "score")
            
            # Extract technology info
            metrics["coach"]["technology"] = safe_get(advice, "info", "technology")
            
        except Exception as e:
            app.logger.warning(f"Could not parse coach for {page_dir}: {e}")
    
    # Parse lighthouse data
    lighthouse_file = page_dir / "data" / "lighthouse.pageSummary.json"
    if lighthouse_file.exists():
        try:
            with open(lighthouse_file, 'r') as f:
                lh_data = json.load(f)
            
            # Scores (0-1 converted to 0-100)
            categories = lh_data.get("categories", {})
            perf_score = safe_get(categories, "performance", "score")
            metrics["lighthouse"]["performance"] = perf_score * 100 if perf_score is not None else None
            
            seo_score = safe_get(categories, "seo", "score")
            metrics["lighthouse"]["seo"] = seo_score * 100 if seo_score is not None else None
            
            bp_score = safe_get(categories, "best-practices", "score")
            metrics["lighthouse"]["bestPractices"] = bp_score * 100 if bp_score is not None else None
            
            a11y_score = safe_get(categories, "accessibility", "score")
            metrics["lighthouse"]["accessibility"] = a11y_score * 100 if a11y_score is not None else None
            
            # Timing metrics from audits
            audits = lh_data.get("audits", {})
            metrics["lighthouse"]["firstContentfulPaint"] = safe_get(audits, "first-contentful-paint", "numericValue")
            metrics["lighthouse"]["largestContentfulPaint"] = safe_get(audits, "largest-contentful-paint", "numericValue")
            
            # Fully loaded approximation (interactive time or max-potential-fid as proxy)
            metrics["lighthouse"]["fullyLoaded"] = safe_get(audits, "interactive", "numericValue")
            
        except Exception as e:
            app.logger.warning(f"Could not parse lighthouse for {page_dir}: {e}")
    
    return metrics


def aggregate_pages_metrics(pages_metrics: List[Dict]) -> Dict:
    """
    Calculate average metrics across all pages.
    """
    if not pages_metrics:
        return {}
    
    def avg(values):
        """Calculate average of non-None values."""
        valid = [v for v in values if v is not None]
        return round(sum(valid) / len(valid), 2) if valid else None
    
    aggregated = {
        "pagesCount": len(pages_metrics),
        "browsertime": {
            "fullyLoaded": avg([p["browsertime"]["fullyLoaded"] for p in pages_metrics]),
            "firstContentfulPaint": avg([p["browsertime"]["firstContentfulPaint"] for p in pages_metrics]),
            "largestContentfulPaint": avg([p["browsertime"]["largestContentfulPaint"] for p in pages_metrics])
        },
        "coach": {
            "score": avg([p["coach"]["score"] for p in pages_metrics]),
            "performance": avg([p["coach"]["performance"] for p in pages_metrics]),
            "accessibility": avg([p["coach"]["accessibility"] for p in pages_metrics]),
            "bestPractice": avg([p["coach"]["bestPractice"] for p in pages_metrics]),
            "privacy": avg([p["coach"]["privacy"] for p in pages_metrics])
        },
        "lighthouse": {
            "performance": avg([p["lighthouse"]["performance"] for p in pages_metrics]),
            "seo": avg([p["lighthouse"]["seo"] for p in pages_metrics]),
            "bestPractices": avg([p["lighthouse"]["bestPractices"] for p in pages_metrics]),
            "accessibility": avg([p["lighthouse"]["accessibility"] for p in pages_metrics]),
            "fullyLoaded": avg([p["lighthouse"]["fullyLoaded"] for p in pages_metrics]),
            "firstContentfulPaint": avg([p["lighthouse"]["firstContentfulPaint"] for p in pages_metrics]),
            "largestContentfulPaint": avg([p["lighthouse"]["largestContentfulPaint"] for p in pages_metrics])
        }
    }
    
    return aggregated


def get_all_page_directories(scan_id: str) -> List[Path]:
    """Get all page directories for a scan."""
    report_dir = REPORTS_DIR / scan_id
    pages_dir = report_dir / "pages"
    
    if not pages_dir.exists():
        return []
    
    # Find all directories that contain a 'data' subdirectory
    # The structure can be:
    # - pages/domain/data/  OR
    # - pages/domain/path/data/
    page_dirs = []
    
    # Recursively find all directories containing 'data' subdirectory
    for item in pages_dir.rglob("data"):
        if item.is_dir():
            # Parent of 'data' is the page directory
            page_dirs.append(item.parent)
    
    return sorted(page_dirs)


# Lighthouse audit ID to category mapping
LIGHTHOUSE_CATEGORY_MAP = {
    # Performance
    "first-contentful-paint": "performance",
    "largest-contentful-paint": "performance",
    "total-blocking-time": "performance",
    "cumulative-layout-shift": "performance",
    "speed-index": "performance",
    "interactive": "performance",
    "max-potential-fid": "performance",
    "server-response-time": "performance",
    "render-blocking-resources": "performance",
    "unused-css-rules": "performance",
    "unused-javascript": "performance",
    "modern-image-formats": "performance",
    "uses-responsive-images": "performance",
    "efficient-animated-content": "performance",
    "duplicated-javascript": "performance",
    "legacy-javascript": "performance",
    "dom-size": "performance",
    "total-byte-weight": "performance",
    "offscreen-images": "performance",
    "unminified-css": "performance",
    "unminified-javascript": "performance",
    "uses-optimized-images": "performance",
    "uses-text-compression": "performance",
    "uses-rel-preconnect": "performance",
    "redirects": "performance",
    "uses-http2": "performance",
    "unsized-images": "performance",
    "mainthread-work-breakdown": "performance",
    "font-display-insight": "performance",
    "forced-reflow-insight": "performance",
    "image-delivery-insight": "performance",
    "lcp-breakdown-insight": "performance",
    "lcp-discovery-insight": "performance",
    "network-dependency-tree-insight": "performance",
    "render-blocking-insight": "performance",
    "cache-insight": "performance",
    "legacy-javascript-insight": "performance",
    
    # Accessibility
    "target-size": "accessibility",
    "color-contrast": "accessibility",
    "image-alt": "accessibility",
    "button-name": "accessibility",
    "link-name": "accessibility",
    "aria-allowed-attr": "accessibility",
    "aria-hidden-body": "accessibility",
    "aria-hidden-focus": "accessibility",
    "aria-input-field-name": "accessibility",
    "aria-required-attr": "accessibility",
    "aria-roles": "accessibility",
    "aria-valid-attr": "accessibility",
    "aria-valid-attr-value": "accessibility",
    "document-title": "accessibility",
    "html-has-lang": "accessibility",
    "html-lang-valid": "accessibility",
    "label": "accessibility",
    "meta-viewport": "accessibility",
    
    # Best Practices
    "is-on-https": "best-practices",
    "external-anchors-use-rel-noopener": "best-practices",
    "geolocation-on-start": "best-practices",
    "notification-on-start": "best-practices",
    "no-vulnerable-libraries": "best-practices",
    "image-size-responsive": "best-practices",
    "doctype": "best-practices",
    "charset": "best-practices",
    "inspector-issues": "best-practices",
    "js-libraries": "best-practices",
    "deprecations": "best-practices",
    "password-inputs-can-be-pasted-into": "best-practices",
    
    # SEO
    "viewport": "seo",
    "meta-description": "seo",
    "http-status-code": "seo",
    "link-text": "seo",
    "crawlable-anchors": "seo",
    "is-crawlable": "seo",
    "robots-txt": "seo",
    "canonical": "seo",
    "hreflang": "seo",
    "font-size": "seo",
    "plugins": "seo",
    "tap-targets": "seo",
}


def parse_recommendations(scan_id: str) -> List[Dict]:
    """
    Parse Coach and Lighthouse recommendations for all pages in a scan.
    Aggregates findings and returns a list of unique recommendations.
    """
    page_dirs = get_all_page_directories(scan_id)
    recommendations_map = {}  # Key: (source, id), Value: Recommendation Dict
    
    for page_dir in page_dirs:
        page_name = page_dir.name
        
        # 1. Parse Coach Recommendations
        coach_file = page_dir / "data" / "coach.pageSummary.json"
        if coach_file.exists():
            try:
                with open(coach_file, 'r') as f:
                    coach_data = json.load(f)
                
                advice = coach_data.get("advice", {})
                categories = ["performance", "accessibility", "bestpractice", "privacy"]
                
                for category in categories:
                    cat_data = advice.get(category, {})
                    advice_list = cat_data.get("adviceList", {})
                    
                    for rule_id, rule in advice_list.items():
                        score = rule.get("score")
                        if score is not None and score < 100:
                            key = ("coach", rule_id)
                            
                            if key not in recommendations_map:
                                title = rule.get("title")
                                description = rule.get("description")
                                
                                recommendations_map[key] = {
                                    "id": rule_id,
                                    "source": "coach",
                                    "category": category,
                                    "title": title,
                                    "description": description,
                                    "score": score,
                                    "severity": "error" if score < 50 else "warning" if score < 90 else "info",
                                    "pages": []
                                }
                            
                            rec = recommendations_map[key]
                            if page_name not in rec["pages"]:
                                rec["pages"].append(page_name)
                            
                            # Keep the lowest score found across pages
                            if score < rec["score"]:
                                rec["score"] = score
                                rec["severity"] = "error" if score < 50 else "warning" if score < 90 else "info"
                                
            except Exception as e:
                app.logger.warning(f"Error parsing coach recommendations for {page_name}: {e}")

        # 2. Parse Lighthouse Recommendations
        lighthouse_file = page_dir / "data" / "lighthouse.pageSummary.json"
        if lighthouse_file.exists():
            try:
                with open(lighthouse_file, 'r') as f:
                    lh_data = json.load(f)
                
                audits = lh_data.get("audits", {})
                
                for audit_id, audit in audits.items():
                    score = audit.get("score")
                    # Lighthouse scores are 0-1, we convert to 0-100.
                    # Ignore null scores (not applicable) and perfect scores (1)
                    if score is not None and score < 0.9:
                        score_100 = int(score * 100)
                        key = ("lighthouse", audit_id)
                        
                        if key not in recommendations_map:
                            title = audit.get("title")
                            description = audit.get("description")
                            
                            # Get category from mapping, default to 'other'
                            category = LIGHTHOUSE_CATEGORY_MAP.get(audit_id, "other")
                            
                            recommendations_map[key] = {
                                "id": audit_id,
                                "source": "lighthouse",
                                "category": category,
                                "title": title,
                                "description": description,
                                "score": score_100,
                                "severity": "error" if score_100 < 50 else "warning" if score_100 < 90 else "info",
                                "pages": []
                            }
                        
                        rec = recommendations_map[key]
                        if page_name not in rec["pages"]:
                            rec["pages"].append(page_name)
                        
                        if score_100 < rec["score"]:
                            rec["score"] = score_100
                            rec["severity"] = "error" if score_100 < 50 else "warning" if score_100 < 90 else "info"

            except Exception as e:
                app.logger.warning(f"Error parsing lighthouse recommendations for {page_name}: {e}")
                
    return list(recommendations_map.values())


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
    # Individual page data is stored in pages/$PAGE/data/
    # Search from report_dir to find files in pages/ subdirectory
    
    # Look for browsertime page summary
    browsertime_files = list(report_dir.glob("**/browsertime.pageSummary.json"))
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
    coach_files = list(report_dir.glob("**/coach.pageSummary.json"))
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
    pagexray_files = list(report_dir.glob("**/pagexray.pageSummary.json"))
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
    
    # Look for Lighthouse data
    lighthouse_files = list(report_dir.glob("**/lighthouse.pageSummary.json"))
    if lighthouse_files:
        try:
            with open(lighthouse_files[0], 'r') as f:
                lighthouse_data = json.load(f)
            
            # Extract Lighthouse scores and Web Vitals
            if "categories" in lighthouse_data:
                categories = lighthouse_data["categories"]
                summary["metrics"]["lighthouse"] = {
                    "performance": categories.get("performance", {}).get("score", 0) * 100,
                    "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
                    "bestPractices": categories.get("best-practices", {}).get("score", 0) * 100,
                    "seo": categories.get("seo", {}).get("score", 0) * 100,
                    "pwa": categories.get("pwa", {}).get("score", 0) * 100
                }
            
            # Extract Web Vitals
            if "audits" in lighthouse_data:
                audits = lighthouse_data["audits"]
                summary["metrics"]["lighthouse"]["webVitals"] = {
                    "LCP": audits.get("largest-contentful-paint", {}).get("numericValue"),
                    "TBT": audits.get("total-blocking-time", {}).get("numericValue"),
                    "CLS": audits.get("cumulative-layout-shift", {}).get("numericValue"),
                    "FCP": audits.get("first-contentful-paint", {}).get("numericValue"),
                    "SI": audits.get("speed-index", {}).get("numericValue")
                }
            
            summary["reports"]["lighthouse_json"] = f"/reports/{scan_id}/{lighthouse_files[0].relative_to(report_dir)}"
        except Exception as e:
            app.logger.warning(f"Could not parse lighthouse.pageSummary.json for {scan_id}: {e}")
    
    # Look for Lighthouse HTML report
    lighthouse_html = list(report_dir.glob("**/lighthouse.html"))
    if lighthouse_html:
        summary["reports"]["lighthouse_html"] = f"/reports/{scan_id}/{lighthouse_html[0].relative_to(report_dir)}"
    
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


def run_sitespeed_scan(scan_id: str, url: str, extra_args: list, remove_age_gate: bool = False):
    """Run sitespeed.io scan in a separate thread."""
    try:
        scans[scan_id]["status"] = "running"

        output_dir = f"/reports/{scan_id}"

        # When age gate removal is requested, use sitespeed.io scripting mode:
        # generate a script that navigates, removes overlays, then measures.
        if remove_age_gate:
            scripts_dir = REPORTS_DIR / "_scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            script_file = scripts_dir / f"scan_{scan_id}.cjs"
            script_file.write_text(generate_age_gate_script(url))
            # In scripting mode, the script path replaces the URL argument
            sitespeed_target = f"/sitespeed.io/_scripts/scan_{scan_id}.cjs"
        else:
            sitespeed_target = url

        # Build docker command
        # Use HOST_REPORTS_DIR because docker socket runs containers on the host
        docker_cmd = [
            "docker", "run", "--rm", "--shm-size=2g",
            "-v", f"{HOST_REPORTS_DIR}:/sitespeed.io",
            "-v", f"{HOST_SCRIPTS_DIR}:/scripts:ro",
            SITESPEED_IMAGE,
            sitespeed_target,
            "--outputFolder", scan_id,
            "--plugins.add", "analysisstorer",  # Enable JSON output
            "--plugins.add", "@sitespeed.io/plugin-lighthouse",  # Enable Lighthouse
            "--plugins.remove", "@sitespeed.io/plugin-gpsi",  # Disable GPSI to avoid quota
            "--locale", "fr",
            "--lighthouse.settings.locale", "fr",
            # Lighthouse throttling settings (can be overridden by extra_args)
            "--lighthouse.settings.throttlingMethod", "simulate",
        ]

        # In scripting mode, tell sitespeed this is a multi-step script
        if remove_age_gate:
            docker_cmd.append("--multi")

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
            scans[scan_id]["completed_at"] = format_timestamp(datetime.utcnow())
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
    finally:
        # Clean up per-scan script file if one was generated
        if remove_age_gate:
            try:
                (REPORTS_DIR / "_scripts" / f"scan_{scan_id}.cjs").unlink(missing_ok=True)
            except Exception:
                pass


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
        "options": ["-b", "firefox", "--mobile", "--video"],  // optional
        "removeAgeGate": true  // optional, pre-visits URL to dismiss age gates
    }
    """
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    url = data['url']
    extra_args = data.get('options', [])
    remove_age_gate = data.get('removeAgeGate', False)

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
        "started_at": format_timestamp(datetime.utcnow()),
        "completed_at": None,
        "error": None,
        "output": None
    }
    
    # Start scan in background thread
    thread = threading.Thread(
        target=run_sitespeed_scan,
        args=(scan_id, url, extra_args, remove_age_gate),
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


@app.route('/report/<scan_id>/main', methods=['GET'])
def get_main_page_metrics(scan_id: str):
    """
    Get metrics for the main page (first page scanned) only.
    
    Returns standardized metrics including:
    - Browsertime: fullyLoaded, firstContentfulPaint, largestContentfulPaint
    - Coach: all scores (overall, performance, accessibility, bestPractice, privacy)
    - Lighthouse: performance, seo, bestPractices, accessibility, timing metrics
    """
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
    
    # Get all page directories
    page_dirs = get_all_page_directories(scan_id)
    
    if not page_dirs:
        return jsonify({
            "error": "No pages found in scan",
            "scanId": scan_id
        }), 404
    
    # Parse metrics for the first (main) page
    main_page_dir = page_dirs[0]
    metrics = parse_page_metrics(main_page_dir)
    
    if metrics is None:
        return jsonify({
            "error": "Could not parse main page metrics",
            "scanId": scan_id
        }), 500
    
    # Build response
    scan_data = scans.get(scan_id, {})
    response = {
        "scanId": scan_id,
        "url": scan_data.get("url", ""),
        "pageUrl": metrics["page"],
        "timestamp": scan_data.get("started_at", ""),
        "completed_at": scan_data.get("completed_at", ""),
        "technology": metrics["coach"].get("technology"),
        "metrics": {
            "browsertime": metrics["browsertime"],
            "coach": metrics["coach"],
            "lighthouse": metrics["lighthouse"]
        }
    }
    
    # Remove null values from response
    response = remove_null_values(response)
    
    return jsonify(response)


@app.route('/report/<scan_id>/aggregate', methods=['GET'])
def get_aggregate_metrics(scan_id: str):
    """
    Get aggregated (average) metrics across all scanned pages.
    
    Returns average values for:
    - Browsertime: fullyLoaded, firstContentfulPaint, largestContentfulPaint
    - Coach: all scores (overall, performance, accessibility, bestPractice, privacy)
    - Lighthouse: performance, seo, bestPractices, accessibility, timing metrics
    """
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
    
    # Get all page directories
    page_dirs = get_all_page_directories(scan_id)
    
    if not page_dirs:
        return jsonify({
            "error": "No pages found in scan",
            "scanId": scan_id
        }), 404
    
    # Parse metrics for all pages
    all_metrics = []
    pages_detail = []
    
    for page_dir in page_dirs:
        page_metrics = parse_page_metrics(page_dir)
        if page_metrics:
            all_metrics.append(page_metrics)
            pages_detail.append({
                "page": page_metrics["page"],
                "lighthousePerformance": page_metrics["lighthouse"]["performance"],
                "coachScore": page_metrics["coach"]["score"]
            })
    
    if not all_metrics:
        return jsonify({
            "error": "Could not parse any page metrics",
            "scanId": scan_id
        }), 500
    
    # Calculate aggregated averages
    aggregated = aggregate_pages_metrics(all_metrics)
    
    # Get technology from first (main) page (before null removal)
    main_page_technology = all_metrics[0]["coach"].get("technology") if all_metrics else None
    
    # Build response
    scan_data = scans.get(scan_id, {})
    response = {
        "scanId": scan_id,
        "url": scan_data.get("url", ""),
        "timestamp": scan_data.get("started_at", ""),
        "completed_at": scan_data.get("completed_at", ""),
        "pagesCount": aggregated["pagesCount"],
        "pagesScanned": pages_detail,
        "technology": main_page_technology,
        "averageMetrics": {
            "browsertime": aggregated["browsertime"],
            "coach": aggregated["coach"],
            "lighthouse": aggregated["lighthouse"]
        }
    }
    
    # Remove null values from response
    response = remove_null_values(response)
    
    return jsonify(response)


@app.route('/report/<scan_id>/recommendations', methods=['GET'])
def get_recommendations(scan_id: str):
    """
    Get aggregated recommendations/advice for a website.
    Merges findings from Coach and Lighthouse across all pages.
    """
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
    
    try:
        recommendations = parse_recommendations(scan_id)
        
        # Sort by score (ascending) to show worst issues first
        recommendations.sort(key=lambda x: x["score"])
        
        scan_data = scans.get(scan_id, {})
        response = {
            "scanId": scan_id,
            "url": scan_data.get("url", ""),
            "timestamp": scan_data.get("started_at", ""),
            "recommendationsCount": len(recommendations),
            "recommendations": recommendations
        }
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error retrieving recommendations for {scan_id}: {e}")
        return jsonify({
            "error": "Could not retrieve recommendations",
            "details": str(e)
        }), 500


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
