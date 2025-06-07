#!/usr/bin/env python3
"""Comprehensive decompiler test suite.

This tool consolidates decompiler testing functionality from:
- test_corrected_decompiler.py (Full decompilation pipeline)
- test_simple_decompile.py (Simple opcode decoding)
- test_enhanced_decompiler.py (Enhanced decompiler features)

Usage:
    python test_decompiler.py simple <pcode_file>
    python test_decompiler.py full <pcode_file> [--output <file>]
    python test_decompiler.py batch <directory> [--pattern <pattern>]
    python test_decompiler.py opcodes [--verbose]
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from decompile.core.pcode_decoder import PCodeDecoder
from decompile.core.pcode_ir import IRInstruction, IROpcode
from decompile.core.expression_reconstructor import ExpressionReconstructor
from decompile.core.output_formatter import OutputFormatter
from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer
from decompile.opcodes.opcodes import OPCODE_DEFINITIONS, Opcode


class DecompilerTester:
    """Comprehensive decompiler testing tool."""
    
    def __init__(self):
        """Initialize tester."""
        self.decoder = PCodeDecoder()
        self.reconstructor = ExpressionReconstructor()
        self.formatter = OutputFormatter()
        self.analyzer = ControlFlowAnalyzer()
        
    def test_simple(self, pcode_file: Path) -> Dict[str, Any]:
        """Simple opcode decoding test.
        
        Args:
            pcode_file: Path to P-code file
            
        Returns:
            Test results
        """
        results = {
            "file": str(pcode_file),
            "success": False,
            "instructions": [],
            "errors": [],
            "statistics": {}
        }
        
        try:
            # Read P-code
            pcode_data = pcode_file.read_bytes()
            results["file_size"] = len(pcode_data)
            
            # Decode instructions
            offset = 0
            instruction_count = 0
            opcode_counts = {}
            
            while offset < len(pcode_data):
                try:
                    # Decode single instruction
                    instr, size = self._decode_instruction(pcode_data, offset)
                    
                    if instr:
                        results["instructions"].append({
                            "offset": offset,
                            "opcode": instr.opcode.name,
                            "operands": instr.operands,
                            "size": size
                        })
                        
                        # Count opcodes
                        opcode_counts[instr.opcode.name] = opcode_counts.get(instr.opcode.name, 0) + 1
                        instruction_count += 1
                        
                    offset += size
                    
                except Exception as e:
                    error = f"Failed to decode at offset {offset}: {str(e)}"
                    results["errors"].append(error)
                    offset += 1  # Skip bad byte
                    
            # Calculate statistics
            results["statistics"] = {
                "total_instructions": instruction_count,
                "unique_opcodes": len(opcode_counts),
                "most_common": sorted(opcode_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            results["success"] = len(results["errors"]) == 0
            
        except Exception as e:
            results["errors"].append(f"Fatal error: {str(e)}")
            
        return results
        
    def test_full(self, pcode_file: Path, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Full decompilation pipeline test.
        
        Args:
            pcode_file: Path to P-code file
            output_file: Optional output file for decompiled code
            
        Returns:
            Test results
        """
        results = {
            "file": str(pcode_file),
            "success": False,
            "stages": {},
            "output": "",
            "errors": []
        }
        
        try:
            # Read P-code
            pcode_data = pcode_file.read_bytes()
            
            # Stage 1: Decode to IR
            print("Stage 1: Decoding to IR...")
            ir_instructions = self.decoder.decode(pcode_data)
            results["stages"]["decode"] = {
                "success": True,
                "instruction_count": len(ir_instructions)
            }
            
            # Stage 2: Control flow analysis
            print("Stage 2: Analyzing control flow...")
            cfg = self.analyzer.analyze(ir_instructions)
            results["stages"]["control_flow"] = {
                "success": True,
                "basic_blocks": len(cfg.blocks) if hasattr(cfg, "blocks") else 0
            }
            
            # Stage 3: Expression reconstruction
            print("Stage 3: Reconstructing expressions...")
            ast = self.reconstructor.reconstruct(ir_instructions, cfg)
            results["stages"]["reconstruction"] = {
                "success": True,
                "node_count": self._count_ast_nodes(ast)
            }
            
            # Stage 4: Format output
            print("Stage 4: Formatting output...")
            output = self.formatter.format(ast)
            results["stages"]["formatting"] = {
                "success": True,
                "line_count": len(output.splitlines())
            }
            
            results["output"] = output
            results["success"] = True
            
            # Save output if requested
            if output_file:
                output_file.write_text(output)
                results["output_file"] = str(output_file)
                
        except Exception as e:
            results["errors"].append(f"Pipeline error: {str(e)}")
            import traceback
            results["errors"].append(traceback.format_exc())
            
        return results
        
    def test_batch(self, directory: Path, pattern: str = "*.fun") -> Dict[str, Any]:
        """Test multiple P-code files.
        
        Args:
            directory: Directory containing P-code files
            pattern: File pattern to match
            
        Returns:
            Batch test results
        """
        results = {
            "directory": str(directory),
            "pattern": pattern,
            "files_tested": 0,
            "successes": 0,
            "failures": 0,
            "file_results": []
        }
        
        # Find files
        pcode_files = list(directory.glob(pattern))
        results["files_found"] = len(pcode_files)
        
        # Test each file
        for pcode_file in pcode_files:
            print(f"Testing {pcode_file.name}...")
            
            # Run simple test
            file_result = self.test_simple(pcode_file)
            
            results["files_tested"] += 1
            if file_result["success"]:
                results["successes"] += 1
            else:
                results["failures"] += 1
                
            results["file_results"].append({
                "file": pcode_file.name,
                "success": file_result["success"],
                "instructions": file_result["statistics"].get("total_instructions", 0),
                "errors": len(file_result["errors"])
            })
            
        return results
        
    def test_opcodes(self, verbose: bool = False) -> Dict[str, Any]:
        """Test opcode definitions.
        
        Args:
            verbose: Show detailed information
            
        Returns:
            Opcode test results
        """
        results = {
            "total_opcodes": len(OPCODE_DEFINITIONS),
            "categories": {},
            "missing_handlers": [],
            "opcode_list": []
        }
        
        # Analyze opcodes
        for opcode_id, opcode_def in OPCODE_DEFINITIONS.items():
            # Categorize
            category = self._categorize_opcode(opcode_def)
            results["categories"][category] = results["categories"].get(category, 0) + 1
            
            # Check for handler
            if not hasattr(self.decoder, f"_handle_{opcode_def.name.lower()}"):
                results["missing_handlers"].append(opcode_def.name)
                
            # Add to list
            if verbose:
                results["opcode_list"].append({
                    "id": opcode_id,
                    "name": opcode_def.name,
                    "category": category,
                    "operands": opcode_def.operand_count,
                    "description": opcode_def.description
                })
                
        return results
        
    def _decode_instruction(self, data: bytes, offset: int) -> Tuple[Optional[IRInstruction], int]:
        """Decode single instruction.
        
        Args:
            data: P-code data
            offset: Current offset
            
        Returns:
            Instruction and size, or None and size
        """
        if offset >= len(data):
            return None, 0
            
        opcode = data[offset]
        
        # Look up opcode definition
        if opcode not in OPCODE_DEFINITIONS:
            return None, 1
            
        opcode_def = OPCODE_DEFINITIONS[opcode]
        
        # Create IR instruction
        ir_opcode = IROpcode[opcode_def.name]
        operands = []
        
        # Read operands (simplified)
        size = 1
        for i in range(opcode_def.operand_count):
            if offset + size < len(data):
                operands.append(data[offset + size])
                size += 1
                
        instr = IRInstruction(
            opcode=ir_opcode,
            operands=operands
        )
        
        return instr, size
        
    def _count_ast_nodes(self, ast: Any) -> int:
        """Count nodes in AST.
        
        Args:
            ast: AST root
            
        Returns:
            Node count
        """
        if not ast:
            return 0
            
        count = 1
        
        # Count children recursively
        if hasattr(ast, "children"):
            for child in ast.children:
                count += self._count_ast_nodes(child)
        elif hasattr(ast, "__dict__"):
            for value in ast.__dict__.values():
                if hasattr(value, "__class__") and value.__class__.__module__ != "builtins":
                    count += self._count_ast_nodes(value)
                    
        return count
        
    def _categorize_opcode(self, opcode: Opcode) -> str:
        """Categorize opcode by function.
        
        Args:
            opcode: Opcode definition
            
        Returns:
            Category name
        """
        name = opcode.name.lower()
        
        if "push" in name or "pop" in name:
            return "stack"
        elif "load" in name or "store" in name:
            return "memory"
        elif "call" in name or "return" in name:
            return "control"
        elif "add" in name or "sub" in name or "mul" in name or "div" in name:
            return "arithmetic"
        elif "and" in name or "or" in name or "not" in name:
            return "logical"
        elif "jump" in name or "branch" in name:
            return "branch"
        else:
            return "other"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive decompiler test suite"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Simple test
    simple_parser = subparsers.add_parser("simple", help="Simple opcode decoding")
    simple_parser.add_argument("pcode_file", type=Path, help="P-code file to test")
    
    # Full test
    full_parser = subparsers.add_parser("full", help="Full decompilation pipeline")
    full_parser.add_argument("pcode_file", type=Path, help="P-code file to test")
    full_parser.add_argument("--output", type=Path, help="Output file for decompiled code")
    
    # Batch test
    batch_parser = subparsers.add_parser("batch", help="Test multiple files")
    batch_parser.add_argument("directory", type=Path, help="Directory with P-code files")
    batch_parser.add_argument("--pattern", default="*.fun", help="File pattern")
    
    # Opcode test
    opcode_parser = subparsers.add_parser("opcodes", help="Test opcode definitions")
    opcode_parser.add_argument("--verbose", action="store_true", help="Show detailed info")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Create tester
    tester = DecompilerTester()
    
    # Execute command
    if args.command == "simple":
        if not args.pcode_file.exists():
            print(f"Error: File not found: {args.pcode_file}")
            return
            
        print(f"Running simple test on: {args.pcode_file}")
        results = tester.test_simple(args.pcode_file)
        
        print(f"\nResults:")
        print(f"  Success: {results['success']}")
        print(f"  File size: {results.get('file_size', 0)} bytes")
        print(f"  Instructions decoded: {results['statistics'].get('total_instructions', 0)}")
        print(f"  Unique opcodes: {results['statistics'].get('unique_opcodes', 0)}")
        
        if results['statistics'].get('most_common'):
            print(f"\nMost common opcodes:")
            for opcode, count in results['statistics']['most_common']:
                print(f"  {opcode}: {count}")
                
        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results['errors'][:5]:
                print(f"  - {error}")
                
    elif args.command == "full":
        if not args.pcode_file.exists():
            print(f"Error: File not found: {args.pcode_file}")
            return
            
        print(f"Running full pipeline test on: {args.pcode_file}")
        results = tester.test_full(args.pcode_file, args.output)
        
        print(f"\nResults:")
        print(f"  Success: {results['success']}")
        
        if results['stages']:
            print(f"\nStage Results:")
            for stage, info in results['stages'].items():
                print(f"  {stage}: {'✓' if info.get('success') else '✗'}")
                for key, value in info.items():
                    if key != 'success':
                        print(f"    {key}: {value}")
                        
        if results.get('output_file'):
            print(f"\nOutput saved to: {results['output_file']}")
        elif results.get('output'):
            print(f"\nDecompiled output ({len(results['output'].splitlines())} lines):")
            print("-" * 60)
            print(results['output'][:500] + "..." if len(results['output']) > 500 else results['output'])
            
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  {error}")
                
    elif args.command == "batch":
        if not args.directory.is_dir():
            print(f"Error: Not a directory: {args.directory}")
            return
            
        print(f"Running batch test in: {args.directory}")
        print(f"Pattern: {args.pattern}")
        results = tester.test_batch(args.directory, args.pattern)
        
        print(f"\nResults:")
        print(f"  Files found: {results['files_found']}")
        print(f"  Files tested: {results['files_tested']}")
        print(f"  Successes: {results['successes']}")
        print(f"  Failures: {results['failures']}")
        
        if results['file_results']:
            print(f"\nFile Results:")
            for result in results['file_results'][:20]:
                status = "✓" if result['success'] else "✗"
                print(f"  {status} {result['file']}: {result['instructions']} instructions")
                
    elif args.command == "opcodes":
        print("Testing opcode definitions...")
        results = tester.test_opcodes(args.verbose)
        
        print(f"\nOpcode Summary:")
        print(f"  Total opcodes: {results['total_opcodes']}")
        
        print(f"\nCategories:")
        for category, count in sorted(results['categories'].items()):
            print(f"  {category}: {count}")
            
        if results['missing_handlers']:
            print(f"\nMissing handlers ({len(results['missing_handlers'])}):")
            for name in results['missing_handlers'][:10]:
                print(f"  - {name}")
                
        if args.verbose and results['opcode_list']:
            print(f"\nOpcode Details:")
            for opcode in results['opcode_list'][:20]:
                print(f"  {opcode['id']:3d}: {opcode['name']:<20} ({opcode['category']}) - {opcode['description']}")


if __name__ == "__main__":
    main()