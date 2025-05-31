#!/usr/bin/env python3
"""Automated opcode discovery pipeline.

This script automates the iterative process of:
1. Running the decoder on test files
2. Analyzing unknown opcodes
3. Adding missing opcodes to opcodes.yaml
4. Re-running until coverage targets are met
"""

import subprocess
import sys
from pathlib import Path
import logging
import yaml
from typing import Dict, List, Tuple, Set, Optional
import re
from collections import Counter, OrderedDict
import shutil
import time
import json
from datetime import datetime

from opcode_discovery_config import DiscoveryConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpcodeDiscoveryPipeline:
    """Automated pipeline for discovering and adding missing opcodes."""
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """Initialize the pipeline.
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or DiscoveryConfig()
        self.opcodes_yaml = Path('extract/pbd_core/opcodes.yaml')
        self.unknown_log = Path('unknown_opcodes.log')
        self.iteration_history = []
        
        # Ensure directories exist
        self.config.ensure_directories()
        
        # Set logging level based on config
        if self.config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def run_pipeline(self) -> Dict[str, float]:
        """Run the automated discovery pipeline.
        
        Returns:
            Dictionary mapping file names to final coverage percentages
        """
        # Get test files
        test_files = self.config.get_test_files()
        if not test_files:
            logger.error("No test files found!")
            return {}
        
        logger.info(f"Starting opcode discovery pipeline with {len(test_files)} test files")
        logger.info(f"Target coverage: {self.config.coverage_target * 100:.1f}%")
        
        # Log test files
        logger.info("Test files:")
        for f in test_files[:5]:  # Show first 5
            logger.info(f"  - {f.name} ({f.stat().st_size:,} bytes)")
        if len(test_files) > 5:
            logger.info(f"  ... and {len(test_files) - 5} more")
        
        iteration = 0
        previous_unknown_count = float('inf')
        start_time = time.time()
        
        # Initial backup
        self._backup_opcodes("initial")
        
        while iteration < self.config.max_iterations:
            iteration += 1
            iteration_start = time.time()
            logger.info(f"\n{'='*60}")
            logger.info(f"=== Iteration {iteration} ===")
            logger.info(f"{'='*60}")
            
            # Step 1: Run decoder and collect unknowns
            unknown_count, coverage_by_file = self._run_decoders(test_files)
            
            # Record iteration data
            iteration_data = {
                'iteration': iteration,
                'unknown_count': unknown_count,
                'coverage_by_file': coverage_by_file,
                'duration': time.time() - iteration_start
            }
            self.iteration_history.append(iteration_data)
            
            logger.info(f"Total unknown opcodes: {unknown_count}")
            for file, coverage in sorted(coverage_by_file.items()):
                logger.info(f"  {file}: {coverage * 100:.2f}% coverage")
            
            # Check if we've reached target coverage
            avg_coverage = sum(coverage_by_file.values()) / len(coverage_by_file) if coverage_by_file else 0
            if avg_coverage >= self.config.coverage_target:
                logger.info(f"✓ Reached target coverage: {avg_coverage * 100:.2f}%")
                break
            
            # Check if we're making progress
            if unknown_count >= previous_unknown_count:
                logger.warning("No improvement in unknown count, stopping")
                break
            
            previous_unknown_count = unknown_count
            
            # Step 2: Analyze unknown opcodes
            missing_opcodes = self._analyze_unknowns()
            
            if not missing_opcodes:
                logger.info("No new opcodes to add")
                break
            
            # Log what we're about to add
            logger.info(f"Found {len(missing_opcodes)} opcodes with missing variants:")
            for opcode, variants in sorted(missing_opcodes.items())[:5]:
                logger.info(f"  {opcode}: {len(variants)} variants")
            if len(missing_opcodes) > 5:
                logger.info(f"  ... and {len(missing_opcodes) - 5} more")
            
            # Step 3: Add missing opcodes
            added_count = self._add_missing_opcodes(missing_opcodes)
            logger.info(f"Added {added_count} new opcode definitions")
            
            if added_count == 0:
                logger.info("No opcodes were added, stopping")
                break
            
            # Backup after changes
            self._backup_opcodes(f"iteration_{iteration}")
            
            # Brief pause to ensure file system catches up
            time.sleep(0.5)
        
        # Final coverage report
        _, final_coverage = self._run_decoders(test_files)
        
        # Generate report
        total_duration = time.time() - start_time
        report = self._generate_report(final_coverage, total_duration)
        
        # Save report
        report_file = self.config.report_dir / f"discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("=== Final Coverage Report ===")
        logger.info("="*60)
        for file, coverage in sorted(final_coverage.items()):
            logger.info(f"{file}: {coverage * 100:.2f}%")
        
        avg_coverage = sum(final_coverage.values()) / len(final_coverage) if final_coverage else 0
        logger.info(f"\nAverage coverage: {avg_coverage * 100:.2f}%")
        logger.info(f"Total time: {total_duration:.1f} seconds")
        logger.info(f"Iterations: {len(self.iteration_history)}")
        
        return final_coverage
    
    def _run_decoders(self, test_files: List[Path]) -> Tuple[int, Dict[str, float]]:
        """Run decoders on all test files and count unknowns.
        
        Returns:
            Tuple of (total unknown count, coverage by file)
        """
        # Clear previous log
        if self.unknown_log.exists():
            self.unknown_log.unlink()
        
        coverage_by_file = {}
        
        for test_file in test_files:
            output_file = test_file.with_suffix('.pcode')
            cmd = [
                sys.executable,
                'decompile/pcode_decoder.py',
                str(test_file),
                str(output_file)
            ]
            
            # Run decoder
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to decode {test_file.name}: {result.stderr}")
                continue
        
        # Count unknowns from log
        if not self.unknown_log.exists():
            # No unknowns - perfect coverage
            for test_file in test_files:
                coverage_by_file[test_file.name] = 1.0
            return 0, coverage_by_file
        
        with open(self.unknown_log, 'r') as f:
            lines = f.readlines()
        
        # Count by file
        file_counts = Counter()
        total_instructions = Counter()
        
        for line in lines:
            match = re.search(r'Obj: (\S+)', line)
            if match:
                filename = match.group(1)
                file_counts[filename] += 1
        
        # Estimate total instructions (rough estimate based on file sizes)
        for test_file in test_files:
            filename = test_file.name
            # Rough estimate: ~1 instruction per 4 bytes
            file_size = test_file.stat().st_size
            estimated_instructions = file_size / 4
            total_instructions[filename] = estimated_instructions
        
        # Calculate coverage
        for filename in total_instructions:
            unknowns = file_counts.get(filename, 0)
            total = total_instructions[filename]
            if total > 0:
                coverage = 1.0 - (unknowns / total)
                coverage_by_file[filename] = max(0, coverage)
        
        return len(lines), coverage_by_file
    
    def _analyze_unknowns(self) -> Dict[str, List[Tuple[str, int]]]:
        """Analyze unknown opcodes and identify patterns.
        
        Returns:
            Dictionary mapping opcodes to variant lists
        """
        if not self.unknown_log.exists():
            return {}
        
        with open(self.unknown_log, 'r') as f:
            lines = f.readlines()
        
        # Extract opcode and next byte pairs
        pairs = []
        
        for line in lines:
            match = re.search(r'Opcode: (0x[A-F0-9]+).*Context: ([a-f0-9 ]+)', line)
            if match:
                opcode = match.group(1)
                context = match.group(2).split()
                
                # Find opcode position in context
                opcode_hex = opcode.lower()[2:]
                
                for i, byte in enumerate(context):
                    if byte == opcode_hex:
                        # If there's a next byte, record the pair
                        if i + 1 < len(context):
                            next_byte = context[i+1].upper()
                            pairs.append((opcode, f'0x{next_byte}'))
                        break
        
        # Count occurrences
        pair_counts = Counter(pairs)
        
        # Group by base opcode
        missing_opcodes = {}
        for (opcode, variant), count in pair_counts.items():
            if count >= self.config.min_occurrence_threshold:
                if opcode not in missing_opcodes:
                    missing_opcodes[opcode] = []
                missing_opcodes[opcode].append((variant, count))
        
        # Sort variants by count
        for opcode in missing_opcodes:
            missing_opcodes[opcode].sort(key=lambda x: x[1], reverse=True)
        
        return missing_opcodes
    
    def _add_missing_opcodes(self, missing_opcodes: Dict[str, List[Tuple[str, int]]]) -> int:
        """Add missing opcodes to opcodes.yaml.
        
        Args:
            missing_opcodes: Dictionary mapping opcodes to variant lists
            
        Returns:
            Number of opcodes added
        """
        # Load existing opcodes
        with open(self.opcodes_yaml, 'r') as f:
            opcodes = yaml.safe_load(f) or {}
        
        added_count = 0
        
        for opcode_hex, variants in missing_opcodes.items():
            opcode_int = int(opcode_hex, 16)
            
            # Get category from config
            category = self.config.get_category_for_opcode(opcode_int)
            
            # Check if opcode exists
            if opcode_int not in opcodes:
                # New opcode - create with variants
                opcodes[opcode_int] = {
                    'category': category,
                    'description': f'Auto-discovered operation {opcode_hex[2:]}',
                    'variants': {}
                }
            
            # Get or create variants section
            if 'variants' not in opcodes[opcode_int]:
                opcodes[opcode_int]['variants'] = {}
            
            existing_variants = opcodes[opcode_int]['variants']
            
            # Add missing variants
            for variant_hex, count in variants:
                variant_int = int(variant_hex, 16)
                
                if variant_int not in existing_variants:
                    # Determine the type based on patterns
                    if opcode_int in [0xC4, 0xC5, 0xC6, 0xC7]:
                        mnemonic = f"CONST_{opcode_hex[2:]}_{variant_hex[2:]}"
                        stack_effect = "0 -> 1"
                        description = f"Constant variant {opcode_hex[2:]}_{variant_hex[2:]}"
                    elif opcode_int == 0xE4:
                        mnemonic = f"LOAD_{opcode_hex[2:]}_{variant_hex[2:]}"
                        stack_effect = "0 -> 1"
                        description = f"Load operation {opcode_hex[2:]}_{variant_hex[2:]}"
                    elif opcode_int == 0xE8:
                        mnemonic = f"STORE_{opcode_hex[2:]}_{variant_hex[2:]}"
                        stack_effect = "1 -> 0"
                        description = f"Store operation {opcode_hex[2:]}_{variant_hex[2:]}"
                    elif opcode_int == 0xE0:
                        mnemonic = f"JUMP_COND_{variant_hex[2:]}"
                        stack_effect = "1 -> 0"
                        description = f"Conditional jump {variant_hex[2:]}"
                    elif opcode_int == 0xE1:
                        mnemonic = f"CALL_FUNC_{variant_hex[2:]}"
                        stack_effect = "varies"
                        description = f"Call function variant {variant_hex[2:]}"
                    else:
                        mnemonic = f"OP_{opcode_hex[2:]}_{variant_hex[2:]}"
                        stack_effect = "varies"
                        description = f"Auto-discovered {opcode_hex[2:]} variant {variant_hex[2:]}"
                    
                    existing_variants[variant_int] = {
                        'mnemonic': mnemonic,
                        'operands': ['value'],
                        'stack_effect': stack_effect,
                        'description': description,
                        'auto_discovered': True,
                        'discovery_count': count
                    }
                    added_count += 1
                    logger.debug(f"Added {opcode_hex} variant {variant_hex} (count: {count})")
        
        # Save updated opcodes
        if added_count > 0:
            with open(self.opcodes_yaml, 'w') as f:
                yaml.dump(opcodes, f, default_flow_style=False, sort_keys=True, width=120)
        
        return added_count
    
    def _backup_opcodes(self, tag: str):
        """Create a backup of opcodes.yaml."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.config.backup_dir / f"opcodes_{timestamp}_{tag}.yaml"
        shutil.copy(self.opcodes_yaml, backup_file)
        logger.debug(f"Created backup: {backup_file}")
    
    def _generate_report(self, final_coverage: Dict[str, float], total_duration: float) -> Dict:
        """Generate a comprehensive report of the discovery process."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'coverage_target': self.config.coverage_target,
                'max_iterations': self.config.max_iterations,
                'min_occurrence_threshold': self.config.min_occurrence_threshold,
                'test_files_count': len(self.config.get_test_files())
            },
            'results': {
                'final_coverage': final_coverage,
                'average_coverage': sum(final_coverage.values()) / len(final_coverage) if final_coverage else 0,
                'total_duration_seconds': total_duration,
                'iterations_completed': len(self.iteration_history)
            },
            'iteration_history': self.iteration_history
        }
        return report


def main():
    """Run the opcode discovery pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated opcode discovery pipeline')
    parser.add_argument('--coverage', type=float, default=0.95,
                      help='Target coverage percentage (0-1)')
    parser.add_argument('--max-files', type=int, default=10,
                      help='Maximum number of test files to use')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--test-file', type=str, action='append',
                      help='Specific test file to use (can be repeated)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = DiscoveryConfig()
    config.coverage_target = args.coverage
    config.max_test_files = args.max_files
    config.verbose = args.verbose
    
    if args.test_file:
        config.specific_test_files = [Path(f) for f in args.test_file]
    
    # Run pipeline
    pipeline = OpcodeDiscoveryPipeline(config)
    final_coverage = pipeline.run_pipeline()
    
    # Exit with appropriate code
    avg_coverage = sum(final_coverage.values()) / len(final_coverage) if final_coverage else 0
    if avg_coverage >= config.coverage_target:
        logger.info(f"\n✅ SUCCESS: Achieved {avg_coverage * 100:.2f}% average coverage")
        sys.exit(0)
    else:
        logger.warning(f"\n⚠️  WARNING: Only achieved {avg_coverage * 100:.2f}% average coverage")
        logger.warning(f"Target was {config.coverage_target * 100:.1f}%")
        sys.exit(1)


if __name__ == "__main__":
    main() 