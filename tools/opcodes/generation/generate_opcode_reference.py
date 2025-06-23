#!/usr/bin/env python3
"""Generate a unified opcode implementation from comprehensive reference.
Creates both a Python dispatch table and documentation.
"""

import json
from collections import defaultdict
from pathlib import Path

import yaml


class OpcodeReferenceGenerator:
    def __init__(self) -> None:

        self.reference = None
        self.load_reference()

    def load_reference(self) -> None:




        """Load the comprehensive opcode reference."""
        json_path = Path("reference/opcode_reference.json")
        yaml_path = Path("reference/opcode_reference.yaml")

        if json_path.exists():
            with open(json_path) as f:
                self.reference = json.load(f)
        elif yaml_path.exists():
            with open(yaml_path) as f:
                self.reference = yaml.safe_load(f)
        else:
            msg = "Run extract_all_opcodes.py first to generate reference"
            raise FileNotFoundError(
                msg,
            )

    def generate_python_implementation(self) -> None:




        """Generate Python opcode implementation."""
        output_path = Path("decompile/opcodes_unified.py")

        with open(output_path, "w") as f:
            f.write('"""\n')
            f.write("Unified PowerBuilder P-code opcode definitions.\n")
            f.write("Generated from multiple reference implementations.\n")
            f.write('"""\n\n')

            f.write("from dataclasses import dataclass\n")
            f.write("from typing import Callable\n\n")

            # Generate opcode info class
            f.write("@dataclass\n")
            f.write("class OpcodeInfo:\n")
            f.write('    """Information about a P-code opcode."""\n')
            f.write("    opcode: int\n")
            f.write("    name: str\n")
            f.write("    length: int\n")
            f.write("    category: str | None = None\n")
            f.write("    stack_effect: str | None = None\n")
            f.write("    handler: Callable | None = None\n\n")

            # Generate opcode definitions
            f.write("# Opcode definitions\n")
            f.write("OPCODES: dict[int, OpcodeInfo] = {\n")

            for opcode_hex, info in self.reference["opcodes"].items():
                opcode = int(opcode_hex, 16)
                name = info["name"]
                length = info["length"]
                category = info.get("category", "None")
                stack = info.get("stack_effect", "None")

                if category != "None":
                    category = f'"{category}"'
                if stack != "None":
                    stack = f'"{stack}"'

                f.write(
                    f'    0x{opcode:02X}: OpcodeInfo({opcode}, "{name}", {length}, ', )
                f.write(f"{category}, {stack}), \n")

            f.write("}\n\n")

            # Generate category groups
            f.write("# Opcode categories\n")
            categories = defaultdict(list)
            for opcode_hex, info in self.reference["opcodes"].items():
                if "category" in info:
                    categories[info["category"]].append(int(opcode_hex, 16))

            for category, opcodes in sorted(categories.items()):
                var_name = f"{category.upper()}_OPCODES"
                f.write(f"{var_name} = {sorted(opcodes)}\n")

            f.write("\n")

            # Generate type variant mappings
            if (
                "patterns" in self.reference
                and "type_variants" in self.reference["patterns"]
            ):
                f.write("# Type-specific opcode variants\n")
                f.write("TYPE_VARIANTS = {\n")

                for base_op, types in self.reference["patterns"][
                    "type_variants"
                ].items():
                    f.write(f'    "{base_op}": {sorted(types)}, \n')

                f.write("}\n\n")

            # Generate helper functions
            f.write("def get_opcode_name(opcode: int) -> str:\n")
            f.write('    """Get the name of an opcode."""\n')
            f.write("    info = OPCODES.get(opcode)\n")
            f.write('    return info.name if info else f"UNKNOWN_{opcode:02X}"\n\n')

            f.write("def get_opcode_length(opcode: int) -> int:\n")
            f.write('    """Get the length of an opcode instruction."""\n')
            f.write("    info = OPCODES.get(opcode)\n")
            f.write("    return info.length if info else 1\n\n")

            f.write("def get_stack_effect(opcode: int) -> str | None: \n")
            f.write('    """Get the stack effect of an opcode."""\n')
            f.write("    info = OPCODES.get(opcode)\n")
            f.write("    return info.stack_effect if info else None\n")

    def generate_csharp_implementation(self) -> None:




        """Generate C# opcode implementation."""
        output_path = Path("reference/implementations/Opcodes.cs")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("// Unified PowerBuilder P-code opcode definitions\n")
            f.write("// Generated from multiple reference implementations\n\n")

            f.write("using System\n")
            f.write("using System.Collections.Generic;\n\n")

            f.write("namespace SimeFinch.Decompiler\n{\n")

            # Generate opcode enum
            f.write("    public enum Opcode : ushort\n    {\n")

            for opcode_hex, info in self.reference["opcodes"].items():
                opcode = int(opcode_hex, 16)
                name = info["name"].replace("-", "_")
                f.write(f"        {name} = 0x{opcode:02X},\n")

            f.write("    }\n\n")

            # Generate opcode info class
            f.write("    public class OpcodeInfo\n    {\n")
            f.write("        public ushort Opcode { get; set; }\n")
            f.write("        public string Name { get; set; }\n")
            f.write("        public byte Length { get; set; }\n")
            f.write("        public string Category { get; set; }\n")
            f.write("        public string StackEffect { get; set; }\n\n")

            f.write(
                "        private static readonly Dictionary<ushort, OpcodeInfo> _opcodes = new()\n",
            )
            f.write("        {\n")

            for opcode_hex, info in self.reference["opcodes"].items():
                opcode = int(opcode_hex, 16)
                name = info["name"]
                length = info["length"]
                category = info.get("category", "unknown")
                stack = info.get("stack_effect", "")

                f.write(f"            {{ 0x{opcode:02X}, new OpcodeInfo {{ ")
                f.write(f'Opcode = 0x{opcode:02X}, Name = "{name}", ')
                f.write(f'Length = {length}, Category = "{category}", ')
                f.write(f'StackEffect = "{stack}" }} }},\n')

            f.write("        };\n\n")

            f.write("        public static OpcodeInfo Get(ushort opcode) => ")
            f.write("_opcodes.TryGetValue(opcode, out var info) ? info : null;\n")
            f.write("    }\n")
            f.write("}\n")

    def generate_test_framework(self) -> None:




        """Generate test framework for opcode verification."""
        output_path = Path("tests/opcode_verification/test_opcodes.py")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write('"""\n')
            f.write("Test framework for verifying opcode implementations.\n")
            f.write('"""\n\n')

            f.write("import pytest\n")
            f.write("from pathlib import Path\n")
            f.write(
                "from decompile.opcodes_unified import OPCODES, get_opcode_name, get_opcode_length\n\n",
            )

            f.write("class TestOpcodes:\n")
            f.write('    """Test opcode definitions."""\n\n')

            f.write("    def test_all_opcodes_have_names(self):\n")
            f.write('        """Verify all opcodes have meaningful names."""\n')
            f.write("        for opcode, info in OPCODES.items():\n")
            f.write('            assert info.name != f"UNKNOWN_{opcode:02X}"\n')
            f.write("            assert len(info.name) > 0\n\n")

            f.write("    def test_opcode_lengths_positive(self):\n")
            f.write('        """Verify all opcodes have positive lengths."""\n')
            f.write("        for opcode, info in OPCODES.items():\n")
            f.write("            assert info.length > 0\n")
            f.write("            assert info.length <= 10  # Reasonable max\n\n")

            f.write("    def test_type_variants_exist(self):\n")
            f.write(
                '        """Verify type-specific variants exist for common operations."""\n',
            )
            f.write("        # Operations that should have type variants\n")
            f.write(
                '        expected_variants = ["ADD", "SUB", "MUL", "DIV", "ASSIGN", "PUSH"]\n',
            )
            f.write("        \n")
            f.write("        for base_op in expected_variants:\n")
            f.write(
                "            variants = [name for name in [info.name for info in OPCODES.values()] \n",
            )
            f.write('                       if name.startswith(base_op + "_")]\n')
            f.write(
                '            assert len(variants) > 1, f"{base_op} should have type variants"\n\n',
            )

            f.write('    @pytest.mark.parametrize("opcode,expected_name", [\n')

            # Add some known opcodes for verification
            known_opcodes = [
                (0x00, "RETURN"),
                (0x01, "STORE_RETURN_VAL"),
                (0x04, "JUMP"),
            ]

            for opcode, _name in known_opcodes:
                if f"0x{opcode:02X}" in self.reference["opcodes"]:
                    actual_name = self.reference["opcodes"][f"0x{opcode:02X}"]["name"]
                    f.write(f'        (0x{opcode:02X}, "{actual_name}"),\n')

            f.write("    ])\n")
            f.write("    def test_known_opcodes(self, opcode, expected_name):\n")
            f.write('        """Test specific known opcodes."""\n')
            f.write("        assert get_opcode_name(opcode) == expected_name\n")

    def generate_comparison_report(self) -> None:




        """Generate a report comparing implementations."""
        output_path = Path("docs/implementation_comparison.md")

        with open(output_path, "w") as f:
            f.write("# PowerBuilder Decompiler Implementation Comparison\n\n")

            f.write("## Overview\n\n")
            f.write(
                "This document compares opcode implementations across different decompilers.\n\n",
            )

            # Count opcodes by source
            source_counts = defaultdict(int)
            both_sources = 0

            for info in self.reference["opcodes"].values():
                impls = info.get("implementations", {})
                if "pbdviewer" in impls and "powerbuilder-decompile" in impls:
                    both_sources += 1
                elif "pbdviewer" in impls:
                    source_counts["pbdviewer"] += 1
                elif "powerbuilder-decompile" in impls:
                    source_counts["powerbuilder-decompile"] += 1

            f.write("## Implementation Coverage\n\n")
            f.write(f"- Opcodes in both implementations: {both_sources}\n")
            f.write(f"- Opcodes only in pbdviewer: {source_counts['pbdviewer']}\n")
            f.write(
                f"- Opcodes only in powerbuilder-decompile: {source_counts['powerbuilder-decompile']}\n",
            )
            f.write(f"- Total unique opcodes: {len(self.reference['opcodes'])}\n\n")

            f.write("## Confidence Levels\n\n")
            confidence_counts = defaultdict(int)
            for info in self.reference["opcodes"].values():
                confidence = info.get("confidence", "unknown")
                confidence_counts[confidence] += 1

            for level, count in sorted(confidence_counts.items()):
                percentage = (count / len(self.reference["opcodes"])) * 100
                f.write(f"- {level}: {count} opcodes ({percentage:.1f}%)\n")

            f.write("\n## Implementation Differences\n\n")
            f.write("| Opcode | pbdviewer | powerbuilder-decompile | Notes |\n")
            f.write("|--------|-----------|------------------------|-------|\n")

            differences = []
            for opcode_hex, info in self.reference["opcodes"].items():
                impls = info.get("implementations", {})
                if len(impls) > 1:
                    pb_handler = impls.get("pbdviewer", {}).get("handler", "-")
                    py_func = impls.get("powerbuilder-decompile", {}).get(
                        "function",
                        "-",
                    )

                    if pb_handler != "-" and py_func != "-":
                        differences.append(
                            {
                                "opcode": opcode_hex,
                                "pb": pb_handler,
                                "py": py_func,
                                "name": info["name"],
                            },
                        )

            for diff in differences[:20]:  # Show first 20
                f.write(
                    f"| {diff['opcode']} | {diff['pb']} | {diff['py']} | {diff['name']} |\n",
                )

            if len(differences) > 20:
                f.write(f"\n*... and {len(differences) - 20} more differences*\n")


def main() -> None:





    generator = OpcodeReferenceGenerator()

    # Generate implementations
    generator.generate_python_implementation()
    generator.generate_csharp_implementation()
    generator.generate_test_framework()
    generator.generate_comparison_report()


if __name__ == "__main__":
    main()
