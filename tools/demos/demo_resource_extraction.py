#!/usr/bin/env python3
"""Demonstration of enhanced resource extraction capabilities.

This script shows how the new resource extraction features work,
including string extraction, image extraction, and resource cataloging.
"""

import sys
import tempfile
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from extract.pbd.extraction.enhanced_image_extractor import EnhancedImageExtractor
from extract.pbd.extraction.resource_catalog import ResourceCatalog
from extract.pbd.extraction.string_extractor import StringResourceExtractor


def demo_string_extraction() -> None:







    """Demonstrate string resource extraction."""
    print("String Resource Extraction Demo")
    print("=" * 50)

    extractor = StringResourceExtractor()

    # Simulate P-code data with various string types
    test_data = b"""
    \x00\x00Application Title: PowerBuilder Demo App\x00\x00
    version="12.5.2"\x00
    author="John Doe"\x00
    copyright="2023 Acme Corp"\x00
    \x00\x00SELECT * FROM customers WHERE status = 'ACTIVE'\x00
    H\x00e\x00l\x00l\x00o\x00 \x00W\x00o\x00r\x00l\x00d\x00\x00\x00
    \x05\x00First\x06\x00Second\x05\x00Third
    """

    # Extract all strings
    strings = extractor.extract_strings_from_data(test_data, "demo.pbl")
    print(f"\nExtracted {len(strings)} strings:")
    for s in strings:
        print(f"  - {s}")

    # Extract properties
    properties = extractor.extract_property_strings(test_data)
    print(f"\nExtracted {len(properties)} properties:")
    for name, value in properties.items():
        print(f"  - {name} = {value}")

    # Extract string table
    table = extractor.extract_string_table(test_data)
    print(f"\nExtracted string table with {len(table)} entries:")
    for idx, string in table:
        print(f"  - [{idx}] {string}")


def demo_image_extraction() -> None:







    """Demonstrate image resource extraction."""
    print("\n\nImage Resource Extraction Demo")
    print("=" * 50)

    extractor = EnhancedImageExtractor()

    # Create test data with embedded images
    # Minimal BMP header
    bmp = b"BM\x46\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00"
    bmp += b"\x28\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00"
    bmp += b"\x01\x00\x18\x00" + b"\x00" * 40

    # Minimal GIF
    gif = b"GIF89a\x10\x00\x10\x00\xF0\x00\x00" + b"\x00" * 10 + b";"

    # Combine with other data
    test_data = b"PowerBuilder Object Data\x00\x00" + bmp + b"\x00\x00" + gif + b"\x00\x00END"

    # Extract images
    images = extractor.find_images_in_data(test_data, "window.srw")
    print(f"\nFound {len(images)} images:")
    for img in images:
        print(f"  - Format: {img['format']}")
        print(f"    Offset: {img['offset']}")
        print(f"    Size: {img['size']} bytes")
        if "metadata" in img and img["metadata"]:
            print(f"    Metadata: {img['metadata']}")


def demo_resource_catalog() -> None:







    """Demonstrate resource cataloging."""
    print("\n\nResource Catalog Demo")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "catalog.json"
        catalog = ResourceCatalog(catalog_path)

        # Add various resources
        print("\nAdding resources to catalog...")

        # Add strings from multiple sources
        catalog.add_string_resource("app.pbl", "Application Title")
        catalog.add_string_resource("window1.srw", "Application Title")  # Shared
        catalog.add_string_resource("window2.srw", "Application Title")  # Shared
        catalog.add_string_resource("window1.srw", "Window 1 Specific")
        catalog.add_string_resource("window2.srw", "Window 2 Specific")

        # Add images
        catalog.add_image_resource("app.pbl", {
            "format": "ico",
            "size": 1024,
            "metadata": {"width": 32, "height": 32},
        })
        catalog.add_image_resource("toolbar.srm", {
            "format": "bmp",
            "size": 2048,
            "metadata": {"width": 16, "height": 16},
        })

        # Generate statistics
        stats = catalog.generate_statistics()
        print(f"\nCatalog Statistics:")
        print(f"  - Total Resources: {stats['total_resources']}")
        print(f"  - Resource Types: {stats['resource_counts']}")
        print(f"  - Unique Objects: {stats['unique_objects']}")

        # Find common resources
        common = catalog.find_common_resources(min_usage=2)
        print(f"\nCommon Resources (used by 2+ objects):")
        for resource_id, objects in common.items():
            resource = catalog._find_resource(resource_id)
            if resource and "value" in resource:
                print(f"  - '{resource['value']}' used by:")
                for obj in objects:
                    print(f"    - {obj}")

        # Find resources for specific object
        print(f"\nResources used by window1.srw:")
        resources = catalog.find_object_resources("window1.srw")
        for rtype, resource_ids in resources.items():
            print(f"  - {rtype}: {len(resource_ids)} resources")

        # Save and reload catalog
        catalog.save_catalog()
        print(f"\nCatalog saved to: {catalog_path}")

        # Export summary
        summary_path = Path(tmpdir) / "summary.txt"
        catalog.export_summary(summary_path)
        print(f"Summary exported to: {summary_path}")

        # Show summary content
        print("\nSummary Preview:")
        print("-" * 40)
        lines = summary_path.read_text().split("\n")[:20]
        for line in lines:
            print(line)


def main() -> None:







    """Run all demonstrations."""
    print("PowerBuilder Resource Extraction Enhancement Demo")
    print("=" * 70)
    print("This demonstrates the new resource extraction capabilities:")
    print("- String resource extraction from P-code")
    print("- Enhanced image extraction from multiple object types")
    print("- Resource cataloging and cross-referencing")
    print()

    demo_string_extraction()
    demo_image_extraction()
    demo_resource_catalog()

    print("\n" + "=" * 70)
    print("Demo complete!")


if __name__ == "__main__":
    main()
