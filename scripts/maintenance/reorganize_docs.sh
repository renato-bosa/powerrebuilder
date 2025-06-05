#!/bin/bash
# Script to reorganize documentation files

# Create docs/project directory if it doesn't exist
mkdir -p docs/project

# Move project documentation files
echo "Moving project documentation to docs/project/..."

# Move CONFIG_FILES.md
if [ -f "CONFIG_FILES.md" ]; then
    mv CONFIG_FILES.md docs/project/
    echo "✓ Moved CONFIG_FILES.md to docs/project/"
fi

# Move PROJECT_TREE.md  
if [ -f "PROJECT_TREE.md" ]; then
    mv PROJECT_TREE.md docs/project/
    echo "✓ Moved PROJECT_TREE.md to docs/project/"
fi

# Move markdownlint.json to root config location
if [ -f "markdownlint.json" ] && [ ! -f ".markdownlint.json" ]; then
    mv markdownlint.json .markdownlint.json
    echo "✓ Renamed markdownlint.json to .markdownlint.json"
fi

# Update README.md to reference new locations if needed
echo ""
echo "Documentation reorganization complete!"
echo "Don't forget to update any references to these files in README.md or other docs."