#!/usr/bin/env python3
"""Compare v10/v11 semantic reports for the typed-numeric constant gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


TYPED_NUMERIC_OPCODES = {0x0036, 0x0038}


def load_compact(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as report_file:
        report = json.load(report_file)

    functions = {}
    unresolved = {}
    for entry in report["entries"]:
        for region in entry.get("pcode_regions", []):
            preview = region.get("semantic_preview")
            if not preview:
                continue
            function_key = f"{entry['index']}|{region['region_index']}"
            evidence = preview["evidence"]
            comparison = evidence.get("function_comparison") or {}
            functions[function_key] = {
                "object": entry["name"],
                "owner": region["owner"],
                "signature": preview["signature"],
                "complete": preview["semantically_complete"],
                "verification": evidence["function_reconstruction"],
                "verification_basis": comparison.get("verification_basis"),
                "typed_numeric_counts": {
                    "PUSH_CONST_DEC": sum(
                        instruction["opcode"] == 0x0036
                        for instruction in region["scan"]["instructions"]
                    ),
                    "PUSH_CONST_DOUBLE": sum(
                        instruction["opcode"] == 0x0038
                        for instruction in region["scan"]["instructions"]
                    ),
                },
            }
            for item in preview["unresolved"]:
                unresolved_key = (
                    f"{function_key}|{item['offset']}|{item['opcode']}"
                )
                unresolved[unresolved_key] = {
                    "function_key": function_key,
                    "opcode": item["opcode"],
                    "mnemonic": item["mnemonic"],
                    "reason": item["reason"],
                }

    return {
        "summary": report["summary"],
        "functions": functions,
        "unresolved": unresolved,
    }


def function_rows(keys: list[str], functions: dict) -> list[dict]:
    return [functions[key] for key in sorted(keys)]


def compare(label: str, old_path: Path, new_path: Path) -> dict:
    old = load_compact(old_path)
    new = load_compact(new_path)
    old_unresolved = old["unresolved"]
    new_unresolved = new["unresolved"]
    gone = {
        key: value
        for key, value in old_unresolved.items()
        if key not in new_unresolved
    }
    added = {
        key: value
        for key, value in new_unresolved.items()
        if key not in old_unresolved
    }
    direct = {
        key: value
        for key, value in gone.items()
        if value["opcode"] in TYPED_NUMERIC_OPCODES
    }
    cascade = {
        key: value
        for key, value in gone.items()
        if value["opcode"] not in TYPED_NUMERIC_OPCODES
    }
    cascade_reasons = Counter(
        (value["mnemonic"], value["reason"]) for value in cascade.values()
    )
    direct_mnemonics = Counter(value["mnemonic"] for value in direct.values())

    old_functions = old["functions"]
    new_functions = new["functions"]
    complete_promotions = [
        key
        for key, function in new_functions.items()
        if function["complete"] and not old_functions[key]["complete"]
    ]
    complete_regressions = [
        key
        for key, function in old_functions.items()
        if function["complete"] and not new_functions[key]["complete"]
    ]
    verified_promotions = [
        key
        for key, function in new_functions.items()
        if function["verification"] == "verified"
        and old_functions[key]["verification"] != "verified"
    ]
    verified_regressions = [
        key
        for key, function in old_functions.items()
        if function["verification"] == "verified"
        and new_functions[key]["verification"] != "verified"
    ]
    remaining_typed = [
        value
        for value in new_unresolved.values()
        if value["opcode"] in TYPED_NUMERIC_OPCODES
    ]

    return {
        "corpus": label,
        "old_unresolved": len(old_unresolved),
        "new_unresolved": len(new_unresolved),
        "direct_typed_numeric_resolved": len(direct),
        "direct_typed_numeric_functions": len(
            {value["function_key"] for value in direct.values()}
        ),
        "direct_typed_numeric_by_mnemonic": dict(sorted(direct_mnemonics.items())),
        "cascade_failures_resolved": len(cascade),
        "cascade_functions": len(
            {value["function_key"] for value in cascade.values()}
        ),
        "new_failures": len(added),
        "remaining_typed_numeric_unresolved": len(remaining_typed),
        "cascade_reasons": [
            {"count": count, "mnemonic": mnemonic, "reason": reason}
            for (mnemonic, reason), count in cascade_reasons.most_common()
        ],
        "old_complete": sum(f["complete"] for f in old_functions.values()),
        "new_complete": sum(f["complete"] for f in new_functions.values()),
        "complete_promotions": function_rows(complete_promotions, new_functions),
        "complete_regressions": function_rows(complete_regressions, old_functions),
        "old_verified": sum(
            f["verification"] == "verified" for f in old_functions.values()
        ),
        "new_verified": sum(
            f["verification"] == "verified" for f in new_functions.values()
        ),
        "verified_promotions": function_rows(verified_promotions, new_functions),
        "verified_regressions": function_rows(verified_regressions, old_functions),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "pb2022-analysis",
    )
    args = parser.parse_args()
    root = args.analysis_root
    pairs = [
        ("exmmain", "whole-function-v10-exmmain", "whole-function-v11-exmmain"),
        ("appexmfe", "whole-function-v10-appexmfe", "whole-function-v11-appexmfe"),
        ("pfcapsrv", "whole-function-v10-pfcapsrv", "whole-function-v11-pfcapsrv"),
        ("replicacao", "replicacao-snapshot-v10", "replicacao-snapshot-v11"),
    ]
    result = [
        compare(
            label,
            root / old_dir / "decode-report.json",
            root / new_dir / "decode-report.json",
        )
        for label, old_dir, new_dir in pairs
    ]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
