#!/usr/bin/env python3
"""Command-line script to validate all templates in the project.

This script validates all Jinja2 templates used for code generation,
checking for syntax errors, naming conventions, and other issues.
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generate.template_validator import TemplateValidator


def main() -> None:







    """Main entry point for template validation."""
    parser = argparse.ArgumentParser(
        description="Validate Jinja2 templates for code generation",
    )
    parser.add_argument(
        "--template-dir",
        type=str,
        help="Template directory to validate (default: all template directories)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation results",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with error code if warnings are found",
    )

    args = parser.parse_args()

    # Determine template directories to validate
    if args.template_dir:
        template_dirs = [Path(args.template_dir)]
    else:
        # Validate all template directories
        template_dirs = [
            project_root / "generate" / "backend" / "templates",
            project_root / "generate" / "flutter" / "templates",
        ]

    total_valid = 0
    total_invalid = 0
    total_warnings = 0

    for template_dir in template_dirs:
        if not template_dir.exists():
            print(f"Template directory not found: {template_dir}")
            continue

        print(f"\nValidating templates in: {template_dir}")
        print("=" * 60)

        validator = TemplateValidator(str(template_dir))
        results = validator.validate_all_templates()

        # Count results
        valid_count = len(results["valid"])
        invalid_count = len(results["invalid"])
        warning_count = len(results["warnings"])

        total_valid += valid_count
        total_invalid += invalid_count
        total_warnings += warning_count

        # Display summary
        print(f"Valid templates: {valid_count}")
        print(f"Invalid templates: {invalid_count}")
        print(f"Templates with warnings: {warning_count}")

        # Show details if verbose or if there are issues
        if args.verbose or invalid_count > 0 or warning_count > 0:
            # Show invalid templates
            if results["invalid"]:
                print("\n❌ Invalid templates:")
                for result in results["invalid"]:
                    print(f"  - {result['template']}:")
                    for error in result["errors"]:
                        print(f"    ERROR: {error}")

            # Show templates with warnings
            if results["warnings"]:
                print("\n⚠️  Templates with warnings:")
                for result in results["warnings"]:
                    print(f"  - {result['template']}:")
                    for warning in result["warnings"]:
                        print(f"    WARNING: {warning}")

            # Show valid templates if verbose
            if args.verbose and results["valid"]:
                print("\n✅ Valid templates:")
                for result in results["valid"]:
                    print(f"  - {result['template']}")

    # Final summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total valid templates: {total_valid}")
    print(f"Total invalid templates: {total_invalid}")
    print(f"Total templates with warnings: {total_warnings}")

    # Determine exit code
    if total_invalid > 0:
        print("\n❌ Template validation failed!")
        sys.exit(1)
    elif total_warnings > 0 and args.fail_on_warning:
        print("\n⚠️  Template validation completed with warnings!")
        sys.exit(1)
    else:
        print("\n✅ Template validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
