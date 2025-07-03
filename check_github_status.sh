#!/bin/bash
# Script to check if GitHub Actions checks have passed for the latest commit

# Configuration
GITHUB_REPO="danilobatson/ai-health-screening"
BRANCH="main"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking GitHub Actions status for ${GITHUB_REPO}:${BRANCH}${NC}"
echo "------------------------------------------------------"

# Get the latest commit hash
COMMIT=$(git rev-parse HEAD)
echo -e "Latest commit: ${YELLOW}$COMMIT${NC}"

# Check GitHub Actions status
echo -e "\n${YELLOW}Fetching check statuses...${NC}"
CHECKS=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/commits/$COMMIT/check-runs")

# Extract all check names and conclusions
BACKEND_CHECK=$(echo "$CHECKS" | grep -o '"name":"backend-quality"[^}]*' | grep -o '"conclusion":"[^"]*' | cut -d'"' -f4)
FRONTEND_CHECK=$(echo "$CHECKS" | grep -o '"name":"frontend-quality"[^}]*' | grep -o '"conclusion":"[^"]*' | cut -d'"' -f4)
E2E_CHECK=$(echo "$CHECKS" | grep -o '"name":"e2e-quality"[^}]*' | grep -o '"conclusion":"[^"]*' | cut -d'"' -f4)
SUMMARY_CHECK=$(echo "$CHECKS" | grep -o '"name":"quality-gates-summary"[^}]*' | grep -o '"conclusion":"[^"]*' | cut -d'"' -f4)

# Format status output
function format_status {
    if [ "$1" == "success" ]; then
        echo -e "${GREEN}✅ SUCCESS${NC}"
    elif [ "$1" == "failure" ]; then
        echo -e "${RED}❌ FAILED${NC}"
    elif [ "$1" == "neutral" ]; then
        echo -e "${YELLOW}⚠️ NEUTRAL${NC}"
    elif [ "$1" == "cancelled" ]; then
        echo -e "${YELLOW}⏹️ CANCELLED${NC}"
    elif [ -z "$1" ]; then
        echo -e "${YELLOW}⏳ PENDING${NC}"
    else
        echo -e "${YELLOW}❓ $1${NC}"
    fi
}

# Display results
echo -e "\n${YELLOW}Check Status:${NC}"
echo -e "Backend Quality:  $(format_status "$BACKEND_CHECK")"
echo -e "Frontend Quality: $(format_status "$FRONTEND_CHECK")"
echo -e "E2E Quality:      $(format_status "$E2E_CHECK")"
echo -e "Quality Summary:  $(format_status "$SUMMARY_CHECK")"

# Determine overall status
if [ "$BACKEND_CHECK" == "success" ] && [ "$FRONTEND_CHECK" == "success" ] && [ "$E2E_CHECK" == "success" ] && [ "$SUMMARY_CHECK" == "success" ]; then
    echo -e "\n${GREEN}✅ ALL CHECKS PASSED - Vercel should deploy automatically${NC}"
    exit 0
elif [ -z "$BACKEND_CHECK" ] || [ -z "$FRONTEND_CHECK" ] || [ -z "$E2E_CHECK" ] || [ -z "$SUMMARY_CHECK" ]; then
    echo -e "\n${YELLOW}⏳ SOME CHECKS STILL PENDING - Waiting for completion${NC}"
    exit 1
else
    echo -e "\n${RED}❌ SOME CHECKS FAILED - Vercel will not deploy${NC}"
    exit 1
fi
