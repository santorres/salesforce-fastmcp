#!/bin/bash

################################################################################
# Channel Intelligence CLI - Test Script
# 
# This script runs a series of tests to verify the CLI is working correctly
# Usage: bash test_cli.sh
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/Users/santiagot/Applications/salesforce-fastmcp"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}   Channel Intelligence CLI - Test Suite${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/cli/channel_cli.py" ]; then
    echo -e "${RED}❌ Error: Not in correct project directory${NC}"
    echo "Expected: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Activate virtual environment
echo -e "${YELLOW}1. Activating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}2. Installing dependencies...${NC}"
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Test imports
echo -e "${YELLOW}3. Testing Python imports...${NC}"
python3 -c "from cli.channel_cli import cli; print('✅ CLI import successful')"
echo ""

# Test help command
echo -e "${YELLOW}4. Testing CLI help...${NC}"
python3 -m cli.channel_cli --help > /dev/null
echo -e "${GREEN}✅ CLI help working${NC}"
echo ""

# Test KPI command
echo -e "${YELLOW}5. Testing KPI command...${NC}"
echo "   Running: python3 -m cli.channel_cli kpi"
python3 -m cli.channel_cli kpi
echo -e "${GREEN}✅ KPI command successful${NC}"
echo ""

# Test Revenue command
echo -e "${YELLOW}6. Testing Revenue command...${NC}"
echo "   Running: python3 -m cli.channel_cli revenue"
python3 -m cli.channel_cli revenue
echo -e "${GREEN}✅ Revenue command successful${NC}"
echo ""

# Test Pipeline command
echo -e "${YELLOW}7. Testing Pipeline command...${NC}"
echo "   Running: python3 -m cli.channel_cli pipeline"
python3 -m cli.channel_cli pipeline
echo -e "${GREEN}✅ Pipeline command successful${NC}"
echo ""

# Test Risk command
echo -e "${YELLOW}8. Testing Risk command...${NC}"
echo "   Running: python3 -m cli.channel_cli risk"
python3 -m cli.channel_cli risk
echo -e "${GREEN}✅ Risk command successful${NC}"
echo ""

# Test JSON output
echo -e "${YELLOW}9. Testing JSON output...${NC}"
echo "   Running: python3 -m cli.channel_cli kpi --json"
OUTPUT=$(python3 -m cli.channel_cli kpi --json)
if echo "$OUTPUT" | grep -q '"data"'; then
    echo -e "${GREEN}✅ JSON output working${NC}"
else
    echo -e "${RED}❌ JSON output not valid${NC}"
fi
echo ""

# Test Top Partners command
echo -e "${YELLOW}10. Testing Top Partners command...${NC}"
echo "    Running: python3 -m cli.channel_cli top-partners --limit 5"
python3 -m cli.channel_cli top-partners --limit 5
echo -e "${GREEN}✅ Top Partners command successful${NC}"
echo ""

# Test Registrations command
echo -e "${YELLOW}11. Testing Registrations command...${NC}"
echo "    Running: python3 -m cli.channel_cli registrations"
python3 -m cli.channel_cli registrations
echo -e "${GREEN}✅ Registrations command successful${NC}"
echo ""

# Test Search command
echo -e "${YELLOW}12. Testing Search command...${NC}"
echo "    Running: python3 -m cli.channel_cli search 'test'"
python3 -m cli.channel_cli search "test"
echo -e "${GREEN}✅ Search command successful${NC}"
echo ""

# Test with filters
echo -e "${YELLOW}13. Testing with filters (revenue --breakdown partner)...${NC}"
echo "    Running: python3 -m cli.channel_cli revenue --breakdown partner"
python3 -m cli.channel_cli revenue --breakdown partner
echo -e "${GREEN}✅ Filter command successful${NC}"
echo ""

# Test with period
echo -e "${YELLOW}14. Testing with period (kpi --period THIS_FISCAL_YEAR)...${NC}"
echo "    Running: python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR"
python3 -m cli.channel_cli kpi --period THIS_FISCAL_YEAR
echo -e "${GREEN}✅ Period option successful${NC}"
echo ""

# Summary
echo -e "${BLUE}================================================================================${NC}"
echo -e "${GREEN}✅ All tests passed successfully!${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run individual commands as needed: python3 -m cli.channel_cli COMMAND"
echo "  2. View command help: python3 -m cli.channel_cli COMMAND --help"
echo "  3. See CLI_QUICKSTART.md for detailed examples"
echo ""
echo "To deactivate virtual environment when done:"
echo "  deactivate"
echo ""
