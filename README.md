# Sitespeed Runner Service

A Python Flask microservice that provides an HTTP API to run sitespeed.io performance scans via Docker.

## Features

- **Asynchronous scanning**: Scans run in the background without blocking the API
- **Status polling**: Check scan progress via `/status/{scanId}`
- **Report parsing**: Get parsed JSON summaries of completed scans
- **Docker-based**: Uses the official sitespeed.io Docker image

## API Endpoints

### POST /run-sitespeed
Start a new sitespeed.io scan.

**Request:**
```json
{
  "url": "https://example.com",
  "options": ["-b", "firefox", "--mobile", "--video"]
}
```

**Response (202 Accepted):**
```json
{
  "scanId": "uuid-here",
  "status": "queued",
  "statusUrl": "/status/uuid-here",
  "reportUrl": "/report/uuid-here"
}
```

### GET /status/{scanId}
Check the status of a scan.

**Response:**
```json
{
  "scanId": "uuid-here",
  "status": "completed|running|failed",
  "url": "https://example.com",
  "started_at": "2024-12-09T12:00:00",
  "completed_at": "2024-12-09T12:05:00",
  "reportUrl": "/report/uuid-here"
}
```

### GET /report/{scanId}
Get the parsed report summary for a completed scan.

**Response:**
```json
{
  "scanId": "uuid-here",
  "url": "https://example.com",
  "timestamp": "2024-12-09T12:00:00",
  "metrics": {
    "loadTime": 1234,
    "firstPaint": 567,
    "visualMetrics": {...},
    "score": {...}
  }
}
```

### GET /scans
List all scans.

**Response:**
```json
{
  "scans": [...],
  "total": 5
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "sitespeed-runner"
}
```

## Usage from n8n

You can call this service from n8n using the HTTP Request node:

1. **Start a scan:**
   - Method: POST
   - URL: `http://sitespeed-runner:5679/run-sitespeed`
   - Body: `{"url": "https://example.com", "options": ["-b", "chrome"]}`

2. **Poll for status:**
   - Method: GET
   - URL: `http://sitespeed-runner:5679/status/{{$json.scanId}}`

3. **Get report:**
   - Method: GET
   - URL: `http://sitespeed-runner:5679/report/{{$json.scanId}}`

## Common sitespeed.io Options

Add these to the `options` array in your request:

- `-b chrome` or `-b firefox` - Browser to use
- `--mobile` - Emulate mobile device
- `--video` - Record video
- `--visualMetrics` - Calculate visual metrics
- `-n 3` - Number of runs (default is 3)
- `--speedIndex` - Calculate Speed Index

## Environment Variables

- `SITESPEED_IO_CONTAINER`: Docker image to use (default: `sitespeedio/sitespeed.io:38.6.0-plus1`)

## Storage

Reports are stored in `/srv/docker/n8n/local_files/sitespeed-reports/` and are accessible to both this service and n8n.

