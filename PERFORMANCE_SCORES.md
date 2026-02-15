# Performance Score Optimization Guide

## Why Are My Scores Lower Than Browser Lighthouse?

When running Lighthouse through sitespeed-runner, you may see **lower performance scores** compared to running Lighthouse directly in your browser's DevTools. This is **completely normal** and happens for several reasons:

### 1. **CPU Throttling** (Main Cause)
- **Lighthouse Default**: Applies 4x CPU throttling to simulate slower devices
- **Docker Environment**: Adds additional performance overhead
- **Result**: Your fast website appears slower than it actually is

### 2. **Network Throttling**
- **Lighthouse Default**: Simulates slow 4G (1.6 Mbps download, 750 Kbps upload, 150ms RTT)
- **Your Browser**: May run without throttling or with different settings

### 3. **Test Environment Differences**
- **Browser DevTools**: Runs on your local machine with full resources
- **sitespeed-runner**: Runs in Docker container on your server
- **Docker Overhead**: Container isolation adds small performance penalty

### 4. **Mobile vs Desktop**
- **Mobile mode** (`--mobile` flag): More restrictive, simulates mobile device
- **Desktop mode**: Better performance, fewer restrictions

## What I Changed

### Before:
```python
docker_cmd = [
    "--shm-size=1g",
    # ... other settings ...
    # No throttling configuration (uses Lighthouse defaults)
]
```

### After:
```python
docker_cmd = [
    "--shm-size=2g",  # ✅ Increased shared memory
    # ... other settings ...
    "--lighthouse.settings.throttlingMethod", "simulate",
    "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "1",  # ✅ No CPU throttling
]
```

## How to Use Different Testing Modes

### Mode 1: **Realistic Performance** (Recommended - New Default)
Measures your actual website performance without artificial throttling.

```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": ["-b", "chrome", "-n", "3"]
  }'
```

**Expected Results**: Scores similar to your browser's Lighthouse (90-100 for fast sites)

### Mode 2: **Mobile Device Simulation** (Google's Standard)
Simulates a mid-tier mobile device on slow 4G connection.

```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": [
      "-b", "chrome",
      "-n", "3",
      "--mobile",
      "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "4"
    ]
  }'
```

**Expected Results**: Lower scores (70-85 for good sites) - matches Google PageSpeed Insights

### Mode 3: **No Throttling at All** (Maximum Performance)
Tests your site at full speed with no artificial limitations.

```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": [
      "-b", "chrome",
      "-n", "3",
      "--lighthouse.settings.throttlingMethod", "provided"
    ]
  }'
```

**Expected Results**: Highest possible scores (95-100 for well-optimized sites)

### Mode 4: **Custom Throttling**
Fine-tune throttling to match your target audience.

```bash
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": [
      "-b", "chrome",
      "-n", "3",
      "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "2",
      "--lighthouse.settings.throttling.rttMs", "40",
      "--lighthouse.settings.throttling.throughputKbps", "10240"
    ]
  }'
```

## Complete Lighthouse Settings Reference

Add these to the `options` array to customize Lighthouse behavior:

### Throttling Settings
```bash
# CPU throttling (1 = no throttling, 4 = standard mobile)
"--lighthouse.settings.throttling.cpuSlowdownMultiplier", "1"

# Network latency in milliseconds
"--lighthouse.settings.throttling.rttMs", "40"

# Download speed in Kbps
"--lighthouse.settings.throttling.throughputKbps", "10240"

# Upload speed in Kbps
"--lighthouse.settings.throttling.uploadThroughputKbps", "10240"

# Throttling method: "simulate" or "provided"
"--lighthouse.settings.throttlingMethod", "simulate"
```

### Device Emulation
```bash
# Mobile device (already handled by --mobile flag)
"--lighthouse.settings.formFactor", "mobile"

# Desktop device
"--lighthouse.settings.formFactor", "desktop"

# Screen emulation
"--lighthouse.settings.screenEmulation.mobile", "false"
"--lighthouse.settings.screenEmulation.width", "1350"
"--lighthouse.settings.screenEmulation.height", "940"
```

