#!/usr/bin/env python3
"""Resolve naming collisions based on the resolution plan."""

import csv
import re
import os
from pathlib import Path

def apply_renames(resolution_plan_path):
    """Apply the renames from the resolution plan."""
    
    # Read the resolution plan
    with open(resolution_plan_path, 'r') as f:
        reader = csv.DictReader(f)
        renames = list(reader)
    
    print(f"Applying {len(renames)} renames...")
    
    # Group renames by file
    renames_by_file = {}
    for rename in renames:
        file_path = rename['file']
        if file_path not in renames_by_file:
            renames_by_file[file_path] = []
        renames_by_file[file_path].append(rename)
    
    successful_renames = 0
    failed_renames = 0
    
    # Process each file
    for file_path, file_renames in renames_by_file.items():
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Sort renames by line number in reverse order (bottom to top)
            # This prevents line number shifts from affecting subsequent renames
            file_renames.sort(key=lambda x: int(x['line']), reverse=True)
            
            # Apply each rename
            for rename in file_renames:
                old_name = rename['old_name']
                new_name = rename['new_name']
                line_num = int(rename['line'])
                rename_type = rename['type']
                
                # Split content into lines
                lines = content.split('\n')
                
                if line_num <= len(lines):
                    line = lines[line_num - 1]
                    
                    # Create pattern based on type
                    if rename_type == 'class':
                        pattern = r'(\s*class\s+)' + re.escape(old_name) + r'(\s*[\(:])'
                        replacement = r'\1' + new_name + r'\2'
                    else:  # function
                        pattern = r'(\s*def\s+)' + re.escape(old_name) + r'(\s*\()'
                        replacement = r'\1' + new_name + r'\2'
                    
                    # Apply the rename to the specific line
                    new_line = re.sub(pattern, replacement, line)
                    
                    if new_line != line:
                        lines[line_num - 1] = new_line
                        successful_renames += 1
                        print(f"✓ Renamed {old_name} -> {new_name} in {Path(file_path).name}:{line_num}")
                    else:
                        failed_renames += 1
                        print(f"✗ Failed to rename {old_name} in {Path(file_path).name}:{line_num}")
                
                # Rejoin lines
                content = '\n'.join(lines)
            
            # Write back the modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            failed_renames += len(file_renames)
    
    print(f"\nRename complete:")
    print(f"  Successful: {successful_renames}")
    print(f"  Failed: {failed_renames}")
    
    # Update imports
    print("\nUpdating imports...")
    update_imports(renames)

def update_imports(renames):
    """Update import statements to use new names."""
    
    # Create a mapping of old names to new names by module
    rename_map = {}
    for rename in renames:
        old_name = rename['old_name']
        new_name = rename['new_name']
        file_path = rename['file']
        
        # Get module path
        module_path = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        if module_path.startswith('src.'):
            module_path = module_path[4:]  # Remove 'src.' prefix
        
        if module_path not in rename_map:
            rename_map[module_path] = {}
        rename_map[module_path][old_name] = new_name
    
    # Find all Python files
    updated_files = 0
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Update imports
                    for module, name_map in rename_map.items():
                        for old_name, new_name in name_map.items():
                            # Pattern 1: from module import old_name
                            pattern1 = rf'(from\s+{re.escape(module)}\s+import\s+.*)\b{re.escape(old_name)}\b'
                            content = re.sub(pattern1, rf'\1{new_name}', content)
                            
                            # Pattern 2: from module import old_name as alias
                            pattern2 = rf'(from\s+{re.escape(module)}\s+import\s+)\b{re.escape(old_name)}\b(\s+as\s+)'
                            content = re.sub(pattern2, rf'\1{new_name}\2', content)
                            
                            # Pattern 3: import module; module.old_name
                            module_alias = module.split('.')[-1]
                            pattern3 = rf'\b{re.escape(module_alias)}\.{re.escape(old_name)}\b'
                            content = re.sub(pattern3, f'{module_alias}.{new_name}', content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        updated_files += 1
                        
                except Exception as e:
                    print(f"Error updating imports in {file_path}: {e}")
    
    print(f"Updated imports in {updated_files} files")

def main():
    resolution_plan_path = "build/collision_resolution_plan.csv"
    
    if not os.path.exists(resolution_plan_path):
        print("Error: collision_resolution_plan.csv not found. Run detect_collisions.py first.")
        return
    
    apply_renames(resolution_plan_path)

if __name__ == "__main__":
    main()