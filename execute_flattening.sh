#!/bin/bash
# Directory Flattening Script for PowerRebuilder
# This script executes the flattening plan to reduce directory depth

set -e  # Exit on error

echo "=== PowerRebuilder Directory Flattening Script ==="
echo "This script will flatten directories with 1-2 files"
echo ""

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo "ERROR: File not found: $1"
        return 1
    fi
    return 0
}

# Function to check if directory exists
check_dir() {
    if [ ! -d "$1" ]; then
        echo "ERROR: Directory not found: $1"
        return 1
    fi
    return 0
}

# Backup current state
echo "Creating backup of current imports..."
find src -name "*.py" -exec grep -l "from src\.\|import src\." {} \; > imports_backup.txt

echo ""
echo "=== Phase 1: Moving Files ==="

# 1. Move decompile/utils/version.py
echo "1. Moving decompile/utils/version.py..."
if check_file "src/decompile/utils/version.py"; then
    mv src/decompile/utils/version.py src/decompile/version.py
    echo "   ✓ Moved to src/decompile/version.py"
fi

# 2. Move parse/utils/loader.py
echo "2. Moving parse/utils/loader.py..."
if check_file "src/parse/utils/loader.py"; then
    mv src/parse/utils/loader.py src/parse/grammar_loader.py
    echo "   ✓ Moved to src/parse/grammar_loader.py"
fi

# 3. Move parse/error_recovery/strategy.py
echo "3. Moving parse/error_recovery/strategy.py..."
if check_file "src/parse/error_recovery/strategy.py"; then
    mv src/parse/error_recovery/strategy.py src/parse/recovery_strategy.py
    echo "   ✓ Moved to src/parse/recovery_strategy.py"
fi

# 4. Move decompile/visualization/visualizer.py
echo "4. Moving decompile/visualization/visualizer.py..."
if check_file "src/decompile/visualization/visualizer.py"; then
    mv src/decompile/visualization/visualizer.py src/decompile/cfg_visualizer.py
    echo "   ✓ Moved to src/decompile/cfg_visualizer.py"
fi

# 5. Move generate/mappings/powerbuilder_flutter_mapping.json
echo "5. Moving generate/mappings/powerbuilder_flutter_mapping.json..."
if check_file "src/generate/mappings/powerbuilder_flutter_mapping.json"; then
    # First, we need to copy it to flutter directory where it's expected
    cp src/generate/mappings/powerbuilder_flutter_mapping.json src/generate/converters/flutter/
    echo "   ✓ Copied to src/generate/converters/flutter/"
    # Keep original in mappings for now until we verify everything works
fi

echo ""
echo "=== Phase 2: Updating Imports ==="

# Update imports for version.py
echo "Updating decompile.utils.version imports..."
find src -name "*.py" -exec sed -i '' 's/from src\.decompile\.utils\.version/from src.decompile.version/g' {} \;
find src -name "*.py" -exec sed -i '' 's/import src\.decompile\.utils\.version/import src.decompile.version/g' {} \;

# Update imports for loader.py -> grammar_loader.py
echo "Updating parse.utils.loader imports..."
find src -name "*.py" -exec sed -i '' 's/from src\.parse\.utils\.loader/from src.parse.grammar_loader/g' {} \;
find src -name "*.py" -exec sed -i '' 's/import src\.parse\.utils\.loader/import src.parse.grammar_loader/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.utils\.loader/from .grammar_loader/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.\.utils\.loader/from ..grammar_loader/g' {} \;

# Update imports for strategy.py -> recovery_strategy.py
echo "Updating parse.error_recovery.strategy imports..."
find src -name "*.py" -exec sed -i '' 's/from src\.parse\.error_recovery\.strategy/from src.parse.recovery_strategy/g' {} \;
find src -name "*.py" -exec sed -i '' 's/import src\.parse\.error_recovery\.strategy/import src.parse.recovery_strategy/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.error_recovery\.strategy/from .recovery_strategy/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.error_recovery import strategy/from . import recovery_strategy/g' {} \;

# Update imports for visualizer.py -> cfg_visualizer.py
echo "Updating decompile.visualization.visualizer imports..."
find src -name "*.py" -exec sed -i '' 's/from src\.decompile\.visualization\.visualizer/from src.decompile.cfg_visualizer/g' {} \;
find src -name "*.py" -exec sed -i '' 's/import src\.decompile\.visualization\.visualizer/import src.decompile.cfg_visualizer/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.visualization\.visualizer/from .cfg_visualizer/g' {} \;
find src -name "*.py" -exec sed -i '' 's/from \.visualization import visualizer/from . import cfg_visualizer/g' {} \;

echo ""
echo "=== Phase 3: Removing Empty Directories ==="

# Remove __init__.py files from directories we're removing
rm -f src/decompile/utils/__init__.py 2>/dev/null || true
rm -f src/parse/utils/__init__.py 2>/dev/null || true
rm -f src/parse/error_recovery/__init__.py 2>/dev/null || true
rm -f src/decompile/visualization/__init__.py 2>/dev/null || true
rm -f src/generate/mappings/__init__.py 2>/dev/null || true

# Remove empty directories
rmdir src/decompile/utils 2>/dev/null && echo "✓ Removed src/decompile/utils" || true
rmdir src/parse/utils 2>/dev/null && echo "✓ Removed src/parse/utils" || true
rmdir src/parse/error_recovery 2>/dev/null && echo "✓ Removed src/parse/error_recovery" || true
rmdir src/decompile/visualization 2>/dev/null && echo "✓ Removed src/decompile/visualization" || true
rmdir src/generate/mappings 2>/dev/null && echo "✓ Removed src/generate/mappings" || true

echo ""
echo "=== Summary ==="
echo "Flattening complete!"
echo ""
echo "Files moved:"
[ -f "src/decompile/version.py" ] && echo "  ✓ src/decompile/version.py"
[ -f "src/parse/grammar_loader.py" ] && echo "  ✓ src/parse/grammar_loader.py"
[ -f "src/parse/recovery_strategy.py" ] && echo "  ✓ src/parse/recovery_strategy.py"
[ -f "src/decompile/cfg_visualizer.py" ] && echo "  ✓ src/decompile/cfg_visualizer.py"
[ -f "src/generate/converters/flutter/powerbuilder_flutter_mapping.json" ] && echo "  ✓ JSON mapping copied to flutter directory"

echo ""
echo "Next steps:"
echo "1. Run tests to ensure everything still works"
echo "2. Commit changes with: git add -A && git commit -m 'refactor: Flatten directories with 1-2 files'"
echo "3. Remove the original JSON file if tests pass: rm src/generate/mappings/powerbuilder_flutter_mapping.json"