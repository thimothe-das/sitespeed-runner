#!/bin/bash
# Performance Mode Testing Script
# Tests your website with different Lighthouse configurations

# Configuration
API_URL="${API_URL:-http://localhost:5679}"
TEST_URL="${1:-https://example.com}"

if [ -z "$1" ]; then
    echo "Usage: $0 <url-to-test>"
    echo "Example: $0 https://therapeutelarochelle.fr"
    exit 1
fi

echo "🚀 Testing Performance Modes for: $TEST_URL"
echo "================================================"
echo ""

# Function to start a scan and wait for results
run_test() {
    local name="$1"
    local options="$2"
    
    echo "📊 Running: $name"
    echo "Options: $options"
    
    # Start scan
    response=$(curl -s -X POST "$API_URL/run-sitespeed" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$TEST_URL\", \"options\": $options}")
    
    scan_id=$(echo "$response" | grep -o '"scanId":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$scan_id" ]; then
        echo "❌ Failed to start scan"
        echo "Response: $response"
        return 1
    fi
    
    echo "   Scan ID: $scan_id"
    echo -n "   Waiting for completion"
    
    # Wait for completion
    status="queued"
    while [ "$status" = "queued" ] || [ "$status" = "running" ]; do
        sleep 5
        echo -n "."
        status_response=$(curl -s "$API_URL/status/$scan_id")
        status=$(echo "$status_response" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    done
    echo ""
    
    if [ "$status" = "completed" ]; then
        # Get report with main page metrics
        report=$(curl -s "$API_URL/report/$scan_id/main")
        
        # Extract lighthouse performance score
        perf_score=$(echo "$report" | grep -o '"performance":[0-9.]*' | head -1 | cut -d':' -f2)
        
        if [ -z "$perf_score" ]; then
            perf_score=$(echo "$report" | python3 -c "import sys,json;data=json.load(sys.stdin);print(data.get('metrics',{}).get('lighthouse',{}).get('performance','N/A'))" 2>/dev/null || echo "N/A")
        fi
        
        echo "   ✅ Performance Score: $perf_score"
        echo "   📄 Full Report: $API_URL/report/$scan_id/main"
        echo ""
        
        # Store result
        echo "$name|$perf_score" >> /tmp/perf_test_results.txt
    else
        echo "   ❌ Scan failed: $status"
        echo ""
    fi
}

# Clear previous results
rm -f /tmp/perf_test_results.txt

echo "Starting tests... (this will take several minutes)"
echo ""

# Test 1: New Default (No CPU throttling)
run_test "Mode 1: Realistic Performance (New Default)" \
    '["b", "chrome", "-n", "1"]'

# Test 2: Mobile with standard throttling
run_test "Mode 2: Mobile Device Simulation" \
    '["-b", "chrome", "-n", "1", "--mobile", "--lighthouse.settings.throttling.cpuSlowdownMultiplier", "4"]'

# Test 3: No throttling at all
run_test "Mode 3: Maximum Performance (No Throttling)" \
    '["-b", "chrome", "-n", "1", "--lighthouse.settings.throttlingMethod", "provided"]'

echo "================================================"
echo "📈 Test Results Summary"
echo "================================================"

if [ -f /tmp/perf_test_results.txt ]; then
    echo ""
    while IFS='|' read -r name score; do
        printf "%-45s: %s\n" "$name" "$score"
    done < /tmp/perf_test_results.txt
    echo ""
    echo "✅ Testing complete!"
    echo ""
    echo "💡 Tip: The 'Realistic Performance' mode should give you"
    echo "   scores similar to your browser's Lighthouse tool."
else
    echo "❌ No results collected"
fi

# Cleanup
rm -f /tmp/perf_test_results.txt


