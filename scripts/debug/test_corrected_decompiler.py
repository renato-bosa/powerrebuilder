#!/usr/bin/env python3
"""Test the decompiler with corrected opcodes."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decompile.core.pcode_decoder import PCodeDecoder
from decompile.core.control_flow import ControlFlowAnalyzer
from decompile.core.stack_emulator import StackEmulator
from decompile.core.output_formatter import OutputFormatter


def test_decompile(pcode_file):
    """Test decompilation with corrected opcodes."""
    print(f"\nTesting decompilation of: {pcode_file}")
    print("=" * 80)
    
    # Read P-code
    with open(pcode_file, 'rb') as f:
        pcode_data = f.read()
    
    print(f"P-code size: {len(pcode_data)} bytes")
    
    # Step 1: Decode instructions
    decoder = PCodeDecoder()
    instructions = decoder.decode(pcode_data)
    
    print(f"\nDecoded {len(instructions)} instructions")
    
    # Show first 20 instructions
    print("\nFirst 20 instructions:")
    for i, instr in enumerate(instructions[:20]):
        print(f"  {i:04d}: {instr}")
    
    # Count opcode usage
    opcode_counts = {}
    unknown_count = 0
    for instr in instructions:
        if hasattr(instr, 'opcode'):
            mnemonic = instr.mnemonic if hasattr(instr, 'mnemonic') else f"OP_{instr.opcode:02X}"
            opcode_counts[mnemonic] = opcode_counts.get(mnemonic, 0) + 1
            if mnemonic.startswith("OP_"):
                unknown_count += 1
    
    print(f"\nOpcode usage (top 10):")
    for mnemonic, count in sorted(opcode_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {mnemonic:15s}: {count:5d} times")
    
    print(f"\nUnknown opcodes: {unknown_count}")
    
    # Step 2: Analyze control flow
    analyzer = ControlFlowAnalyzer()
    blocks = analyzer.analyze(instructions)
    
    print(f"\nControl flow analysis:")
    print(f"  Basic blocks: {len(blocks)}")
    
    # Step 3: Emulate stack
    emulator = StackEmulator()
    state = emulator.emulate(instructions)
    
    print(f"\nStack emulation:")
    print(f"  Final stack depth: {len(state.stack)}")
    print(f"  Generated statements: {len(state.statements)}")
    
    # Show first few statements
    if state.statements:
        print("\nFirst 10 statements:")
        for stmt in state.statements[:10]:
            print(f"  {stmt}")
    
    # Step 4: Format output
    formatter = OutputFormatter()
    source = formatter.format_function("test_function", state.statements, blocks)
    
    print("\nDecompiled source (first 30 lines):")
    lines = source.split('\n')
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:3d}: {line}")
    
    return len(instructions), unknown_count, len(state.stack)


def main():
    """Main test function."""
    test_files = [
        "tests/fixtures/pcode_files/test.pcode",
        "tests/fixtures/pcode_files/test_tj_report.pcode",
    ]
    
    results = []
    for test_file in test_files:
        if Path(test_file).exists():
            instr_count, unknown_count, stack_depth = test_decompile(test_file)
            results.append((test_file, instr_count, unknown_count, stack_depth))
    
    print("\n\nSummary:")
    print("=" * 80)
    for filename, instr_count, unknown_count, stack_depth in results:
        print(f"{Path(filename).name:30s}: {instr_count:5d} instructions, "
              f"{unknown_count:5d} unknown, stack depth: {stack_depth}")
    
    # Check if improvement
    print("\nAnalysis:")
    if all(stack_depth == 0 for _, _, _, stack_depth in results):
        print("✓ Stack is balanced! Opcodes are likely correct.")
    else:
        print("✗ Stack is not balanced. More work needed on opcodes.")


if __name__ == "__main__":
    main()