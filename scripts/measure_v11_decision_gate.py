#!/usr/bin/env python3
"""Measure the analysis-only PB2022 v11 semantic decision gate."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def direct_family(mnemonic: str) -> str:
    if mnemonic.startswith("DB") or mnemonic in {"ENTER_EMBEDDED", "EXIT_EMBEDDED"}:
        return "sql_and_embedded_sql"
    if mnemonic.startswith("INCR_"):
        return "increment_operations"
    if mnemonic.startswith("DECR_"):
        return "decrement_operations"
    if mnemonic.startswith("ADDASSIGN_"):
        return "addassign_operations"
    if mnemonic.startswith(("SUBASSIGN_", "MULTASSIGN_", "DIVASSIGN_")):
        return "other_compound_assignments"
    if mnemonic.startswith("MOD_"):
        return "modulo_operations"
    if mnemonic == "INT":
        return "int_intrinsic"
    if mnemonic.startswith(("CLASS_CALL", "DOTFUNCCALL")) or mnemonic == "FREE_INV_METH_ARGS":
        return "call_protocol"
    if mnemonic in {"THROW_EXCEPTION", "POP_TRY"}:
        return "exception_handling"
    if mnemonic == "DUP_STACKED_LVALUE":
        return "dup_stacked_lvalue"
    if mnemonic == "ARRAY_BOUND_INFO":
        return "array_bound_info"
    if mnemonic == "CREATE_USING":
        return "create_using"
    if mnemonic in {"DOT_DEC", "DOT_DOUBLE", "DOT_LONGLONG"}:
        return "typed_member_access"
    if mnemonic in {"INDEX_ANY", "INDEX_ERR_CHK_ANY"}:
        return "any_indexing"
    if mnemonic.startswith("TRANSFORM_") or mnemonic == "CALC_COMPLEX_ARRAY_BOUND":
        return "array_shape_transform"
    if mnemonic in {
        "ABS_DEC",
        "ABS_LONG",
        "BLOB",
        "COS",
        "MAX_LONG",
        "MIN_LONG",
        "NEGATE",
        "SIN",
        "SQRT",
        "UPPER",
    }:
        return "intrinsic_or_unary_operations"
    if mnemonic == "PUSH_CONST_FLOAT":
        return "typed_float_constant"
    if mnemonic == "ASSIGN":
        return "generic_assignment"
    if mnemonic.startswith("PB2022_OP_"):
        return "unknown_pb2022_opcode"
    return "other_direct_semantic_gap"


def unresolved_kind(item: dict) -> str:
    reason = item["reason"]
    if reason == "semantic rule not implemented":
        return "direct_rule_absent"
    metadata_markers = (
        "unknown PB 2022 system-function reference",
        "unknown enum constant",
        "member name is external",
        "member name is missing",
        "global function name is missing",
        "local-variable index",
    )
    if any(marker in reason for marker in metadata_markers):
        return "artifact_or_metadata_resolution_gap"
    return "dependent_stack_or_context_failure"


def unresolved_family(item: dict) -> str:
    kind = unresolved_kind(item)
    if kind != "direct_rule_absent":
        return kind
    return direct_family(item["mnemonic"])


def load_functions(path: Path, corpus: str) -> dict[str, dict]:
    with path.open("r", encoding="utf-8-sig") as report_file:
        report = json.load(report_file)
    functions = {}
    for entry in report["entries"]:
        for region in entry.get("pcode_regions", []):
            preview = region.get("semantic_preview")
            if not preview:
                continue
            key = f"{corpus}|{entry['index']}|{region['region_index']}"
            unresolved = sorted(preview["unresolved"], key=lambda item: item["offset"])
            for item in unresolved:
                item["kind"] = unresolved_kind(item)
                item["family"] = unresolved_family(item)
                item["direct"] = item["kind"] == "direct_rule_absent"
            functions[key] = {
                "corpus": corpus,
                "entry": entry["name"],
                "region_index": region["region_index"],
                "signature": preview["signature"],
                "complete": preview["evidence"]["semantic_rules_complete"],
                "verification": preview["evidence"]["function_reconstruction"],
                "unresolved": unresolved,
            }
    return functions


def aggregate_items(functions: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    family_items = defaultdict(list)
    opcode_items = defaultdict(list)
    for key, function in functions.items():
        for item in function["unresolved"]:
            row = {
                **item,
                "function_key": key,
                "corpus": function["corpus"],
                "entry": function["entry"],
                "signature": function["signature"],
            }
            family_items[item["family"]].append(row)
            opcode_items[(item["opcode"], item["mnemonic"], item["reason"])].append(row)

    families = []
    for family, rows in family_items.items():
        families.append(
            {
                "family": family,
                "occurrences": len(rows),
                "functions": len({row["function_key"] for row in rows}),
                "corpora": sorted({row["corpus"] for row in rows}),
            }
        )
    families.sort(key=lambda row: (-row["occurrences"], row["family"]))

    opcodes = []
    for (opcode, mnemonic, reason), rows in opcode_items.items():
        opcodes.append(
            {
                "opcode": opcode,
                "opcode_hex": f"0x{opcode:04X}",
                "mnemonic": mnemonic,
                "reason": reason,
                "family": rows[0]["family"],
                "occurrences": len(rows),
                "functions": len({row["function_key"] for row in rows}),
                "corpora": sorted({row["corpus"] for row in rows}),
            }
        )
    opcodes.sort(key=lambda row: (-row["occurrences"], row["mnemonic"], row["reason"]))
    return families, opcodes


def aggregate_kinds(functions: dict[str, dict]) -> list[dict]:
    rows = []
    for kind in sorted(
        {
            item["kind"]
            for function in functions.values()
            for item in function["unresolved"]
        }
    ):
        affected = {
            key
            for key, function in functions.items()
            if any(item["kind"] == kind for item in function["unresolved"])
        }
        rows.append(
            {
                "kind": kind,
                "occurrences": sum(
                    item["kind"] == kind
                    for function in functions.values()
                    for item in function["unresolved"]
                ),
                "functions": len(affected),
            }
        )
    rows.sort(key=lambda row: -row["occurrences"])
    return rows


def first_blockers(functions: dict[str, dict]) -> dict:
    first_observed = Counter()
    first_direct = Counter()
    first_observed_groups = defaultdict(list)
    first_direct_groups = defaultdict(list)
    dependent_only_groups = defaultdict(list)
    no_direct_profiles = Counter()
    dependent_only = 0
    for function in functions.values():
        if function["complete"]:
            continue
        unresolved = function["unresolved"]
        if unresolved:
            item = unresolved[0]
            first_observed[item["family"]] += 1
            first_observed_groups[
                (item["family"], item["mnemonic"], item["reason"])
            ].append(function)
        direct = [item for item in unresolved if item["direct"]]
        if direct:
            item = direct[0]
            first_direct[item["family"]] += 1
            first_direct_groups[
                (item["family"], item["mnemonic"], item["reason"])
            ].append(function)
        else:
            dependent_only += 1
            no_direct_profiles[
                "+".join(sorted({item["kind"] for item in unresolved}))
                if unresolved
                else "no_unresolved_items"
            ] += 1
            if unresolved:
                item = unresolved[0]
                dependent_only_groups[
                    (item["family"], item["mnemonic"], item["reason"])
                ].append(function)

    def serialize_groups(groups: dict) -> list[dict]:
        rows = []
        for (family, mnemonic, reason), affected in groups.items():
            rows.append(
                {
                    "family": family,
                    "mnemonic": mnemonic,
                    "reason": reason,
                    "functions": len(affected),
                    "examples": [
                        {
                            "corpus": function["corpus"],
                            "entry": function["entry"],
                            "signature": function["signature"],
                        }
                        for function in affected[:3]
                    ],
                }
            )
        rows.sort(key=lambda row: (-row["functions"], row["mnemonic"], row["reason"]))
        return rows

    return {
        "first_observed": dict(first_observed.most_common()),
        "first_observed_groups": serialize_groups(first_observed_groups),
        "first_direct": dict(first_direct.most_common()),
        "first_direct_groups": serialize_groups(first_direct_groups),
        "dependent_only_functions": dependent_only,
        "no_direct_kind_profiles": dict(no_direct_profiles.most_common()),
        "dependent_only_first_groups": serialize_groups(dependent_only_groups),
    }


def family_gate_metrics(functions: dict[str, dict]) -> list[dict]:
    direct_families = sorted(
        {
            item["family"]
            for function in functions.values()
            for item in function["unresolved"]
            if item["direct"]
        }
    )
    rows = []
    for family in direct_families:
        affected = {
            key: function
            for key, function in functions.items()
            if any(item["direct"] and item["family"] == family for item in function["unresolved"])
        }
        occurrence_count = sum(
            item["direct"] and item["family"] == family
            for function in affected.values()
            for item in function["unresolved"]
        )
        dependent_cooccurrences = sum(
            item["kind"] == "dependent_stack_or_context_failure"
            for function in affected.values()
            for item in function["unresolved"]
        )
        metadata_cooccurrences = sum(
            item["kind"] == "artifact_or_metadata_resolution_gap"
            for function in affected.values()
            for item in function["unresolved"]
        )
        sole_direct = 0
        first_direct = 0
        dependent_in_sole_direct = 0
        metadata_in_sole_direct = 0
        for function in affected.values():
            direct = [item for item in function["unresolved"] if item["direct"]]
            if {item["family"] for item in direct} == {family}:
                sole_direct += 1
                dependent_in_sole_direct += sum(
                    item["kind"] == "dependent_stack_or_context_failure"
                    for item in function["unresolved"]
                )
                metadata_in_sole_direct += sum(
                    item["kind"] == "artifact_or_metadata_resolution_gap"
                    for item in function["unresolved"]
                )
            if direct and direct[0]["family"] == family:
                first_direct += 1
        rows.append(
            {
                "family": family,
                "occurrences": occurrence_count,
                "functions": len(affected),
                "first_direct_blocker_functions": first_direct,
                "sole_direct_family_functions": sole_direct,
                "dependent_stack_failures_in_affected_functions": dependent_cooccurrences,
                "dependent_stack_failures_in_sole_direct_functions": dependent_in_sole_direct,
                "metadata_gaps_in_affected_functions": metadata_cooccurrences,
                "metadata_gaps_in_sole_direct_functions": metadata_in_sole_direct,
            }
        )
    rows.sort(key=lambda row: (-row["occurrences"], row["family"]))
    return rows


def target_family_known_overlap(
    target_functions: dict[str, dict], known_functions: dict[str, dict]
) -> list[dict]:
    target_pairs = defaultdict(set)
    for function in target_functions.values():
        for item in function["unresolved"]:
            if item["direct"]:
                target_pairs[item["family"]].add((item["opcode"], item["mnemonic"]))
    rows = []
    for family, pairs in target_pairs.items():
        matching_items = []
        for key, function in known_functions.items():
            for item in function["unresolved"]:
                if item["direct"] and (item["opcode"], item["mnemonic"]) in pairs:
                    matching_items.append((key, function["corpus"], item))
        rows.append(
            {
                "family": family,
                "target_opcode_mnemonics": [
                    {"opcode_hex": f"0x{opcode:04X}", "mnemonic": mnemonic}
                    for opcode, mnemonic in sorted(pairs)
                ],
                "known_exact_occurrences": len(matching_items),
                "known_exact_functions": len({key for key, _, _ in matching_items}),
                "known_exact_corpora": sorted({corpus for _, corpus, _ in matching_items}),
            }
        )
    rows.sort(key=lambda row: (-row["known_exact_occurrences"], row["family"]))
    return rows


def new_mismatch_patterns(base: dict, old_known: dict[str, dict]) -> list[dict]:
    rows = []
    for mismatch in base["known_complete_not_verified"]:
        key = f"{mismatch['corpus']}|{mismatch['entry']}|{mismatch['region_index']}"
        # Reports identify functions by entry index, while the mismatch base
        # intentionally stores the stable entry name. Resolve the unique row.
        candidates = [
            function
            for function in old_known.values()
            if function["corpus"] == mismatch["corpus"]
            and function["entry"] == mismatch["entry"]
            and function["region_index"] == mismatch["region_index"]
        ]
        if len(candidates) == 1 and not candidates[0]["complete"]:
            rows.append(
                {
                    "corpus": mismatch["corpus"],
                    "entry": mismatch["entry"],
                    "signature": mismatch["signature"],
                    "family": mismatch["first_mismatch_family"],
                    "first_source": mismatch["first_source"],
                    "first_reconstructed": mismatch["first_reconstructed"],
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "pb2022-analysis",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="v11 base JSON produced by analyze_v10_decision_gate.ps1",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.analysis_root
    base_path = args.base or root / "v11-decision-gate-base.json"
    out_path = args.out or root / "v11-decision-gate-data.json"

    known_v11 = {}
    known_v10 = {}
    for corpus in ("exmmain", "appexmfe", "pfcapsrv"):
        known_v11.update(
            load_functions(root / f"whole-function-v11-{corpus}" / "decode-report.json", corpus)
        )
        known_v10.update(
            load_functions(root / f"whole-function-v10-{corpus}" / "decode-report.json", corpus)
        )
    target = load_functions(root / "replicacao-snapshot-v11" / "decode-report.json", "replicacao")
    with base_path.open("r", encoding="utf-8-sig") as base_file:
        base = json.load(base_file)

    known_families, known_opcodes = aggregate_items(known_v11)
    target_families, target_opcodes = aggregate_items(target)
    new_mismatches = new_mismatch_patterns(base, known_v10)
    result = {
        "report_generation": "v11",
        "target": {
            "function_count": len(target),
            "incomplete_functions": sum(not function["complete"] for function in target.values()),
            "unresolved_count": sum(len(function["unresolved"]) for function in target.values()),
            "kinds": aggregate_kinds(target),
            "families": target_families,
            "opcodes": target_opcodes,
            "first_blockers": first_blockers(target),
            "direct_family_metrics": family_gate_metrics(target),
            "direct_family_known_exact_overlap": target_family_known_overlap(
                target, known_v11
            ),
        },
        "known": {
            "function_count": len(known_v11),
            "incomplete_functions": sum(
                not function["complete"] for function in known_v11.values()
            ),
            "unresolved_count": sum(
                len(function["unresolved"]) for function in known_v11.values()
            ),
            "kinds": aggregate_kinds(known_v11),
            "families": known_families,
            "opcodes": known_opcodes,
            "first_blockers": first_blockers(known_v11),
            "direct_family_metrics": family_gate_metrics(known_v11),
        },
        "complete_not_verified": {
            "count": len(base["known_complete_not_verified"]),
            "families": base["known_mismatch_families"],
            "newly_complete_mismatches": new_mismatches,
            "newly_complete_mismatch_families": dict(
                Counter(row["family"] for row in new_mismatches).most_common()
            ),
        },
        "compiled_symbol_control": {
            "checked": base["compiled_symbol_verified_checked"],
            "reproduced": base["compiled_symbol_verified_reproduced"],
        },
    }
    with out_path.open("w", encoding="utf-8") as out_file:
        json.dump(result, out_file, ensure_ascii=False, indent=2)
        out_file.write("\n")
    target_csv_path = root / "v11-decision-gate-target-unresolved.csv"
    with target_csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        fieldnames = (
            "opcode_hex",
            "mnemonic",
            "reason",
            "family",
            "kind",
            "occurrences",
            "functions",
            "corpora",
        )
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in target_opcodes:
            writer.writerow(
                {
                    **{field: row[field] for field in fieldnames if field not in {"kind", "corpora"}},
                    "kind": (
                        "direct_rule_absent"
                        if row["reason"] == "semantic rule not implemented"
                        else unresolved_kind(row)
                    ),
                    "corpora": ";".join(row["corpora"]),
                }
            )
    print(f"JSON: {out_path}")
    print(f"CSV: {target_csv_path}")
    print(
        "target unresolved/direct/dependent: "
        f"{result['target']['unresolved_count']}/"
        f"{next(row['occurrences'] for row in result['target']['kinds'] if row['kind'] == 'direct_rule_absent')}/"
        f"{next(row['occurrences'] for row in result['target']['kinds'] if row['kind'] == 'dependent_stack_or_context_failure')}"
    )
    print(
        "known incomplete/unresolved: "
        f"{result['known']['incomplete_functions']}/{result['known']['unresolved_count']}"
    )
    print(
        "complete-not-verified/new-mismatches: "
        f"{result['complete_not_verified']['count']}/{len(new_mismatches)}"
    )


if __name__ == "__main__":
    main()
