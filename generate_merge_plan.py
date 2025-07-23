#!/usr/bin/env python3
"""Generate specific file merge recommendations based on import analysis."""

import json
from pathlib import Path
from collections import defaultdict

def load_analysis():
    with open("/Users/michael/Projects/powerrebuilder/import_analysis.json", "r") as f:
        return json.load(f)

def generate_merge_plan(analysis):
    """Generate specific merge recommendations."""
    merges = defaultdict(list)
    
    # Group single-use modules by their importer
    for imported, importer in analysis["single_use_modules"].items():
        # Skip if it's a test or example module
        if "test" in imported or "example" in imported:
            continue
            
        # Group by common parent
        imported_parts = imported.split(".")
        importer_parts = importer.split(".")
        
        # Find common prefix
        common_prefix = []
        for i in range(min(len(imported_parts), len(importer_parts))):
            if imported_parts[i] == importer_parts[i]:
                common_prefix.append(imported_parts[i])
            else:
                break
        
        if len(common_prefix) >= 2:  # At least module.submodule level
            merge_target = ".".join(common_prefix)
            merges[merge_target].append((imported, importer))
    
    # Analyze leaf modules for grouping
    leaf_groups = defaultdict(list)
    for module in analysis["leaf_modules"]:
        if "test" in module or "example" in module:
            continue
            
        parts = module.split(".")
        if len(parts) >= 2:
            parent = ".".join(parts[:-1])
            leaf_groups[parent].append(module)
    
    return merges, leaf_groups

def main():
    analysis = load_analysis()
    merges, leaf_groups = generate_merge_plan(analysis)
    
    print("# PowerRebuilder Module Merge Plan\n")
    
    print("## Automated Merge Recommendations\n")
    print("Based on single-use import relationships, these modules should be merged:\n")
    
    # Sort by number of modules to merge (biggest wins first)
    sorted_merges = sorted(merges.items(), key=lambda x: len(x[1]), reverse=True)
    
    for target, modules in sorted_merges[:20]:  # Top 20
        if len(modules) >= 2:  # Only show groups with multiple merges
            print(f"### Merge into `{target}`")
            print(f"Combines {len(modules)} single-use modules:")
            for imported, importer in modules:
                print(f"- `{imported}` (imported only by `{importer}`)")
            print()
    
    print("\n## Leaf Module Consolidation\n")
    print("These leaf modules (no project imports) can be consolidated:\n")
    
    # Sort by number of leaf modules
    sorted_leaves = sorted(leaf_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    for parent, leaves in sorted_leaves[:15]:  # Top 15
        if len(leaves) >= 3:  # Only show groups with 3+ modules
            print(f"### `{parent}` has {len(leaves)} leaf modules")
            for leaf in sorted(leaves)[:10]:  # Show up to 10
                print(f"- `{leaf}`")
            if len(leaves) > 10:
                print(f"- ... and {len(leaves) - 10} more")
            print()
    
    print("\n## Specific File Operations\n")
    
    # Generate specific merge commands for top candidates
    print("### Common Utils Consolidation")
    print("```bash")
    print("# Merge common utility modules")
    print("cat src/common/utils/collections.py >> src/common/utils.py")
    print("cat src/common/utils/strings.py >> src/common/utils.py")
    print("cat src/common/utils/files.py >> src/common/utils.py")
    print("rm src/common/utils/collections.py src/common/utils/strings.py src/common/utils/files.py")
    print("```\n")
    
    print("### Extract PBD Structure Consolidation")
    print("```bash")
    print("# Create consolidated structures module")
    print("cat src/extract/pbd/header.py > src/extract/pbd/structures.py")
    print("cat src/extract/pbd/entry.py >> src/extract/pbd/structures.py")
    print("cat src/extract/pbd/node.py >> src/extract/pbd/structures.py")
    print("cat src/extract/pbd/data_block.py >> src/extract/pbd/structures.py")
    print("cat src/extract/pbd/object.py >> src/extract/pbd/structures.py")
    print("```\n")
    
    # Import update patterns
    print("### Import Update Patterns")
    print("```python")
    print("# Before:")
    print("from src.common.utils.strings import clean_string")
    print("from src.common.utils.collections import OrderedSet")
    print()
    print("# After:")
    print("from src.common.utils import clean_string, OrderedSet")
    print("```")

if __name__ == "__main__":
    main()