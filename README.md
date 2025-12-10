# Sitespeed Runner Service

A Python Flask microservice that provides an HTTP API to run comprehensive website performance analysis via Docker.

## Features

- **Asynchronous scanning**: Scans run in the background without blocking the API
- **Status polling**: Check scan progress via `/status/{scanId}`
- **Lighthouse integration**: Official Google Lighthouse scores and audits ⭐
- **Complete analysis**: Browsertime, Coach, PageXray, Axe, Visual Metrics
- **No external APIs**: Everything runs locally (no API keys or quotas)
- **Report parsing**: Get parsed JSON summaries of completed scans
- **Docker-based**: Uses the official sitespeed.io Docker image

## What You Get

Each scan provides comprehensive analysis:

### Performance Metrics
- **Browsertime**: Load times, FCP, LCP, TBT, CLS, CPU usage
- **Lighthouse**: Official Google Performance score ⭐
- **Visual Metrics**: Speed Index, Visual Complete, filmstrip
- **Network Analysis**: HAR files, waterfall charts

### Quality Audits
- **Lighthouse Scores**: Performance, Accessibility, Best Practices, SEO, PWA
- **Coach**: Best practices and optimization recommendations
- **Axe**: WCAG accessibility compliance (with `--axe.enable`)
- **PageXray**: Resource analysis, third-party detection

### Visual Evidence
- **Video Recording**: Full page load capture
- **Screenshots**: Key moments (LCP, layout shift, etc.)
- **Lighthouse HTML**: Interactive Google audit report

## API Endpoints

### POST /run-sitespeed
Start a new comprehensive website scan.

**Request:**
```json
{
  "url": "https://example.com",
  "options": ["-b", "chrome", "--mobile", "-n", "3"]
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
  "completed_at": "2024-12-09T12:01:00",
  "reports": {
    "html": "/reports/{scanId}/index.html",
    "lighthouse_html": "/reports/{scanId}/pages/.../lighthouse.html",
    "detailed_html": "/reports/{scanId}/detailed.html",
    "har": "/reports/{scanId}/pages/.../browsertime.har",
    "video": "/reports/{scanId}/pages/.../video/1.mp4",
    "screenshots": ["..."]
  },
  "metrics": {
    "lighthouse": {
      "performance": 89,
      "accessibility": 84,
      "bestPractices": 96,
      "seo": 100,
      "webVitals": {
        "FCP": 1600,
        "LCP": 3500,
        "TBT": 60,
        "CLS": 0
      }
    },
    "browsertime": {...},
    "coach": {...},
    "pagexray": {...}
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

## Quick Examples

### Basic Scan (Mobile)
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "options": ["-b", "chrome", "-n", "1", "--mobile"]}'
```

### Complete Analysis (Desktop)
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": [
      "-b", "chrome",
      "-n", "3",
      "--axe.enable",
      "--visualMetrics"
    ]
  }'
```

### Crawl Multiple Pages
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": [
      "-b", "chrome",
      "-n", "1",
      "--crawler.depth", "1",
      "--crawler.maxPages", "10"
    ]
  }'
```

### Complete Site Audit (Full Analysis with Crawling)
```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://therapeutelarochelle.fr",
    "options": [
      "-b", "chrome",
      "-n", "3",
      "--desktop",
      "--axe.enable",
      "--visualMetrics",
      "--crawler.depth", "1",
      "--crawler.maxPages", "10",
      "--spa",
      "--plugins.add", "analysisstorer",
      "--plugins.add", "@sitespeed.io/plugin-lighthouse",
      "--plugins.remove", "@sitespeed.io/plugin-gpsi"
    ]
  }'
```

**What this does:**
- ✅ Scans homepage + 10 linked pages (up to 10 total)
- ✅ Runs 3 tests per page for accurate metrics
- ✅ Lighthouse audits (Performance, SEO, Accessibility, Best Practices)
- ✅ Accessibility testing (WCAG compliance)
- ✅ Visual metrics (Speed Index, Visual Complete)
- ✅ JSON output for programmatic access
- ⏱️ **Estimated time**: ~25-30 minutes for 10 pages

**Note:** The `--plugins.*` options are already configured by default, but are shown here for completeness. You can omit them.

## Usage from n8n

You can call this service from n8n using the HTTP Request node:

