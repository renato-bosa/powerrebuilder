"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

# Define modules to document
MODULES = ["parse", "model", "extract", "decompile", "generate", "common"]

# Generate navigation structure
nav = mkdocs_gen_files.Nav()

# Process each module
for module in MODULES:
    module_path = Path(module)
    
    # Skip if module doesn't exist
    if not module_path.exists():
        continue
    
    # Process all Python files
    for path in sorted(module_path.rglob("*.py")):
        # Skip __pycache__ and tests
        if "__pycache__" in str(path) or "test_" in path.name:
            continue
            
        # Skip __init__ files with minimal content
        if path.name == "__init__.py" and path.stat().st_size < 100:
            continue
        
        # Create module path
        module_parts = list(path.relative_to(module_path).parts)
        if module_parts[-1] == "__init__.py":
            module_parts = module_parts[:-1]
        elif module_parts[-1].endswith(".py"):
            module_parts[-1] = module_parts[-1][:-3]
        
        # Skip if empty
        if not module_parts:
            module_parts = [module]
        
        # Create documentation path
        doc_path = Path("reference", module, *module_parts[:-1], f"{module_parts[-1]}.md")
        
        # Create full module name
        if module_parts == [module]:
            full_module = module
        else:
            full_module = f"{module}.{'.'.join(module_parts)}"
        
        # Add to navigation
        nav_parts = [module.capitalize()] + [p.replace("_", " ").title() for p in module_parts]
        nav[nav_parts] = doc_path.as_posix()
        
        # Write the page
        with mkdocs_gen_files.open(doc_path, "w") as fd:
            print(f"# {full_module}", file=fd)
            print(file=fd)
            print(f"::: {full_module}", file=fd)
        
        # Set edit path
        mkdocs_gen_files.set_edit_path(doc_path, path)

# Write navigation file
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())