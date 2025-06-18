
from typing import Any, Dict, List, Optional, Union
# extract/pbd_core/crossref.py
"""Utilities for finding and reporting cross-references between PBD objects."""

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path

# Assuming PbdObject will be imported for type hinting if needed, but find_cross_references takes its content directly.
# from .pbd_object import PbdObject # Causes circular if PbdObject might use this, keep for hinting if safe

logger = logging.getLogger(__name__)


@dataclass
class CrossReference:
    caller_object_name: str
    # caller_script_type: Optional[str] = None # e.g., event name, function name if identifiable
    callee_name_raw: str  # The raw string identified as a potential callee
    callee_object_type: str | None = None  # e.g., NVO, Window, Function, DataWindow
    callee_object_name: str | None = None  # Resolved object name
    callee_member_name: str | None = None  # Resolved function/event/variable name
    call_type: str  # e.g., CREATE, EVENT, FUNCTION, VARIABLE_ACCESS
    line_number: int | None = None  # Placeholder for future line number tracking
    raw_line_content: str | None = None  # Placeholder for the line where found


# Basic Regexes (these are very simplified and will need significant refinement)
# They primarily look for keywords and identifiers. Case-insensitivity is important.
# Group 1 is usually the key callee identifier.
REGEX_PATTERNS = {
    "CREATE": re.compile(
        r"\\bCREATE\\s+(?:USING\\s+)?([a-zA-Z0-9_.-]+)\\b", re.IGNORECASE
    ),
    "FUNCTION_CALL_STATIC": re.compile(
        r"\\b([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)\\s*\\(", re.IGNORECASE
    ),
    "FUNCTION_CALL_DYNAMIC_METHOD": re.compile(
        r"([a-zA-Z0-9_.]+)\\.([a-zA-Z0-9_]+)\\s*\\(", re.IGNORECASE
    ),
    "EVENT_TRIGGER": re.compile(
        r"\\.(?:EVENT\\s+)?(?:TriggerEvent|PostEvent)\\s*\\(\\s*['\"]([a-zA-Z0-9_]+)['\"]",
        re.IGNORECASE,
    ),
    # DataWindow related
    "DW_SETTRANSOBJECT": re.compile(
        r"\\.(?:SetTransObject|SetTransaction)\\s*\\(\\s*([a-zA-Z0-9_]+)\\s*\\)",
        re.IGNORECASE,
    ),
    "DW_GETCHILD": re.compile(
        r"\\.GetChild\\s*\\(\\s*['\"]([a-zA-Z0-9_]+)['\"]", re.IGNORECASE
    ),
}


def _extract_reference_info(call_type: str, match: re.Match) -> tuple[str, str | None, str | None]:
    """Extract reference information based on call type."""
    callee_name_raw = ""
    callee_obj = None
    callee_mem = None

    if call_type == "CREATE":
        callee_name_raw = match.group(1)
        callee_obj = callee_name_raw  # Object being created is the callee object
    elif call_type == "FUNCTION_CALL_STATIC":
        callee_obj = match.group(1)  # Class/Object name
        callee_mem = match.group(2)  # Function name
        callee_name_raw = f"{callee_obj}::{callee_mem}"
    elif call_type == "FUNCTION_CALL_DYNAMIC_METHOD":
        callee_obj = match.group(1)  # Variable or class name
        callee_mem = match.group(2)  # Method name
        callee_name_raw = f"{callee_obj}.{callee_mem}"
    elif call_type == "EVENT_TRIGGER":
        callee_mem = match.group(1)
        callee_name_raw = callee_mem
    elif call_type in {"DW_SETTRANSOBJECT", "DW_GETCHILD"}:
        callee_name_raw = match.group(1)
        callee_obj = callee_name_raw
    
    return callee_name_raw, callee_obj, callee_mem

def _process_line_for_references(
    object_name: str, line: str, line_num: int
) -> list[CrossReference]:
    """Process a single line for cross-references."""
    references = []
    
    for call_type, pattern in REGEX_PATTERNS.items():
        for match in pattern.finditer(line):
            callee_name_raw, callee_obj, callee_mem = _extract_reference_info(call_type, match)
            
            if callee_name_raw:
                references.append(
                    CrossReference(
                        caller_object_name=object_name,
                        callee_name_raw=callee_name_raw.strip(),
                        callee_object_name=callee_obj.strip() if callee_obj else None,
                        callee_member_name=callee_mem.strip() if callee_mem else None,
                        call_type=call_type,
                        line_number=line_num + 1,  # 1-indexed
                        raw_line_content=line.strip(),
                    )
                )
    
    return references

def find_cross_references(
    object_name: str, text_content: str | None
) -> list[CrossReference]:
    """Finds potential cross-references in the given text content of a PBD object.
    Uses a basic set of regular expressions.

    Args:
        object_name: The name of the PBD object whose content is being scanned (the caller).
        text_content: The raw text content (source code/p-code) of the PBD object.

    Returns:
        A list of CrossReference objects found.
    """
    if not text_content:
        return []

    references = []
    lines = text_content.splitlines()

    for line_num, line in enumerate(lines):
        references.extend(_process_line_for_references(object_name, line, line_num))
    
    return references


def write_crossref_csv(references: list[CrossReference], output_path: Path) -> None:
    """Writes a list of CrossReference objects to a CSV file."""
    if not references:
        logger.info("No cross-references found to write.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = [
        "CallerObject",
        "CallType",
        "CalleeRaw",
        "CalleeObject",
        "CalleeMember",
        "LineNumber",
        "RawLineContent",
    ]

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for ref in references:
                writer.writerow(
                    [
                        ref.caller_object_name,
                        ref.call_type,
                        ref.callee_name_raw,
                        ref.callee_object_name,
                        ref.callee_member_name,
                        ref.line_number,
                        ref.raw_line_content,
                    ]
                )
        logger.info("Cross-reference CSV written to %s", output_path)
    except OSError as e:
        logger.exception("Failed to write cross-reference CSV to %s: %s", output_path, e)


if __name__ == "__main__":
    # Example Usage (for testing this module directly)
    logging.basicConfig(level=logging.DEBUG)
    example_content = """
    // Create an NVO
    n_my_nvo inv_my_nvo
    inv_my_nvo = CREATE n_cst_myarray
    inv_my_nvo = CREATE my.object.name

    // Call a static function
    dw_1.SetItem(row, "column_name", n_another_class::uf_calculate_value(param1))

    // Call an instance method
    inv_my_nvo.uf_process_data("some_arg")
    my.obj.reference.do_something()

    // Trigger an event
    this.TriggerEvent("ue_custom_event")
    parent.PostEvent("ue_another")

    // DataWindow specific
    dw_1.SetTransObject(SQLCA)
    dw_1.GetChild("dw_child_name", lnv_child_dw_ref)
    dw_1.Object.DataWindow.Zoom = 100 // Not captured by simple regexes here
    """

    found_refs = find_cross_references("w_example_window", example_content)
    for _r in found_refs:
        pass

    if found_refs:
        write_crossref_csv(found_refs, Path("./temp_crossref_output.csv"))
