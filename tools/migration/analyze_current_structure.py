#!/usr/bin/env python3
"""
Analyze current codebase structure to provide migration statistics.
"""

import os
from pathlib import Path
from collections import defaultdict
import json

class StructureAnalyzer:
    def __init__(self):
        self.base_path = Path.cwd()
        self.stats = defaultdict(lambda: defaultdict(int))
        self.file_list = defaultdict(list)
        self.duplicates = []
        
    def analyze_module(self, module_name: str):
        """Analyze a specific module."""
        module_path = self.base_path / module_name
        
        if not module_path.exists():
            return
            
        py_files = list(module_path.rglob("*.py"))
        
        # Exclude __pycache__ and test files
        py_files = [f for f in py_files if "__pycache__" not in str(f) and "test_" not in f.name]
        
        self.stats[module_name]["total_files"] = len(py_files)
        self.stats[module_name]["total_lines"] = 0
        
        # Analyze each file
        for py_file in py_files:
            relative_path = py_file.relative_to(self.base_path)
            self.file_list[module_name].append(str(relative_path))
            
            try:
                with open(py_file, 'r') as f:
                    lines = f.readlines()
                    self.stats[module_name]["total_lines"] += len(lines)
                    
                    # Check for common patterns
                    for line in lines:
                        if "class" in line and ":" in line:
                            self.stats[module_name]["classes"] += 1
                        elif "def " in line and ":" in line:
                            self.stats[module_name]["functions"] += 1
                            
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
        
        # Analyze structure depth
        max_depth = 0
        for f in py_files:
            depth = len(f.relative_to(module_path).parts)
            max_depth = max(max_depth, depth)
        self.stats[module_name]["max_depth"] = max_depth
        
    def find_duplicates(self):
        """Find potentially duplicate files based on naming patterns."""
        all_files = []
        for module, files in self.file_list.items():
            all_files.extend(files)
        
        # Look for similar names
        for i, file1 in enumerate(all_files):
            base1 = Path(file1).stem
            for file2 in all_files[i+1:]:
                base2 = Path(file2).stem
                
                # Check for common duplicate patterns
                if any([
                    base1 == base2,
                    f"{base1}_enhanced" == base2,
                    base1 == f"{base2}_enhanced",
                    f"{base1}_simple" == base2,
                    base1 == f"{base2}_simple",
                    f"{base1}_advanced" == base2,
                    base1 == f"{base2}_advanced",
                ]):
                    self.duplicates.append((file1, file2))
    
    def generate_report(self):
        """Generate analysis report."""
        report = ["# Current Structure Analysis\n"]
        
        # Overall statistics
        total_files = sum(s["total_files"] for s in self.stats.values())
        total_lines = sum(s["total_lines"] for s in self.stats.values())
        
        report.append("## Overall Statistics")
        report.append(f"- Total Python files: {total_files}")
        report.append(f"- Total lines of code: {total_lines:,}")
        report.append(f"- Average file size: {total_lines // total_files if total_files > 0 else 0} lines")
        report.append("")
        
        # Module breakdown
        report.append("## Module Breakdown")
        report.append("| Module | Files | Lines | Classes | Functions | Max Depth |")
        report.append("|--------|-------|-------|---------|-----------|-----------|")
        
        for module in sorted(self.stats.keys()):
            s = self.stats[module]
            report.append(f"| {module} | {s['total_files']} | {s['total_lines']:,} | "
                         f"{s['classes']} | {s['functions']} | {s['max_depth']} |")
        
        report.append("")
        
        # Potential duplicates
        if self.duplicates:
            report.append("## Potential Duplicate Files")
            for file1, file2 in self.duplicates[:20]:  # Show first 20
                report.append(f"- {file1} ↔ {file2}")
            if len(self.duplicates) > 20:
                report.append(f"... and {len(self.duplicates) - 20} more")
        
        report.append("")
        
        # Deep nesting
        report.append("## Files with Deep Nesting (>3 levels)")
        deep_files = []
        for module, files in self.file_list.items():
            for f in files:
                if len(Path(f).parts) > 4:
                    deep_files.append(f)
        
        for f in sorted(deep_files)[:20]:
            report.append(f"- {f}")
        
        if len(deep_files) > 20:
            report.append(f"... and {len(deep_files) - 20} more")
        
        report.append("")
        
        # Recommendations
        report.append("## Migration Impact Estimates")
        report.append(f"- Estimated file reduction: {total_files} → ~{total_files // 2} files (50% reduction)")
        report.append(f"- Estimated duplicate removal: ~{len(self.duplicates)} files")
        report.append(f"- Estimated test consolidation: ~40% reduction in test files")
        report.append(f"- Estimated total reduction: ~55-60% fewer files")
        
        return "\n".join(report)
    
    def save_file_inventory(self):
        """Save complete file inventory for migration planning."""
        inventory = {}
        for module, files in self.file_list.items():
            inventory[module] = sorted(files)
        
        with open("file_inventory.json", "w") as f:
            json.dump(inventory, f, indent=2)
    
    def run(self):
        """Run the analysis."""
        modules = ["extract", "parse", "decompile", "model", "generate", "common", "tools", "tests"]
        
        print("Analyzing codebase structure...")
        
        for module in modules:
            print(f"  Analyzing {module}...")
            self.analyze_module(module)
        
        print("Finding duplicates...")
        self.find_duplicates()
        
        print("Generating report...")
        report = self.generate_report()
        
        with open("STRUCTURE_ANALYSIS.md", "w") as f:
            f.write(report)
        
        self.save_file_inventory()
        
        print("\nAnalysis complete!")
        print("- Report saved to: STRUCTURE_ANALYSIS.md")
        print("- File inventory saved to: file_inventory.json")
        
        # Print summary
        print("\nSummary:")
        total_files = sum(s["total_files"] for s in self.stats.values())
        print(f"  Total Python files: {total_files}")
        print(f"  Potential duplicates: {len(self.duplicates)}")
        print(f"  Estimated reduction: ~{total_files // 2} files (50%)")


if __name__ == "__main__":
    analyzer = StructureAnalyzer()
    analyzer.run()