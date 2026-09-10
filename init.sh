#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "🏢 Polyfloor — Agent Onboarding & Environment Health Check"
echo "=========================================================="

# 1. Check Nix & Flakes
if command -v nix >/dev/null 2>&1; then
    echo "✓ Nix detected: $(nix --version)"
    if nix flake --help >/dev/null 2>&1; then
        echo "✓ Nix Flakes enabled"
    else
        echo "⚠️  Nix Flakes may not be enabled"
    fi
else
    echo "❌ Nix not found in PATH"
fi

# 2. Check Node & Python environment
if command -v node >/dev/null 2>&1; then
    echo "✓ Node.js: $(node --version)"
else
    echo "⚠️  Node.js not found in current shell"
fi

if command -v python3 >/dev/null 2>&1; then
    echo "✓ Python: $(python3 --version)"
else
    echo "⚠️  Python3 not found in current shell"
fi

if command -v just >/dev/null 2>&1; then
    echo "✓ just task runner: $(just --version)"
else
    echo "⚠️  just task runner not found in current shell"
fi

# 3. Check Staged Assets
ASSET_DIR="frontend/static/assets"
if [ -d "$ASSET_DIR" ] && [ -f "$ASSET_DIR/interiors.png" ]; then
    echo "✓ Staged assets present at $ASSET_DIR"
else
    echo "⚠️  Assets missing or incomplete at $ASSET_DIR"
fi

# 4. Git Status
echo "----------------------------------------------------------"
echo "📌 Current Git Branch / Status:"
git status -s || true

# 5. Uncompleted Features
echo "----------------------------------------------------------"
echo "📋 Next 3 Uncompleted Features (from feature_list.json):"
if command -v jq >/dev/null 2>&1 && [ -f "feature_list.json" ]; then
    jq -r '.features[] | select(.passes == false) | "  - [\(.id)] \(.title) (\(.category))"' feature_list.json | head -n 3
else
    echo "⚠️  feature_list.json or jq not available"
fi
echo "=========================================================="
