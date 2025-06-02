#!/bin/bash
# Download all PowerBuilder P-code reverse engineering resources

set -e  # Exit on error

echo "🚀 Starting PowerBuilder resource download..."

# Create reference directory if it doesn't exist
mkdir -p reference

# Function to check if directory exists before cloning
clone_if_not_exists() {
    local url=$1
    local dir=$2
    if [ ! -d "$dir" ]; then
        echo "📥 Cloning $url..."
        git clone "$url" "$dir"
    else
        echo "✅ $dir already exists, skipping clone"
    fi
}

# Function to download with wget
download_docs() {
    local url=$1
    local dir=$2
    local desc=$3
    
    if [ ! -d "$dir" ]; then
        echo "📥 Downloading $desc..."
        mkdir -p "$dir"
        wget --mirror --convert-links --adjust-extension --page-requisites --no-parent \
             --no-host-directories --directory-prefix="$dir" \
             "$url" 2>/dev/null || echo "⚠️  Warning: Some files may not have downloaded completely"
    else
        echo "✅ $dir already exists, skipping download"
    fi
}

echo ""
echo "=== 1/9: pbdviewer Repository ==="
clone_if_not_exists "https://github.com/hucxy/pbdviewer.git" "reference/pbdviewer"

echo ""
echo "=== 2/9: powerbuilder-decompile Repository ==="
clone_if_not_exists "https://github.com/sijms/powerbuilder-decompile.git" "reference/powerbuilder-decompile"

echo ""
echo "=== 3/9: PowerBuilder Native Interface Docs ==="
download_docs "https://docs.appeon.com/pb2025/native_interface_programmers_guide_and_reference/" \
              "reference/pbni_docs" \
              "PBNI documentation"

echo ""
echo "=== 4/9: PowerBuilder Users Guide ==="
download_docs "https://docs.appeon.com/pb2022/pbug/" \
              "reference/pb_users_guide" \
              "PowerBuilder Users Guide"

echo ""
echo "=== 5/9: SAP Community Forum Thread ==="
if [ ! -d "reference/sap_forum_export" ]; then
    echo "📥 Archiving SAP forum thread..."
    mkdir -p "reference/sap_forum_export"
    wget -E -H -k -K -p \
         "https://community.sap.com/topics/powerbuilder/questions/2013/07/22/conversion-of-pbd-to-pbl.html" \
         -P "reference/sap_forum_export" 2>/dev/null || echo "⚠️  Forum may require login"
else
    echo "✅ SAP forum already archived"
fi

echo ""
echo "=== 6/9: StackExchange Discussion ==="
if [ ! -d "reference/stackexchange_pbvm" ]; then
    echo "📥 Archiving StackExchange thread..."
    mkdir -p "reference/stackexchange_pbvm"
    wget -E -H -k -K -p \
         "https://reverseengineering.stackexchange.com/questions/16859/reverse-engineering-windows-powerbuilder-binaries" \
         -P "reference/stackexchange_pbvm" 2>/dev/null || true
else
    echo "✅ StackExchange already archived"
fi

echo ""
echo "=== 7/9: PowerBuilder Code Examples ==="
clone_if_not_exists "https://github.com/thansuoi113/PowerBuilder-Code-Examples.git" "reference/pb_code_examples"

echo ""
echo "=== 8/9: PBLib Website Mirror ==="
download_docs "https://pblib.com/" \
              "reference/pblib_mirror" \
              "PBLib website"

echo ""
echo "=== 9/9: DataWindow Syntax Docs ==="
if [ ! -d "reference/datawindow_docs" ]; then
    echo "📥 Downloading DataWindow documentation..."
    mkdir -p "reference/datawindow_docs"
    wget -E -H -k -K -p \
         "https://docs.appeon.com/pb2022/datawindow_reference/Describe_func.html" \
         -P "reference/datawindow_docs" 2>/dev/null || true
else
    echo "✅ DataWindow docs already downloaded"
fi

echo ""
echo "=== Creating file index ==="
cd reference
tree -L 2 > file_index.txt 2>/dev/null || ls -la > file_index.txt
cd ..

echo ""
echo "✅ Resource download complete!"
echo ""
echo "📊 Summary:"
echo "  - Repositories cloned: pbdviewer, powerbuilder-decompile, pb_code_examples"
echo "  - Documentation downloaded: PBNI, Users Guide, DataWindow"
echo "  - Forums archived: SAP Community, StackExchange"
echo "  - Website mirrored: PBLib"
echo ""
echo "📁 All resources saved in: ./reference/"
echo "📋 File index created at: ./reference/file_index.txt"
echo ""
echo "Next steps:"
echo "  1. Run: python extract/scripts/extract_all_opcodes.py"
echo "  2. Run: python generate/scripts/generate_opcode_reference.py"
echo "  3. Start analyzing opcode implementations in each repository" 