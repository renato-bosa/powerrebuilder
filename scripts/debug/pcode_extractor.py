#!/usr/bin/env python3
"""Comprehensive P-code extraction and debugging tool.

This tool consolidates P-code extraction functionality from multiple scripts:
- test_real_pcode.py (Library API extraction)
- test_real_pcode_simple.py (Simplified extraction)
- debug_pcode_extraction.py (Debug .fun file creation)
- debug_pcode_final.py (Uses actual extraction functions)
- test_fun_file_creation.py (Verify .fun creation)

Usage:
    python pcode_extractor.py extract <pbd_file> [--output-dir <dir>]
    python pcode_extractor.py verify <pbd_file>
    python pcode_extractor.py debug <pbd_file> <entry_name>
    python pcode_extractor.py list <pbd_file> [--pcode-only]
"""

import argparse
import hashlib
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from extract.pbd.structures.header import extract_pbl_header as read_pbd_header
from extract.pbd.structures.entry import PbEntryDefinition
from extract.pbd.extraction.library import Library
from extract.pbd.structures.node import NodeType, PbNode
from extract.pbd.structures.pbd_object import PbObject
from extract.pbd.utils.text_extraction import extract_text_segments
from extract.pbd.io.file_operations import extract_file_content


class PCodeExtractor:
    """Unified P-code extraction tool."""
    
    def __init__(self, pbd_path: Path, output_dir: Optional[Path] = None):
        """Initialize extractor.
        
        Args:
            pbd_path: Path to PBD file
            output_dir: Output directory for extracted files
        """
        self.pbd_path = pbd_path
        self.output_dir = output_dir or pbd_path.parent / f"{pbd_path.stem}_extracted"
        self.library: Optional[Library] = None
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract all P-code from PBD file.
        
        Returns:
            Dictionary with extraction results
        """
        results = {
            "total_entries": 0,
            "pcode_entries": 0,
            "extracted_files": [],
            "errors": []
        }
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize library
            self.library = Library(self.pbd_path)
            self.library.parse()
            
            results["total_entries"] = len(self.library.entries)
            
            # Extract P-code from each entry
            for entry_name, entry in self.library.entries.items():
                if self._has_pcode(entry):
                    results["pcode_entries"] += 1
                    
                    # Extract P-code
                    pcode_data = self._extract_pcode(entry)
                    if pcode_data:
                        # Save .fun file
                        fun_path = self.output_dir / f"{entry_name}.fun"
                        fun_path.write_bytes(pcode_data)
                        results["extracted_files"].append(str(fun_path))
                        
                        # Also save human-readable version
                        txt_path = self.output_dir / f"{entry_name}.pcode"
                        self._save_readable_pcode(txt_path, pcode_data)
                        
        except Exception as e:
            results["errors"].append(f"Library error: {str(e)}")
            
        return results
        
    def verify_pcode(self) -> Dict[str, Any]:
        """Verify P-code detection without extraction.
        
        Returns:
            Dictionary with verification results
        """
        results = {
            "total_entries": 0,
            "pcode_entries": [],
            "non_pcode_entries": [],
            "statistics": {}
        }
        
        try:
            # Initialize library
            self.library = Library(self.pbd_path)
            self.library.parse()
            
            results["total_entries"] = len(self.library.entries)
            
            # Check each entry
            for entry_name, entry in self.library.entries.items():
                if self._has_pcode(entry):
                    results["pcode_entries"].append(entry_name)
                else:
                    results["non_pcode_entries"].append(entry_name)
                    
            # Calculate statistics
            results["statistics"] = {
                "pcode_percentage": len(results["pcode_entries"]) / results["total_entries"] * 100
                if results["total_entries"] > 0 else 0,
                "avg_pcode_size": self._calculate_avg_pcode_size(results["pcode_entries"])
            }
            
        except Exception as e:
            results["error"] = str(e)
            
        return results
        
    def debug_entry(self, entry_name: str) -> Dict[str, Any]:
        """Debug P-code extraction for a specific entry.
        
        Args:
            entry_name: Name of entry to debug
            
        Returns:
            Dictionary with debug information
        """
        results = {
            "entry_name": entry_name,
            "found": False,
            "has_pcode": False,
            "pcode_info": {},
            "extraction_details": {}
        }
        
        try:
            # Initialize library
            self.library = Library(self.pbd_path)
            self.library.parse()
            
            if entry_name in self.library.entries:
                results["found"] = True
                entry = self.library.entries[entry_name]
                
                # Check for P-code
                results["has_pcode"] = self._has_pcode(entry)
                
                if results["has_pcode"]:
                    # Get detailed P-code info
                    obj = self._get_object(entry)
                    if obj and hasattr(obj, "function_block_node"):
                        node = obj.function_block_node
                        results["pcode_info"] = {
                            "offset": node.offset,
                            "length": node.length,
                            "flags": node.flags,
                            "hash": self._calculate_hash(node)
                        }
                        
                        # Try extraction
                        pcode_data = self._extract_pcode(entry)
                        if pcode_data:
                            results["extraction_details"] = {
                                "size": len(pcode_data),
                                "first_bytes": pcode_data[:16].hex(),
                                "last_bytes": pcode_data[-16:].hex()
                            }
                            
        except Exception as e:
            results["error"] = str(e)
            
        return results
        
    def list_entries(self, pcode_only: bool = False) -> List[Dict[str, Any]]:
        """List all entries in PBD file.
        
        Args:
            pcode_only: Only list entries with P-code
            
        Returns:
            List of entry information
        """
        entries = []
        
        try:
            # Initialize library
            self.library = Library(self.pbd_path)
            self.library.parse()
            
            for entry_name, entry in self.library.entries.items():
                has_pcode = self._has_pcode(entry)
                
                if not pcode_only or has_pcode:
                    entry_info = {
                        "name": entry_name,
                        "type": entry.type.name if hasattr(entry.type, "name") else str(entry.type),
                        "has_pcode": has_pcode
                    }
                    
                    # Add P-code details if available
                    if has_pcode:
                        obj = self._get_object(entry)
                        if obj and hasattr(obj, "function_block_node"):
                            node = obj.function_block_node
                            entry_info["pcode_size"] = node.length
                            
                    entries.append(entry_info)
                    
        except Exception as e:
            print(f"Error listing entries: {e}")
            
        return entries
        
    def _has_pcode(self, entry: PbEntryDefinition) -> bool:
        """Check if entry has P-code.
        
        Args:
            entry: Entry to check
            
        Returns:
            True if entry has P-code
        """
        obj = self._get_object(entry)
        if obj:
            # Check for function_block_node (indicates P-code)
            if hasattr(obj, "function_block_node") and obj.function_block_node:
                return True
                
            # Check nodes for FUNCTION_BLOCK type
            if hasattr(obj, "nodes"):
                for node in obj.nodes:
                    if node.type == NodeType.FUNCTION_BLOCK:
                        return True
                        
        return False
        
    def _get_object(self, entry: PbEntryDefinition) -> Optional[PbObject]:
        """Get PbObject from entry.
        
        Args:
            entry: Entry to get object from
            
        Returns:
            PbObject or None
        """
        if hasattr(entry, "_object"):
            return entry._object
            
        # Try to parse object
        try:
            content = extract_file_content(
                self.pbd_path,
                entry.data_offset,
                entry.object_key
            )
            if content:
                obj = PbObject()
                obj.parse(content)
                entry._object = obj
                return obj
        except Exception:
            pass
            
        return None
        
    def _extract_pcode(self, entry: PbEntryDefinition) -> Optional[bytes]:
        """Extract P-code data from entry.
        
        Args:
            entry: Entry to extract from
            
        Returns:
            P-code bytes or None
        """
        obj = self._get_object(entry)
        if not obj:
            return None
            
        # Get function block node
        node = None
        if hasattr(obj, "function_block_node"):
            node = obj.function_block_node
        elif hasattr(obj, "nodes"):
            for n in obj.nodes:
                if n.type == NodeType.FUNCTION_BLOCK:
                    node = n
                    break
                    
        if not node:
            return None
            
        # Extract P-code data
        try:
            with open(self.pbd_path, "rb") as f:
                f.seek(node.offset)
                return f.read(node.length)
        except Exception:
            return None
            
    def _save_readable_pcode(self, path: Path, pcode_data: bytes) -> None:
        """Save P-code in human-readable format.
        
        Args:
            path: Output path
            pcode_data: P-code bytes
        """
        lines = []
        offset = 0
        
        while offset < len(pcode_data):
            # Read opcode
            if offset >= len(pcode_data):
                break
                
            opcode = pcode_data[offset]
            line = f"{offset:04X}: {opcode:02X}"
            
            # Add some bytes after opcode (simplified)
            bytes_to_show = min(8, len(pcode_data) - offset)
            hex_bytes = " ".join(f"{b:02X}" for b in pcode_data[offset:offset + bytes_to_show])
            line += f" {hex_bytes}"
            
            lines.append(line)
            offset += 1
            
        path.write_text("\n".join(lines))
        
    def _calculate_hash(self, node: PbNode) -> str:
        """Calculate hash of node data.
        
        Args:
            node: Node to hash
            
        Returns:
            Hash string
        """
        try:
            with open(self.pbd_path, "rb") as f:
                f.seek(node.offset)
                data = f.read(node.length)
                return hashlib.md5(data).hexdigest()
        except Exception:
            return "error"
            
    def _calculate_avg_pcode_size(self, pcode_entries: List[str]) -> float:
        """Calculate average P-code size.
        
        Args:
            pcode_entries: List of entry names with P-code
            
        Returns:
            Average size in bytes
        """
        if not pcode_entries or not self.library:
            return 0
            
        total_size = 0
        count = 0
        
        for entry_name in pcode_entries:
            if entry_name in self.library.entries:
                entry = self.library.entries[entry_name]
                obj = self._get_object(entry)
                
                if obj and hasattr(obj, "function_block_node"):
                    node = obj.function_block_node
                    total_size += node.length
                    count += 1
                    
        return total_size / count if count > 0 else 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive P-code extraction and debugging tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract all P-code")
    extract_parser.add_argument("pbd_file", type=Path, help="PBD file to extract from")
    extract_parser.add_argument("--output-dir", type=Path, help="Output directory")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify P-code detection")
    verify_parser.add_argument("pbd_file", type=Path, help="PBD file to verify")
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug specific entry")
    debug_parser.add_argument("pbd_file", type=Path, help="PBD file")
    debug_parser.add_argument("entry_name", help="Entry name to debug")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List entries")
    list_parser.add_argument("pbd_file", type=Path, help="PBD file")
    list_parser.add_argument("--pcode-only", action="store_true", help="Only show P-code entries")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Verify PBD file exists
    if not args.pbd_file.exists():
        print(f"Error: PBD file not found: {args.pbd_file}")
        return
        
    # Create extractor
    output_dir = getattr(args, "output_dir", None)
    extractor = PCodeExtractor(args.pbd_file, output_dir)
    
    # Execute command
    if args.command == "extract":
        print(f"Extracting P-code from: {args.pbd_file}")
        results = extractor.extract_all()
        
        print(f"\nExtraction Results:")
        print(f"  Total entries: {results['total_entries']}")
        print(f"  P-code entries: {results['pcode_entries']}")
        print(f"  Files created: {len(results['extracted_files'])}")
        
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
                
    elif args.command == "verify":
        print(f"Verifying P-code in: {args.pbd_file}")
        results = extractor.verify_pcode()
        
        print(f"\nVerification Results:")
        print(f"  Total entries: {results['total_entries']}")
        print(f"  P-code entries: {len(results['pcode_entries'])}")
        print(f"  Non-P-code entries: {len(results['non_pcode_entries'])}")
        print(f"  P-code percentage: {results['statistics']['pcode_percentage']:.1f}%")
        print(f"  Average P-code size: {results['statistics']['avg_pcode_size']:.0f} bytes")
        
        if "error" in results:
            print(f"\nError: {results['error']}")
            
    elif args.command == "debug":
        print(f"Debugging entry '{args.entry_name}' in: {args.pbd_file}")
        results = extractor.debug_entry(args.entry_name)
        
        print(f"\nDebug Results:")
        print(f"  Entry found: {results['found']}")
        print(f"  Has P-code: {results['has_pcode']}")
        
        if results['pcode_info']:
            print(f"\nP-code Information:")
            for key, value in results['pcode_info'].items():
                print(f"    {key}: {value}")
                
        if results['extraction_details']:
            print(f"\nExtraction Details:")
            for key, value in results['extraction_details'].items():
                print(f"    {key}: {value}")
                
        if "error" in results:
            print(f"\nError: {results['error']}")
            
    elif args.command == "list":
        print(f"Listing entries in: {args.pbd_file}")
        entries = extractor.list_entries(args.pcode_only)
        
        print(f"\nFound {len(entries)} entries:")
        for entry in sorted(entries, key=lambda x: x['name']):
            pcode_info = f" ({entry.get('pcode_size', 0)} bytes)" if entry['has_pcode'] else ""
            print(f"  {entry['name']}: {entry['type']}{pcode_info}")


if __name__ == "__main__":
    main()