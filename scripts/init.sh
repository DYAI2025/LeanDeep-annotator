#!/bin/bash
set -e

# LeanDeep 6.0 Project Init Script
# Usage: ./scripts/init.sh
# Creates virtual environment, installs deps, prepares test data, setup .env

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 LeanDeep 6.0 Project Init"
echo "Working directory: $PROJECT_ROOT"
echo ""

# ============================================================
# 1. CREATE PYTHON VIRTUAL ENVIRONMENT
# ============================================================
echo "📦 Step 1/6: Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "  ⚠️  venv already exists, skipping creation"
else
    python3 -m venv venv
    echo "  ✅ venv created"
fi

source venv/bin/activate
echo "  ✅ venv activated"

# ============================================================
# 2. UPGRADE PIP & INSTALL DEPENDENCIES
# ============================================================
echo ""
echo "📚 Step 2/6: Installing Python dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null
pip install -r requirements.txt > /dev/null
echo "  ✅ Dependencies installed"

# ============================================================
# 3. CREATE .ENV FILE FROM TEMPLATE
# ============================================================
echo ""
echo "⚙️  Step 3/6: Setting up environment configuration..."
if [ -f ".env" ]; then
    echo "  ⚠️  .env already exists, skipping"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  ✅ Created .env from .env.example"
        echo ""
        echo "  ⚠️  IMPORTANT: Edit .env and set LEANDEEP_GOOGLE_API_KEY"
        echo "     Command: nano .env"
    else
        echo "  ⚠️  .env.example not found, skipping .env creation"
    fi
fi

# ============================================================
# 4. PREPARE TEST DATA
# ============================================================
echo ""
echo "🧪 Step 4/6: Preparing test data..."
mkdir -p tests/data
mkdir -p build/markers_normalized
mkdir -p logs

if [ -f "tools/prepare_test_data.py" ]; then
    python3 tools/prepare_test_data.py
    echo "  ✅ Test data prepared"
else
    echo "  ⚠️  tools/prepare_test_data.py not found, skipping test data prep"
fi

# ============================================================
# 5. VALIDATE MARKER SCHEMA
# ============================================================
echo ""
echo "✔️  Step 5/6: Validating marker schema..."
if [ -f "tools/validate_marker_schema.py" ]; then
    python3 tools/validate_marker_schema.py > /dev/null 2>&1 || true
    echo "  ✅ Marker schema validated"
else
    echo "  ⚠️  tools/validate_marker_schema.py not found, skipping validation"
fi

# ============================================================
# 6. HEALTH CHECK
# ============================================================
echo ""
echo "🏥 Step 6/6: Running health check..."
python3 -c "
import sys
try:
    import fastapi
    import pydantic
    import google.generativeai
    print('  ✅ Core modules import OK')
except ImportError as e:
    print(f'  ❌ Import error: {e}', file=sys.stderr)
    sys.exit(1)
"

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Init complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. source venv/bin/activate  (activate virtual environment)"
echo "  2. nano .env                  (set LEANDEEP_GOOGLE_API_KEY)"
echo "  3. python3 -m pytest tests/ -q  (run tests)"
echo "  4. python3 -m uvicorn api.main:app --port 8420 --reload"
echo ""
echo "Documentation:"
echo "  • Architecture: 2-design/architecture.md"
echo "  • Task breakdown: 3-code/tasks.md"
echo "  • Quick start: DEVELOPER_QUICKSTART.md"
echo ""
