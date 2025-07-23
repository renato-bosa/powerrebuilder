#!/usr/bin/env python3
"""Detect naming collisions in the codebase."""

import os
import re
import csv
from pathlib import Path
from collections import defaultdict

def find_python_names(file_path):
    """Extract function and class names from a Python file."""
    names = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find class definitions
        class_pattern = r'^\s*class\s+(\w+)'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            names.append({
                'name': match.group(1),
                'type': 'class',
                'file': str(file_path),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Find function definitions
        func_pattern = r'^\s*def\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            names.append({
                'name': match.group(1),
                'type': 'function',
                'file': str(file_path),
                'line': content[:match.start()].count('\n') + 1
            })
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return names

def count_references(name, src_dir):
    """Count how many times a name is referenced across the codebase."""
    count = 0
    pattern = re.compile(r'\b' + re.escape(name) + r'\b')
    
    for root, dirs, files in os.walk(src_dir):
        # Skip test directories
        if 'test' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    count += len(pattern.findall(content))
                except:
                    pass
    
    return count

def detect_collisions(src_dir):
    """Detect all naming collisions in the source directory."""
    all_names = []
    
    # Collect all names
    for root, dirs, files in os.walk(src_dir):
        # Skip test directories
        if 'test' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                names = find_python_names(file_path)
                all_names.extend(names)
    
    # Group by name
    name_groups = defaultdict(list)
    for item in all_names:
        # Skip private/magic methods
        if item['name'].startswith('_'):
            continue
        name_groups[item['name']].append(item)
    
    # Find collisions
    collisions = []
    for name, occurrences in name_groups.items():
        if len(occurrences) > 1:
            # Check if they're in different modules (real collision)
            modules = set()
            for occ in occurrences:
                # Get module path relative to src
                rel_path = os.path.relpath(occ['file'], src_dir)
                module = rel_path.replace(os.sep, '.').replace('.py', '')
                modules.add(module)
            
            # Only report if in different top-level modules
            if len(set(m.split('.')[0] for m in modules)) > 1:
                collisions.append({
                    'name': name,
                    'count': len(occurrences),
                    'occurrences': occurrences
                })
    
    return collisions

def create_resolution_plan(collisions, src_dir):
    """Create a plan to resolve collisions based on usage count."""
    resolution_plan = []
    
    for collision in collisions:
        name = collision['name']
        occurrences = collision['occurrences']
        
        # Count references for each occurrence
        usage_counts = []
        for occ in occurrences:
            # Count references in the codebase
            ref_count = count_references(name, src_dir)
            usage_counts.append({
                'occurrence': occ,
                'references': ref_count
            })
        
        # Sort by reference count (lowest first - rename the least used)
        usage_counts.sort(key=lambda x: x['references'])
        
        # Keep the most used one, rename others
        for i, item in enumerate(usage_counts[:-1]):  # All except the last (most used)
            occ = item['occurrence']
            # Generate new name based on module
            module_path = os.path.relpath(occ['file'], src_dir)
            module_name = Path(module_path).parent.name
            new_name = f"{module_name}_{name}" if module_name != '.' else f"renamed_{name}"
            
            resolution_plan.append({
                'old_name': name,
                'new_name': new_name,
                'file': occ['file'],
                'line': occ['line'],
                'type': occ['type'],
                'references': item['references']
            })
    
    return resolution_plan

def main():
    src_dir = "src"
    
    print("Detecting naming collisions...")
    collisions = detect_collisions(src_dir)
    
    print(f"\nFound {len(collisions)} naming collisions:")
    for collision in sorted(collisions, key=lambda x: x['count'], reverse=True)[:10]:
        print(f"\n{collision['name']} ({collision['count']} occurrences):")
        for occ in collision['occurrences']:
            rel_path = os.path.relpath(occ['file'], src_dir)
            print(f"  - {occ['type']} in {rel_path}:{occ['line']}")
    
    # Create resolution plan
    print("\nCreating collision resolution plan...")
    resolution_plan = create_resolution_plan(collisions, src_dir)
    
    # Save to CSV
    with open('build/collision_resolution_plan.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['old_name', 'new_name', 'file', 'line', 'type', 'references'])
        writer.writeheader()
        writer.writerows(resolution_plan)
    
    print(f"\nResolution plan saved to build/collision_resolution_plan.csv")
    print(f"Total renames needed: {len(resolution_plan)}")
    
    # Show sample renames
    print("\nSample renames (first 10):")
    for rename in resolution_plan[:10]:
        rel_path = os.path.relpath(rename['file'], src_dir)
        print(f"  {rename['old_name']} -> {rename['new_name']} in {rel_path}:{rename['line']}")

if __name__ == "__main__":
    main()