### Test Configuration
```bash
# Disable throttling entirely
"--lighthouse.settings.throttlingMethod", "provided"

# Skip certain audits
"--lighthouse.settings.skipAudits", "uses-http2,uses-long-cache-ttl"

# Only run specific categories
"--lighthouse.settings.onlyCategories", "performance,accessibility"
```

## Understanding Your Scores

### Lighthouse Score Ranges

| Score | Rating | What It Means |
|-------|--------|---------------|
| **90-100** | 🟢 Good | Excellent performance, well-optimized |
| **50-89** | 🟡 Needs Improvement | Decent performance, room for optimization |
| **0-49** | 🔴 Poor | Significant performance issues |

### Score Comparison

**Example: A well-optimized website**

| Test Configuration | Performance Score | Use Case |
|-------------------|------------------|----------|
| Browser DevTools (no throttling) | 98 | Development testing |
| sitespeed-runner (new default) | 95 | Realistic performance |
| Google PageSpeed Insights | 85 | Mobile device simulation |
| Old sitespeed-runner (4x CPU) | 72 | Worst-case scenario |

**All scores are valid** - they just test different scenarios!

## Which Mode Should You Use?

### For Development & Monitoring
**Use Mode 1** (New Default - No CPU throttling)
- Most realistic representation of actual user experience
- Matches what users with modern devices will see
- Good for comparing changes over time

### For Mobile-First Projects
**Use Mode 2** (Mobile with 4x CPU throttling)
- Matches Google PageSpeed Insights
- Tests worst-case mobile scenario
- Important for SEO and mobile users

### For Performance Benchmarking
**Use Mode 3** (No throttling)
- Shows maximum potential performance
- Good for infrastructure testing
- Useful for comparing hosting providers

### For Specific Target Audience
**Use Mode 4** (Custom throttling)
- Match your typical user's device and network
- Most relevant for your specific use case

## Troubleshooting

### Still Getting Low Scores?

1. **Check Docker Resources**
   ```bash
   docker stats
   ```
   Ensure your server has enough CPU and memory available.

2. **Test with No Throttling**
   ```bash
   curl -X POST http://localhost:5679/run-sitespeed \
     -d '{"url": "https://example.com", "options": ["--lighthouse.settings.throttlingMethod", "provided"]}'
   ```
   If scores are still low, the issue is your website, not throttling.

3. **Compare with Google PageSpeed Insights**
   Visit https://pagespeed.web.dev/ and test your site.
   - If Google scores are similar to your sitespeed-runner: working correctly!
   - If Google scores are higher: check throttling settings

4. **Run Multiple Tests**
   Use `-n 3` or `-n 5` for more accurate results (median of multiple runs)

### Docker Performance Tips

```dockerfile
# Increase shared memory (already done)
--shm-size=2g

# Add more CPU cores if available
--cpus=2

# Increase memory limit
--memory=4g
```

## Recommended Configuration

For most use cases, this is the best configuration:

```json
{
  "url": "https://example.com",
  "options": [
    "-b", "chrome",
    "-n", "3",
    "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "1"
  ]
}
```

This gives you:
- ✅ Realistic performance scores
- ✅ Fast scan times (~50-60 seconds)
- ✅ Consistent results
- ✅ Scores similar to browser Lighthouse

## Additional Resources

- **Lighthouse Throttling**: https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md
- **sitespeed.io Lighthouse**: https://www.sitespeed.io/documentation/sitespeed.io/lighthouse/
- **Google PageSpeed Insights**: https://pagespeed.web.dev/

## Summary

🎯 **The changes I made will give you more realistic scores** that better reflect your actual website performance!

The default configuration now:
- ✅ Disables artificial CPU throttling
- ✅ Uses 2GB shared memory (was 1GB)
- ✅ Still maintains network throttling for realistic conditions
- ✅ Gives scores similar to your browser's Lighthouse

You can always override these settings using the `options` array to test different scenarios.






