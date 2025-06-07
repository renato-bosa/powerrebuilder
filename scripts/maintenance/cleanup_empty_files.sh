#!/bin/bash
# Script to clean up empty and unnecessary files in the SIME-Finch project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting cleanup of empty and unnecessary files...${NC}"

# Function to safely remove files
safe_remove() {
    if [ -e "$1" ]; then
        echo -e "${YELLOW}Removing: $1${NC}"
        rm -rf "$1"
    fi
}

# 1. Remove empty __init__.py files
echo -e "\n${GREEN}Removing empty __init__.py files...${NC}"
find . -name "__init__.py" -type f -size 0 | while read -r file; do
    safe_remove "$file"
done

# 2. Remove nearly empty __init__.py files (only containing future imports)
echo -e "\n${GREEN}Removing nearly empty __init__.py files...${NC}"
find . -name "__init__.py" -type f | while read -r file; do
    # Check if file only contains "from __future__ import annotations" and whitespace
    if grep -v "^from __future__ import annotations$" "$file" | grep -v "^[[:space:]]*$" | grep -q .; then
        : # File has other content, skip
    else
        # File only has future import or is empty
        line_count=$(wc -l < "$file")
        if [ "$line_count" -le 2 ]; then
            safe_remove "$file"
        fi
    fi
done

# 3. Remove __pycache__ directories
echo -e "\n${GREEN}Removing __pycache__ directories...${NC}"
find . -name "__pycache__" -type d | while read -r dir; do
    safe_remove "$dir"
done

# 4. Remove .pyc files
echo -e "\n${GREEN}Removing .pyc files...${NC}"
find . -name "*.pyc" -type f | while read -r file; do
    safe_remove "$file"
done

# 5. Remove .DS_Store files
echo -e "\n${GREEN}Removing .DS_Store files...${NC}"
find . -name ".DS_Store" -type f | while read -r file; do
    safe_remove "$file"
done

# 6. Remove build artifacts
echo -e "\n${GREEN}Removing build artifacts...${NC}"
safe_remove "./sime_finch.egg-info"
safe_remove "./htmlcov"
safe_remove "./.coverage"
safe_remove "./dist"
safe_remove "./build"

# 7. Clean empty directories in output/
echo -e "\n${GREEN}Cleaning empty directories in output/...${NC}"
if [ -d "./output" ]; then
    find ./output -type d -empty -delete
fi

# 8. Remove duplicate parser implementations (as identified in analysis)
echo -e "\n${GREEN}Removing duplicate implementations...${NC}"
safe_remove "./parse/parsers"
safe_remove "./parse/pseudocode_parser.py"
safe_remove "./decompile/generators/unified_decompiler.py"
safe_remove "./decompile/generators"
safe_remove "./decompile/core/pcode_ir.py"
safe_remove "./decompile/templates"

# 9. Update .gitignore to prevent these files from coming back
echo -e "\n${GREEN}Updating .gitignore...${NC}"
cat >> .gitignore << 'EOF'

# Python cache and compiled files
__pycache__/
*.py[cod]
*$py.class
*.pyc

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# macOS
.DS_Store
.AppleDouble
.LSOverride

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Project specific
output/test_*
output/temp_*
EOF

echo -e "\n${GREEN}Cleanup complete!${NC}"
echo -e "${YELLOW}Note: You may need to update imports after removing duplicate files.${NC}"
echo -e "${YELLOW}Run tests to ensure everything still works correctly.${NC}"