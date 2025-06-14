#!/usr/bin/env python3
"""
Analyze Failed DataWindow Extraction Patterns

This script analyzes the pipeline logs to identify patterns in DataWindow extraction failures
and creates a comprehensive report for implementing the 100% accuracy improvements.
"""

import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class FailureAnalyzer:
    """Analyzes DataWindow extraction failures from pipeline logs"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.failures = defaultdict(list)
        self.dat_corruptions = []
        self.parse_errors = []
        self.statistics = {
            'total_failures': 0,
            'by_suffix': Counter(),
            'by_size': Counter(),
            'by_pbd': Counter(),
            'by_error_type': Counter()
        }
        
    def analyze_logs(self):
        """Analyze all log files for failure patterns"""
        log_files = [
            'pipeline_run_2025-06-14.log',
            'pipeline_test_2025-06-14.log'
        ]
        
        for log_file in log_files:
            log_path = self.log_dir / log_file
            if log_path.exists():
                self._parse_log_file(log_path)
                
    def _parse_log_file(self, log_path: Path):
        """Parse a single log file for failures"""
        print(f"Analyzing {log_path.name}...")
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Pattern for failed syntax extraction
        syntax_pattern = r'WARNING: Failed to extract syntax from ([^\s]+)'
        for match in re.finditer(syntax_pattern, content):
            filename = match.group(1)
            self.failures['syntax_extraction'].append(filename)
            self._update_statistics(filename, 'syntax_extraction')
            
        # Pattern for DAT block corruption
        dat_pattern = r'Declared data length (\d+) extends beyond file size (\d+)'
        for match in re.finditer(dat_pattern, content):
            self.dat_corruptions.append({
                'declared_size': int(match.group(1)),
                'file_size': int(match.group(2))
            })
            self.statistics['by_error_type']['dat_corruption'] += 1
            
        # Pattern for parse entry failures
        parse_pattern = r'Failed to parse entry (\d+) at offset (\d+)'
        for match in re.finditer(parse_pattern, content):
            self.parse_errors.append({
                'entry': int(match.group(1)),
                'offset': int(match.group(2))
            })
            self.statistics['by_error_type']['parse_entry'] += 1
            
    def _update_statistics(self, filename: str, error_type: str):
        """Update statistics for a failed file"""
        self.statistics['total_failures'] += 1
        
        # Extract suffix
        suffix_match = re.search(r'_([^.]+)\.dwo', filename)
        if suffix_match:
            suffix = f"_{suffix_match.group(1)}"
            self.statistics['by_suffix'][suffix] += 1
        else:
            self.statistics['by_suffix']['_other'] += 1
            
        # Extract PBD file
        pbd_match = re.search(r'([^/]+\.pbd)', filename)
        if pbd_match:
            pbd_name = pbd_match.group(1)
            self.statistics['by_pbd'][pbd_name] += 1
            
    def generate_test_cases(self) -> Dict[str, List[str]]:
        """Generate test cases based on failure patterns"""
        test_cases = {
            'syntax_extraction_tests': [],
            'dat_corruption_tests': [],
            'parse_entry_tests': [],
            'suffix_specific_tests': defaultdict(list)
        }
        
        # Group failures by pattern
        for failure_type, files in self.failures.items():
            test_cases[f'{failure_type}_tests'] = files[:10]  # Top 10 examples
            
        # Group by suffix for targeted testing
        for filename in self.failures['syntax_extraction']:
            suffix_match = re.search(r'_([^.]+)\.dwo', filename)
            if suffix_match:
                suffix = suffix_match.group(1)
                test_cases['suffix_specific_tests'][suffix].append(filename)
                
        return test_cases
        
    def generate_report(self) -> str:
        """Generate a comprehensive failure analysis report"""
        report = []
        report.append("# DataWindow Extraction Failure Analysis Report\n")
        report.append(f"Total Failures Analyzed: {self.statistics['total_failures']}\n")
        
        # Failure by suffix
        report.append("\n## Failures by DataWindow Type (Suffix)")
        for suffix, count in self.statistics['by_suffix'].most_common():
            percentage = (count / self.statistics['total_failures']) * 100
            report.append(f"- {suffix}: {count} ({percentage:.1f}%)")
            
        # Failure by PBD
        report.append("\n## Most Affected PBD Files")
        for pbd, count in self.statistics['by_pbd'].most_common(10):
            report.append(f"- {pbd}: {count} failures")
            
        # DAT corruption analysis
        if self.dat_corruptions:
            report.append("\n## DAT Block Corruption Analysis")
            report.append(f"Total DAT corruptions: {len(self.dat_corruptions)}")
            
            # Analyze magic numbers
            magic_numbers = Counter()
            for corruption in self.dat_corruptions:
                declared = corruption['declared_size']
                if declared > 0x40000000:  # Likely a magic number
                    magic_numbers[hex(declared)] += 1
                    
            report.append("\nSuspected Magic Numbers:")
            for magic, count in magic_numbers.most_common():
                report.append(f"- {magic}: {count} occurrences")
                
        # Parse entry failures
        if self.parse_errors:
            report.append(f"\n## Parse Entry Failures")
            report.append(f"Total parse failures: {len(self.parse_errors)}")
            
        # Test case recommendations
        report.append("\n## Recommended Test Cases")
        test_cases = self.generate_test_cases()
        for test_type, cases in test_cases.items():
            if isinstance(cases, list) and cases:
                report.append(f"\n### {test_type}")
                for case in cases[:5]:  # Show first 5
                    report.append(f"- {case}")
            elif isinstance(cases, dict):
                report.append(f"\n### {test_type}")
                for suffix, files in list(cases.items())[:5]:
                    report.append(f"- {suffix}: {len(files)} files")
                    
        return '\n'.join(report)
        
    def export_failure_list(self, output_path: Path):
        """Export complete list of failed files for testing"""
        failure_data = {
            'summary': dict(self.statistics),
            'failed_files': dict(self.failures),
            'dat_corruptions': self.dat_corruptions,
            'parse_errors': self.parse_errors,
            'test_cases': self.generate_test_cases()
        }
        
        # Convert Counter objects to dict for JSON serialization
        failure_data['summary']['by_suffix'] = dict(failure_data['summary']['by_suffix'])
        failure_data['summary']['by_size'] = dict(failure_data['summary']['by_size'])
        failure_data['summary']['by_pbd'] = dict(failure_data['summary']['by_pbd'])
        failure_data['summary']['by_error_type'] = dict(failure_data['summary']['by_error_type'])
        
        with open(output_path, 'w') as f:
            json.dump(failure_data, f, indent=2)
            
        print(f"Exported failure data to {output_path}")


def main():
    """Main analysis function"""
    # Analyze logs
    analyzer = FailureAnalyzer(project_root / 'logs')
    analyzer.analyze_logs()
    
    # Generate and save report
    report = analyzer.generate_report()
    report_path = project_root / 'docs' / 'datawindow_failure_analysis.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Analysis report saved to {report_path}")
    
    # Export failure data for testing
    failure_data_path = project_root / 'tests' / 'test_data' / 'failed_datawindows.json'
    failure_data_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.export_failure_list(failure_data_path)
    
    # Print summary
    print(f"\nAnalysis Summary:")
    print(f"Total failures: {analyzer.statistics['total_failures']}")
    print(f"DAT corruptions: {len(analyzer.dat_corruptions)}")
    print(f"Parse errors: {len(analyzer.parse_errors)}")
    
    # Show top failure patterns
    print("\nTop failure patterns:")
    for suffix, count in analyzer.statistics['by_suffix'].most_common(5):
        print(f"  {suffix}: {count}")


if __name__ == '__main__':
    main()