1. **Start a scan:**
   - Method: POST
   - URL: `http://sitespeed-runner:5679/run-sitespeed`
   - Body: `{"url": "https://example.com", "options": ["-b", "chrome", "-n", "3", "--mobile"]}`

2. **Wait Node:** 30-60 seconds (depending on options)

3. **Poll for status:**
   - Method: GET
   - URL: `http://sitespeed-runner:5679/status/{{$json.scanId}}`

4. **Get report:**
   - Method: GET
   - URL: `http://sitespeed-runner:5679/report/{{$json.scanId}}`

## Common Options

Add these to the `options` array in your request:

**Browser & Device:**
- `-b chrome` or `-b firefox` - Browser to use
- `--mobile` - Emulate mobile device (changes Lighthouse config too)
- `-n 3` - Number of runs (1 for quick tests, 3+ for accurate metrics)

**Analysis Features:**
- `--axe.enable` - Run accessibility tests (WCAG compliance)
- `--visualMetrics` - Calculate Speed Index, Visual Complete from video
- `--crawler.depth 1` - Crawl linked pages (0=only URL, 1=+links, 2=+links of links)
- `--crawler.maxPages 10` - Limit number of pages to scan
- `--spa` - Enable Single Page Application support

**Performance:**
- `--video` - Record video (enabled by default)
- `--screenshot` - Take screenshots (enabled by default)
- `--speedIndex` - Calculate Speed Index metric

## Technical Details

### Docker Image
Uses `sitespeedio/sitespeed.io:38.6.0-plus1` which includes:
- Browsertime (performance testing)
- Lighthouse plugin (Google audits)
- Coach (best practices)
- All standard sitespeed.io tools

**Note:** GPSI (Google PageSpeed Insights API) is disabled to avoid quota limits. Lighthouse runs locally instead.

### Storage
Reports are stored in `/srv/docker/n8n/local_files/sitespeed-reports/` and are accessible to both this service and n8n.

### Performance
- **Basic scan**: ~30-50 seconds
- **With visual metrics**: ~60-90 seconds  
- **Crawling**: multiply by number of pages
- **Lighthouse**: adds ~20 seconds per page

### Environment Variables
- `SITESPEED_IO_CONTAINER`: Docker image (default: `sitespeedio/sitespeed.io:38.6.0-plus1`)
- `HOST_REPORTS_DIR`: Host path for reports (default: `/srv/docker/n8n/local_files/sitespeed-reports`)

## What Makes This Special

### ✅ No External Dependencies
- All analysis runs **locally on your server**
- No API keys required
- No quota limits
- No external service failures
- Complete privacy

### ✅ Official Google Lighthouse
- Industry-standard metrics
- Same scores as Google Search Console
- Performance, Accessibility, Best Practices, SEO, PWA audits
- Google Web Vitals (FCP, LCP, TBT, CLS)

### ✅ Complete Website Analysis
Get everything in one scan:
- **Browsertime**: Synthetic performance metrics
- **Lighthouse**: Official Google scores ⭐
- **Coach**: Best practices recommendations
- **PageXray**: Resource analysis
- **Axe**: Accessibility testing
- **Visual Metrics**: Video-based analysis

## Troubleshooting

### Lighthouse Not Running?
Check the Docker image:
```bash
docker exec n8n-sitespeed-runner-1 env | grep SITESPEED_IO_CONTAINER
# Should show: sitespeedio/sitespeed.io:38.6.0-plus1
```

### GPSI Quota Errors?
GPSI is disabled by default. If you see quota errors, ensure `--plugins.remove @sitespeed.io/plugin-gpsi` is in the command.

### Scans Taking Too Long?
- Reduce `-n` value (e.g., `-n 1` for quick tests)
- Remove `--visualMetrics` for faster scans
- Reduce `--crawler.maxPages`

### Reports Not Found?
Reports are stored in `/srv/docker/n8n/local_files/sitespeed-reports/{scanId}/`
Check permissions: `ls -la /srv/docker/n8n/local_files/sitespeed-reports/`

## Additional Resources

- **Lighthouse Integration**: See `LIGHTHOUSE_INTEGRATION.md` for detailed Lighthouse documentation
- **Usage Examples**: See `USAGE.md` for more examples
- **sitespeed.io Docs**: https://www.sitespeed.io/documentation/
- **Lighthouse Docs**: https://developers.google.com/web/tools/lighthouse
