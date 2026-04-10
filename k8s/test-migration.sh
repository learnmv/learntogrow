#!/bin/bash
set -e

echo "=== LearnToGrow Namespace Migration Test ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local url=$1
    local name=$2
    local count=10
    local success=0
    local failed=0

    echo "Testing $name ($url)..."
    for i in $(seq 1 $count); do
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            ((success++))
        else
            ((failed++))
        fi
    done

    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✓ All $count requests succeeded (100% success rate)${NC}"
    else
        echo -e "${RED}✗ $failed/$count requests failed ($success succeeded)${NC}"
    fi
    echo ""
}

# Test health endpoints
echo "1. Testing Health Endpoints"
echo "==========================="
test_endpoint "http://10.0.0.131:30800/health" "Dev Backend Health"
test_endpoint "http://10.0.0.131:30801/health" "Prod Backend Health"

# Test the problematic endpoint
echo "2. Testing Questions Endpoint (Previously Failing)"
echo "==================================================="
test_endpoint "http://10.0.0.131:30800/api/v1/questions/standard/10?limit=1" "Dev Questions API with limit=1"
test_endpoint "http://10.0.0.131:30801/api/v1/questions/standard/10?limit=1" "Prod Questions API with limit=1"

# Test namespace isolation
echo "3. Verifying Namespace Isolation"
echo "=================================="
echo "Checking dev namespace resources:"
kubectl get pods -n learntogrow-dev 2>/dev/null || echo "Namespace not found - migration may not be complete"

echo ""
echo "Checking prod namespace resources:"
kubectl get pods -n learntogrow-prod 2>/dev/null || echo "Namespace not found - migration may not be complete"

echo ""
echo "=== Test Complete ==="
