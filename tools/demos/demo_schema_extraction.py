#!/usr/bin/env python3
"""Demo script for database schema extraction from PowerBuilder code.

This script demonstrates how to use the database schema extractor and
business logic mapper to analyze a PowerBuilder project and generate
comprehensive documentation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from decompile.analysis.business_logic_mapper import BusinessLogicMapper
from decompile.analysis.schema_documentation_generator import (
    generate_schema_documentation,
)


def main() -> None:







    """Run the schema extraction demo."""
    # Example project path - adjust to your PowerBuilder project
    project_path = Path("input")  # Change this to your project path
    output_path = Path("output/schema_demo")

    if not project_path.exists():
        print(f"Project path not found: {project_path}")
        print("Please create an 'input' directory with PowerBuilder source files")
        return

    output_path.mkdir(parents=True, exist_ok=True)

    print("PowerBuilder Database Schema Extraction Demo")
    print("=" * 50)
    print(f"Project: {project_path}")
    print(f"Output: {output_path}")
    print()

    # Step 1: Create the business logic mapper
    print("Step 1: Analyzing PowerBuilder project...")
    mapper = BusinessLogicMapper()

    # Step 2: Map the project
    print("Step 2: Extracting database schema and mapping business logic...")
    mapping_data = mapper.map_project(project_path)

    # Step 3: Generate documentation
    print("Step 3: Generating documentation...")

    # Generate in multiple formats
    for format_type in ["markdown", "html", "json"]:
        print(f"  - Generating {format_type} documentation...")
        doc_file = output_path / f"database_schema.{format_type if format_type != 'html' else 'html'}"
        generate_schema_documentation(
            mapping_data,
            output_format=format_type,
            output_path=doc_file,
        )
        print(f"    Saved to: {doc_file}")

    # Print summary
    print()
    print("Summary:")
    print("-" * 30)

    db_stats = mapping_data.get("database_schema", {}).get("statistics", {})
    logic_stats = mapping_data.get("statistics", {})

    print(f"Total tables found: {db_stats.get('total_tables', 0)}")
    print(f"Total columns: {db_stats.get('total_columns', 0)}")
    print(f"Total relationships: {db_stats.get('total_relationships', 0)}")
    print(f"Total business functions: {logic_stats.get('total_functions', 0)}")
    print(f"Total UI elements: {logic_stats.get('total_ui_elements', 0)}")
    print(f"Total data flows: {logic_stats.get('total_data_flows', 0)}")

    # Show operation breakdown
    op_counts = db_stats.get("operation_counts", {})
    if op_counts:
        print()
        print("Database Operations:")
        for op, count in sorted(op_counts.items()):
            print(f"  {op}: {count}")

    # Show some example tables
    tables = mapping_data.get("database_schema", {}).get("tables", {})
    if tables:
        print()
        print("Sample Tables:")
        for i, (table_name, table_info) in enumerate(list(tables.items())[:5]):
            print(f"  - {table_name} ({len(table_info.get('columns', []))} columns)")
            if i >= 4:  # Show max 5 tables
                if len(tables) > 5:
                    print(f"  ... and {len(tables) - 5} more tables")
                break

    print()
    print("Documentation generation complete!")


if __name__ == "__main__":
    main()
