# Sitespeed Runner Service - Usage Guide

## ✅ Service is Running

The sitespeed runner service is now operational at `http://localhost:5679`

## Quick Start

### 1. Run a Basic Scan

```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{"url": "https://therapeutelarochelle.fr", "options": ["-b", "chrome", "-n", "1"]}'
```

**Response:**
```json
{
  "scanId": "uuid-here",
  "status": "queued",
  "statusUrl": "/status/uuid-here",
  "reportUrl": "/report/uuid-here"
}
```

### 2. Check Scan Status

```bash
curl http://localhost:5679/status/{scanId}
```

### 3. Get Report

```bash
curl http://localhost:5679/report/{scanId}
```

## Advanced Examples

### Mobile Test with Accessibility
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://therapeutelarochelle.fr",
    "options": [
      "-b", "chrome",
      "-n", "1",
      "--mobile",
      "--axe.enable"
    ]
  }'
```

### Crawl Multiple Pages
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://therapeutelarochelle.fr",
    "options": [
      "-b", "chrome",
      "-n", "1",
      "--crawler.depth", "1",
      "--crawler.maxPages", "5"
    ]
  }'
```

### Desktop with Visual Metrics
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type": "application/json" \
  -d '{
    "url": "https://therapeutelarochelle.fr",
    "options": [
      "-b", "chrome",
      "-n", "1",
      "--visualMetrics"
    ]
  }'
```

## Common Options

| Option | Description |
|--------|-------------|
| `-b chrome` or `-b firefox` | Browser to use |
| `-n 3` | Number of test runs (default: 3) |
| `--mobile` | Emulate mobile device |
| `--axe.enable` | Run accessibility tests |
| `--visualMetrics` | Calculate visual metrics from video |
| `--crawler.depth 1` | Crawl depth (0 = only URL, 1 = + direct links) |
| `--crawler.maxPages 5` | Maximum pages to crawl |

## Report Output

The `/report/{scanId}` endpoint returns:

```json
{
  "scanId": "...",
  "url": "https://therapeutelarochelle.fr",
  "timestamp": "2025-12-09T12:00:00",
  "completed_at": "2025-12-09T12:01:00",
  "reports": {
    "html": "/reports/{scanId}/index.html",
    "detailed_html": "/reports/{scanId}/detailed.html",
    "har": "/reports/{scanId}/pages/.../browsertime.har",
    "video": "/reports/{scanId}/pages/.../video/1.mp4",
    "screenshots": ["..."]
  },
  "metrics": {
    // Performance metrics when available
  }
}
```

## Accessing Reports

All reports are stored in `/srv/docker/n8n/local_files/sitespeed-reports/{scanId}/`

- HTML reports: Open `index.html` in a browser
- HAR files: Import into Chrome DevTools or other HAR viewers
- Videos: MP4 format, playable in any video player
- Screenshots: PNG format

## Use from n8n

1. **HTTP Request Node** - Start Scan:
   - Method: POST
   - URL: `http://sitespeed-runner:5679/run-sitespeed`
   - Body: `{"url": "{{$json.url}}", "options": ["-b", "chrome", "-n", "1"]}`

2. **Wait Node** - Wait 30-60 seconds

3. **HTTP Request Node** - Get Status:
   - Method: GET
   - URL: `http://sitespeed-runner:5679/status/{{$json.scanId}}`

4. **IF Node** - Check if `status === "completed"`

5. **HTTP Request Node** - Get Report:
   - Method: GET
   - URL: `http://sitespeed-runner:5679/report/{{$json.scanId}}`

## Important Notes

⚠️ **Google PageSpeed Insights (GPSI):**
- The default sitespeed.io image includes GPSI which requires an API key
- GPSI has been disabled by using the regular image (not the "plus1" version)
- To enable GPSI, add `--gpsi.key YOUR_API_KEY` to options

⚠️ **Lighthouse Plugin:**
- Not available in the base Docker image
- Would require a custom image with Lighthouse installed

⚠️ **Performance:**
- Basic scan: ~30 seconds
- With --visualMetrics: ~45-60 seconds
- Crawling multiple pages: multiply by number of pages

## Troubleshooting

### Scan Failed
Check the error in `/status/{scanId}`:
```bash
curl http://localhost:5679/status/{scanId}
```

### No Reports Generated
- Check that Docker has enough resources (CPU/Memory)
- Verify the URL is accessible from the container
- Check Docker logs: `docker logs n8n-sitespeed-runner-1`

### Reports Not Accessible
Reports are in: `/srv/docker/n8n/local_files/sitespeed-reports/`
They are also accessible from n8n at: `/files/sitespeed-reports/`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/run-sitespeed` | POST | Start a new scan |
| `/status/{scanId}` | GET | Get scan status |
| `/report/{scanId}` | GET | Get parsed report |
| `/scans` | GET | List all scans in memory |

## Example Complete Workflow

```bash
# 1. Start scan
SCAN_ID=$(curl -s -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{"url": "https://therapeutelarochelle.fr", "options": ["-b", "chrome", "-n", "1"]}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['scanId'])")

echo "Scan ID: $SCAN_ID"

# 2. Wait for completion
while true; do
  STATUS=$(curl -s http://localhost:5679/status/$SCAN_ID \
    | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  [ "$STATUS" = "failed" ] && exit 1
  sleep 10
done

# 3. Get report
curl -s http://localhost:5679/report/$SCAN_ID | python3 -m json.tool

# 4. Open HTML report
xdg-open /srv/docker/n8n/local_files/sitespeed-reports/$SCAN_ID/index.html
```

## Support

- Sitespeed.io Documentation: https://www.sitespeed.io/documentation/
- Issues: Check Docker logs and status endpoint for error messages

