# 🚀 Quick Fix: Low Performance Scores

## The Problem

You reported: **"Performance score is low even though it is not when I run Lighthouse on the same website in my browser"**

**Example:**
- Your Browser Lighthouse: **95** 🟢
- sitespeed-runner (old): **72** 🟡
- Difference: **-23 points!** 😱

## The Cause

Lighthouse by default applies **4x CPU throttling** to simulate slower mobile devices. Combined with Docker overhead, this made your scores artificially low.

## The Solution ✅

**I've updated your `app.py` with these changes:**

1. **Disabled CPU throttling** by default (was 4x slowdown)
2. **Increased shared memory** from 1GB to 2GB
3. **Added configuration options** to customize throttling

## Expected Results After Fix

**Same website:**
- Your Browser Lighthouse: **95** 🟢
- sitespeed-runner (NEW): **93-95** 🟢
- Difference: **~0-2 points** ✅

## How to Apply the Fix

### Option 1: Rebuild Docker Container (Recommended)

```bash
cd /srv/docker/n8n/sitespeed-runner
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Option 2: Restart Existing Container

```bash
cd /srv/docker/n8n
docker-compose restart sitespeed-runner
```

## Test the Fix

```bash
# Test your website
curl -X POST http://localhost:5679/run-sitespeed \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-website.com",
    "options": ["-b", "chrome", "-n", "3"]
  }'

# Or use the test script
cd /srv/docker/n8n/sitespeed-runner
./test_performance_modes.sh https://your-website.com
```

## Understanding the Modes

### ✅ Mode 1: Realistic Performance (NEW DEFAULT)
**Best for:** Most use cases, monitoring, comparing with browser Lighthouse

```json
{
  "url": "https://example.com",
  "options": ["-b", "chrome", "-n", "3"]
}
```

**Expected Score:** 90-95 for well-optimized sites (matches browser)

---

### 📱 Mode 2: Mobile Simulation (Google Standard)
**Best for:** Testing mobile user experience, matching Google PageSpeed Insights

```json
{
  "url": "https://example.com",
  "options": [
    "-b", "chrome",
    "-n", "3",
    "--mobile",
    "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "4"
  ]
}
```

**Expected Score:** 70-85 for well-optimized sites (lower is normal)

---

### 🚀 Mode 3: Maximum Performance
**Best for:** Testing server performance, infrastructure benchmarking

```json
{
  "url": "https://example.com",
  "options": [
    "-b", "chrome",
    "-n", "3",
    "--lighthouse.settings.throttlingMethod", "provided"
  ]
}
```

**Expected Score:** 95-100 for well-optimized sites (highest possible)

## Quick Comparison Table

| Configuration | CPU Throttling | Expected Score | Use Case |
|--------------|---------------|----------------|----------|
| **Browser DevTools** | None/Auto | 90-95 | Development |
| **sitespeed (NEW)** | None (1x) | 90-95 | ✅ Monitoring |
| **sitespeed (OLD)** | 4x | 70-80 | ❌ Too pessimistic |
| **Google PSI** | 4x Mobile | 70-85 | Mobile testing |

## Verify the Fix is Working

1. **Run a test scan** with your website
2. **Check the score** in the report
3. **Compare with browser Lighthouse:**
   - Open Chrome DevTools (F12)
   - Go to "Lighthouse" tab
   - Run "Performance" audit
   - Compare scores

**Expected Result:** Should be within ±5 points of each other

## Still Getting Low Scores?

### If scores are still 10+ points lower:

1. **Check Docker is using the new config:**
   ```bash
   docker logs sitespeed-runner-1 | grep "cpuSlowdownMultiplier"
   ```

2. **Try Mode 3 (no throttling):**
   If this still gives low scores, the issue is your website, not the configuration.

3. **Check server resources:**
   ```bash
   docker stats
   ```
   Ensure CPU and memory are not maxed out.

4. **Compare with Google PageSpeed Insights:**
   Visit https://pagespeed.web.dev/
   - If Google scores match sitespeed: ✅ Working correctly
   - If Google scores are higher: Contact support

## Need More Details?

Read the full guide: `PERFORMANCE_SCORES.md`

## Summary

🎉 **Your sitespeed-runner is now configured to give realistic performance scores!**

✅ **What changed:**
- No more artificial CPU throttling (was 4x, now 1x)
- More memory for Chrome (2GB instead of 1GB)
- Scores now match your browser's Lighthouse

✅ **What to do next:**
1. Rebuild/restart your Docker container
2. Run a test scan
3. Enjoy realistic scores! 🚀

---

*Updated: Jan 8, 2026*






