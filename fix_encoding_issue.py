#!/usr/bin/env python3
"""Fix the encoding issue in PowerRebuilder extraction.

This script patches the decode_powerbuilder_name function to remove
the problematic byte-order swapping that corrupts valid UTF-16LE data.
"""

import shutil
from pathlib import Path


def fix_encoding_issue():
    """Apply the fix to the binary.py file."""
    binary_py = Path("src/extract/utils/binary.py")
    
    # Create backup
    backup_path = binary_py.with_suffix(".py.backup")
    if not backup_path.exists():
        shutil.copy2(binary_py, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Read the file
    with open(binary_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and comment out the problematic byte-order fix strategy
    lines = content.split('\n')
    new_lines = []
    in_strategy_5 = False
    strategy_5_indent = 0
    
    for i, line in enumerate(lines):
        # Detect start of Strategy 5
        if "Strategy 5: Try byte-order corrected UTF-16" in line:
            in_strategy_5 = True
            # Comment out this line and track indentation
            new_lines.append(line.replace("# Strategy 5", "# DISABLED - Strategy 5"))
            continue
        
        # If we're in Strategy 5 block
        if in_strategy_5:
            # Check if this is the try: line
            if line.strip() == "try:":
                strategy_5_indent = len(line) - len(line.lstrip())
                new_lines.append(" " * strategy_5_indent + "# DISABLED - This was corrupting valid UTF-16LE data")
                new_lines.append(" " * strategy_5_indent + "# " + line.strip())
                continue
            
            # Check if we've exited the strategy 5 block
            if line.strip() and not line.startswith(" " * strategy_5_indent):
                in_strategy_5 = False
                new_lines.append(line)
                continue
            
            # Comment out lines in strategy 5
            if line.strip():
                new_lines.append(" " * strategy_5_indent + "# " + line.strip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write the fixed content
    fixed_content = '\n'.join(new_lines)
    with open(binary_py, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed encoding issue in {binary_py}")
    print("\nThe problematic byte-order swapping has been disabled.")
    print("Valid UTF-16LE data will no longer be corrupted during extraction.")
    
    # Also create a proper fix by adding a simpler decode function
    print("\nAdding improved PowerBuilder name decoder...")
    
    # Find the location to insert the new function
    insert_index = -1
    for i, line in enumerate(new_lines):
        if line.startswith("def decode_powerbuilder_name"):
            insert_index = i
            break
    
    if insert_index > 0:
        # Insert the improved decoder before the original
        improved_decoder = '''
def decode_powerbuilder_name_simple(data: bytes, is_unicode_context: bool = False) -> str:
    """Simple, reliable PowerBuilder name decoder without corruption 'fixes'.
    
    Args:
        data: Raw bytes of the object name  
        is_unicode_context: Whether the file uses Unicode encoding
        
    Returns:
        Decoded object name
    """
    if not data:
        return ""
    
    # Remove trailing nulls
    if is_unicode_context:
        # UTF-16LE - remove pairs of null bytes from end
        while len(data) >= 2 and data[-2:] == b'\\x00\\x00':
            data = data[:-2]
        
        # Ensure even number of bytes for UTF-16
        if len(data) % 2 != 0:
            data = data[:-1]
        
        if data:
            try:
                return data.decode('utf-16le')
            except Exception:
                # Fallback to ASCII
                pass
    
    # ASCII mode or fallback
    data = data.rstrip(b'\\x00')
    if data:
        try:
            return data.decode('ascii')
        except Exception:
            # Last resort - Latin-1 (accepts all bytes)
            return data.decode('latin-1', errors='replace')
    
    return ""


'''
        new_lines.insert(insert_index, improved_decoder)
        
        # Now modify the original function to use the simple version
        for i in range(insert_index + 1, len(new_lines)):
            if "def decode_powerbuilder_name" in new_lines[i]:
                # Add a line at the beginning of the function to use simple version
                j = i + 1
                while j < len(new_lines) and '"""' in new_lines[j]:
                    j += 1
                # Find the end of docstring
                while j < len(new_lines) and not new_lines[j].strip().startswith('"""'):
                    j += 1
                j += 1  # Skip the closing """
                
                # Insert the redirect to simple version
                indent = "    "
                new_lines.insert(j, f"{indent}# Use simplified decoder to avoid corruption")
                new_lines.insert(j + 1, f"{indent}return decode_powerbuilder_name_simple(data, is_unicode_context)")
                break
        
        # Write the final fixed version
        final_content = '\n'.join(new_lines)
        with open(binary_py, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print("Added simplified decoder function.")
    
    return backup_path


if __name__ == "__main__":
    print("PowerRebuilder Encoding Fix")
    print("=" * 50)
    print("\nThis fix addresses the issue where valid UTF-16LE object names")
    print("were being corrupted by unnecessary byte-order swapping.")
    print()
    
    backup = fix_encoding_issue()
    
    print("\n" + "=" * 50)
    print("Fix applied successfully!")
    print(f"\nOriginal file backed up to: {backup}")
    print("\nYou can now re-run the extraction and should see proper object names")
    print("instead of single-character filenames.")
    print("\nTo revert, run: cp {} src/extract/utils/binary.py".format(backup))