#!/usr/bin/env python3
"""Compare decompilation results across different implementations.
"""

import subprocess
import sys
from pathlib import Path


class DecompilerComparison:
    def __init__(self):
        self.test_file = None

    def find_test_file(self):
        """Find a suitable test PBD file."""
        # Look for smaller PBD files for easier comparison
        pbd_files = list(Path("input/pbd_files").glob("*.pbd"))
        if pbd_files:
            # Sort by size and pick a smaller one
            pbd_files.sort(key=lambda p: p.stat().st_size)
            self.test_file = pbd_files[0]
            print(f"Selected test file: {self.test_file} ({self.test_file.stat().st_size} bytes)")
            return True
        return False

    def run_sime_finch(self):
        """Run SIME Finch decompiler."""
        print("\n📦 Running SIME Finch decompiler...")
        try:
            # Use your existing extraction
            from decompile.core.pcode_decoder import decode_pcode
            from extract.pbd_io.reader import PBDReader

            reader = PBDReader(str(self.test_file))
            objects = reader.read_objects()

            results = []
            for obj in objects[:5]:  # First 5 objects
                if hasattr(obj, 'pcode') and obj.pcode:
                    instructions = decode_pcode(obj.pcode)
                    results.append({
                        'name': obj.name,
                        'instructions': instructions,
                        'count': len(instructions),
                    })

            return results
        except Exception as e:
            print(f"Error: {e}")
            return []

    def run_powerbuilder_decompile(self):
        """Run powerbuilder-decompile."""
        print("\n🐍 Running powerbuilder-decompile...")

        # Check if it's installed
        pb_decompile = Path("reference/powerbuilder-decompile/main.py")
        if not pb_decompile.exists():
            print("powerbuilder-decompile not found. Run download script first.")
            return []

        try:
            # Run the Python decompiler
            result = subprocess.run(
                [sys.executable, str(pb_decompile), str(self.test_file)],
                capture_output=True,
                text=True,
                cwd=pb_decompile.parent, check=False,
            )

            if result.returncode == 0:
                # Parse output (this is simplified - actual parsing would be more complex)
                return [{'output': result.stdout}]
            print(f"Error: {result.stderr}")
            return []
        except Exception as e:
            print(f"Error running powerbuilder-decompile: {e}")
            return []

    def compare_results(self, sime_results, pb_results):
        """Compare decompilation results."""
        print("\n📊 Comparison Results:")
        print("=" * 60)

        if sime_results and pb_results:
            print(f"\nSIME Finch found {len(sime_results)} objects")
            for obj in sime_results[:3]:
                print(f"  - {obj['name']}: {obj['count']} instructions")

            print(f"\npowerbuilder-decompile output length: {len(pb_results[0].get('output', ''))}")

            # For a real comparison, you'd parse both outputs into comparable formats
            print("\n⚠️  Note: Direct comparison requires parsing both outputs to same format")
            print("   This is a proof-of-concept. Full implementation would:")
            print("   1. Parse powerbuilder-decompile output")
            print("   2. Normalize instruction representations")
            print("   3. Compare instruction sequences")
            print("   4. Highlight differences")

    def generate_report(self):
        """Generate comparison report."""
        output_path = Path("docs/decompiler_comparison_results.md")

        with open(output_path, 'w') as f:
            f.write("# Decompiler Comparison Results\n\n")
            f.write(f"Test file: {self.test_file}\n\n")

            f.write("## Next Steps for Full Comparison\n\n")
            f.write("1. **Standardize Output Format**\n")
            f.write("   - Parse powerbuilder-decompile output\n")
            f.write("   - Convert both to common instruction format\n\n")

            f.write("2. **Implement Semantic Comparison**\n")
            f.write("   - Compare stack effects\n")
            f.write("   - Match control flow structures\n")
            f.write("   - Identify equivalent operations\n\n")

            f.write("3. **Create Test Suite**\n")
            f.write("   - Small PowerBuilder programs\n")
            f.write("   - Known P-code sequences\n")
            f.write("   - Expected decompilation results\n\n")

            f.write("4. **Measure Accuracy**\n")
            f.write("   - Instruction coverage\n")
            f.write("   - Semantic correctness\n")
            f.write("   - Recompilability\n")

        print(f"\n📄 Report saved to {output_path}")

def main():
    comparator = DecompilerComparison()

    if not comparator.find_test_file():
        print("No PBD files found for testing")
        return

    # Run decompilers
    sime_results = comparator.run_sime_finch()
    pb_results = comparator.run_powerbuilder_decompile()

    # Compare results
    comparator.compare_results(sime_results, pb_results)

    # Generate report
    comparator.generate_report()

if __name__ == "__main__":
    main()
