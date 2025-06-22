#!/usr/bin/env python3
"""Extract opcodes from all reference implementations and create a comprehensive mapping."""

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml


class OpcodeExtractor:
    def __init__(self) -> None:
        
        self.opcodes = defaultdict(dict)
        self.implementations = {}

    def extract_from_pbdviewer(self) -> None:


        

        """Extract opcodes from C# pbdviewer implementation."""
        # Extract from PCodeParserBase for opcode lengths
        parser_base = Path("reference/pbdviewer/Uitils/PCode/PCodeParserBase.cs")
        if parser_base.exists():
            with open(parser_base) as f:
                content = f.read()

            # Extract opcode handler calls
            handler_pattern = r"case\s+(\d+):\s*\n\s*(\w+)\((.*?)\);"
            matches = re.findall(handler_pattern, content, re.MULTILINE | re.DOTALL)

            for match in matches:
                opcode = int(match[0])
                handler = match[1]
                params = match[2]

                self.opcodes[opcode]["pbdviewer_handler"] = handler
                self.opcodes[opcode]["pbdviewer_params"] = params

        # Extract from length arrays
        for parser_file in Path("reference/pbdviewer/Uitils/PCode").glob(
            "PCodeParser*.cs"
        ):
            with open(parser_file) as f:
                content = f.read()

            # Extract byte array definitions
            array_match = re.search(
                r"byte\[\]\s*.*?=\s*new\s*byte\[\d+\]\s*\{([^}]+)\}", content, re.DOTALL
            )
            if array_match:
                lengths_str = array_match.group(1)
                lengths = [
                    int(x.strip())
                    for x in lengths_str.split(",")
                    if x.strip().isdigit()
                ]

                version = parser_file.stem.replace("PCodeParser", "PB")
                for i, length in enumerate(lengths):
                    if i in self.opcodes:
                        self.opcodes[i][f"{version}_length"] = length

        self.implementations["pbdviewer"] = len(
            [o for o in self.opcodes.values() if "pbdviewer_handler" in o]
        )

    def extract_from_powerbuilder_decompile(self) -> None:


        

        """Extract opcodes from Python powerbuilder-decompile."""
        pcode_file = Path("reference/powerbuilder-decompile/pbd/pcode.py")
        if pcode_file.exists():
            with open(pcode_file) as f:
                content = f.read()

            # Extract g_codes array
            g_codes_match = re.search(r"g_codes\s*=\s*\[([^\]]+)\]", content, re.DOTALL)
            if g_codes_match:
                g_codes_str = g_codes_match.group(1)

                # Parse each entry
                entry_pattern = r"\{[^}]+\}"
                entries = re.findall(entry_pattern, g_codes_str)

                for entry in entries:
                    # Extract fields
                    index_match = re.search(r"'index':\s*0x([0-9a-fA-F]+)", entry)
                    name_match = re.search(r"'name':\s*'([^']+)'", entry)
                    func_match = re.search(r"'func':\s*(\w+)", entry)
                    args_match = re.search(r"'arg_num':\s*(\d+)", entry)

                    if index_match:
                        opcode = int(index_match.group(1), 16)

                        if name_match:
                            self.opcodes[opcode]["pb_decompile_name"] = (
                                name_match.group(1)
                            )
                        if func_match:
                            self.opcodes[opcode]["pb_decompile_func"] = (
                                func_match.group(1)
                            )
                        if args_match:
                            self.opcodes[opcode]["pb_decompile_args"] = int(
                                args_match.group(1)
                            )

            # Extract function implementations for stack effects
            func_pattern = (
                r"def\s+(pb_\w+)\(stack,\s*pcode,\s*routine\):(.*?)(?=\ndef|\Z)"
            )
            func_matches = re.findall(func_pattern, content, re.DOTALL)

            for func_name, func_body in func_matches:
                # Count stack operations
                pops = len(re.findall(r"stack\.pop\(\)", func_body))
                pushes = len(re.findall(r"stack\.append\(", func_body))

                # Find opcodes that use this function
                for opcode, info in self.opcodes.items():
                    if info.get("pb_decompile_func") == func_name:
                        info["stack_pops"] = pops
                        info["stack_pushes"] = pushes

        self.implementations["powerbuilder-decompile"] = len(
            [o for o in self.opcodes.values() if "pb_decompile_name" in o]
        )

    def extract_from_sime_finch(self) -> None:


        

        """Extract our verified opcodes."""
        verified_file = Path("extract/pbd_core/opcodes_verified.yaml")
        if verified_file.exists():
            with open(verified_file) as f:
                data = yaml.safe_load(f)

            if data and "opcodes" in data:
                for opcode_hex, info in data["opcodes"].items():
                    opcode = int(opcode_hex, 16)
                    self.opcodes[opcode]["verified_name"] = info.get("name")
                    self.opcodes[opcode]["verified_length"] = info.get("length")
                    self.opcodes[opcode]["verified_confidence"] = info.get("confidence")
                    self.opcodes[opcode]["verified_source"] = info.get("source", [])

        self.implementations["sime-finch"] = len(
            [o for o in self.opcodes.values() if "verified_name" in o]
        )

    def analyze_patterns(self) -> None:


        

        """Analyze patterns in opcode definitions."""
        # Group by operation type
        operation_types = defaultdict(list)
        for opcode, info in self.opcodes.items():
            name = (
                info.get("pb_decompile_name") or info.get("verified_name") or "UNKNOWN"
            )
            if "_" in name:
                op_type = name.split("_")[0]
                operation_types[op_type].append(opcode)

        # Find type-specific variants
        type_variants = defaultdict(set)
        for opcode, info in self.opcodes.items():
            name = info.get("pb_decompile_name") or info.get("verified_name") or ""
            if name:
                # Extract data type suffix (INT, LONG, DOUBLE, etc.)
                for dtype in [
                    "INT",
                    "UINT",
                    "LONG",
                    "ULONG",
                    "DOUBLE",
                    "DEC",
                    "FLOAT",
                    "STRING",
                    "BOOL",
                    "BINARY",
                    "DATE",
                    "TIME",
                    "CHAR",
                    "ANY",
                ]:
                    if name.endswith("_" + dtype):
                        base_op = name.replace("_" + dtype, "")
                        type_variants[base_op].add(dtype)

        return operation_types, type_variants

    def generate_comprehensive_reference(self) -> None:


        

        """Generate comprehensive opcode reference."""
        operation_types, type_variants = self.analyze_patterns()

        reference = {
            "format_version": "2.0",
            "description": "Comprehensive PowerBuilder P-code opcode reference from multiple sources",
            "sources": {
                "pbdviewer": "https://github.com/hucxy/pbdviewer",
                "powerbuilder-decompile": "https://github.com/sijms/powerbuilder-decompile",
                "sime-finch": "Verified opcodes from reference extraction",
            },
            "statistics": {
                "total_opcodes": len(self.opcodes),
                "implementations": self.implementations,
                "operation_types": len(operation_types),
                "type_variants": len(type_variants),
            },
            "opcodes": {},
        }

        # Build opcode entries
        for opcode in sorted(self.opcodes.keys()):
            info = self.opcodes[opcode]

            # Determine best name
            name = (
                info.get("verified_name")
                or info.get("pb_decompile_name", "").replace("SM_", "")
                or f"OPCODE_{opcode:02X}"
            )

            # Determine length
            length = info.get("verified_length", 1)
            if "PB105_length" in info:
                length = info["PB105_length"]
            elif "PB90_length" in info:
                length = info["PB90_length"]

            # Determine stack effect
            stack_effect = None
            if "stack_pops" in info and "stack_pushes" in info:
                stack_effect = f"{info['stack_pops']} -> {info['stack_pushes']}"

            entry = {
                "name": name,
                "opcode": f"0x{opcode:02X}",
                "length": length,
                "implementations": {},
            }

            # Add implementation details
            if "pbdviewer_handler" in info:
                entry["implementations"]["pbdviewer"] = {
                    "handler": info["pbdviewer_handler"],
                    "params": info.get("pbdviewer_params", ""),
                }

            if "pb_decompile_func" in info:
                entry["implementations"]["powerbuilder-decompile"] = {
                    "function": info["pb_decompile_func"],
                    "arg_count": info.get("pb_decompile_args", 0),
                }

            if stack_effect:
                entry["stack_effect"] = stack_effect

            # Add confidence and notes
            if "verified_confidence" in info:
                entry["confidence"] = info["verified_confidence"]

            # Categorize opcode
            if name != f"OPCODE_{opcode:02X}":
                for op_type, opcodes in operation_types.items():
                    if opcode in opcodes:
                        entry["category"] = op_type.lower()
                        break

            reference["opcodes"][f"0x{opcode:02X}"] = entry

        # Add pattern analysis
        reference["patterns"] = {
            "operation_types": {
                k: [f"0x{o:02X}" for o in v] for k, v in operation_types.items()
            },
            "type_variants": {k: list(v) for k, v in type_variants.items()},
        }

        return reference

    def save_reference(self, reference) -> None:


        

        """Save the comprehensive reference."""
        # Save as YAML
        yaml_path = Path("reference/opcode_reference.yaml")
        with open(yaml_path, "w") as f:
            yaml.dump(reference, f, default_flow_style=False, sort_keys=False)

        # Save as JSON for easier programmatic access
        json_path = Path("reference/opcode_reference.json")
        with open(json_path, "w") as f:
            json.dump(reference, f, indent=2)

        # Generate markdown documentation
        md_path = Path("docs/opcode_reference.md")
        self.generate_markdown_docs(reference, md_path)

    def generate_markdown_docs(self, reference, output_path) -> None:


        

        """Generate markdown documentation from reference."""
        with open(output_path, "w") as f:
            f.write("# PowerBuilder P-code Opcode Reference\n\n")
            f.write(f"Version: {reference['format_version']}\n\n")
            f.write(f"{reference['description']}\n\n")

            f.write("## Sources\n\n")
            for name, url in reference["sources"].items():
                f.write(f"- **{name}**: {url}\n")

            f.write("\n## Statistics\n\n")
            f.write(f"- Total opcodes: {reference['statistics']['total_opcodes']}\n")
            f.write(
                f"- Operation types: {reference['statistics']['operation_types']}\n"
            )
            f.write(f"- Type variants: {reference['statistics']['type_variants']}\n")

            f.write("\n## Opcode Listing\n\n")
            f.write(
                "| Opcode | Name | Length | Category | Stack Effect | Confidence |\n"
            )
            f.write(
                "|--------|------|--------|----------|--------------|------------|\n"
            )

            for opcode_hex, info in reference["opcodes"].items():
                name = info["name"]
                length = info["length"]
                category = info.get("category", "-")
                stack = info.get("stack_effect", "-")
                confidence = info.get("confidence", "-")

                f.write(
                    f"| {opcode_hex} | {name} | {length} | {category} | {stack} | {confidence} |\n"
                )

            f.write("\n## Operation Types\n\n")
            for op_type, opcodes in reference["patterns"]["operation_types"].items():
                if len(opcodes) > 3:  # Only show significant groups
                    f.write(f"### {op_type} ({len(opcodes)} opcodes)\n")
                    f.write(f"{', '.join(opcodes[:10])}")
                    if len(opcodes) > 10:
                        f.write(f" ... and {len(opcodes) - 10} more")
                    f.write("\n\n")


def main() -> None:
    
    


    extractor = OpcodeExtractor()

    # Extract from all sources
    extractor.extract_from_pbdviewer()
    extractor.extract_from_powerbuilder_decompile()
    extractor.extract_from_sime_finch()

    # Generate comprehensive reference
    reference = extractor.generate_comprehensive_reference()

    # Save results
    extractor.save_reference(reference)

    # Print summary
    for _impl, _count in extractor.implementations.items():
        pass


if __name__ == "__main__":
    main()
