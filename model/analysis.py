"""Analysis and visualization tools for PowerBuilder code.

This module contains classes for analyzing and visualizing PowerBuilder code.
"""

from __future__ import annotations

from dataclasses import dataclass

from .utils.base import PBNode


# ─── Code Analysis ────────────────────────────────────────────────────
@dataclass
class CodeMetrics(PBNode):
    """Code metrics analysis."""

    lines_of_code: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    complexity: float


@dataclass
class DependencyAnalysis(PBNode):
    """Dependency analysis."""

    imports: dict[str, set[str]]
    exports: dict[str, set[str]]
    cycles: list[list[str]]


@dataclass
class SecurityAnalysis(PBNode):
    """Security analysis."""

    sql_injections: list[str]
    hardcoded_credentials: list[str]
    insecure_functions: list[str]


# ─── Code Visualization ─────────────────────────────────────────────────
@dataclass
class CallGraph(PBNode):
    """Function call graph."""

    nodes: list[str]
    edges: list[tuple[str, str]]
    weights: dict[tuple[str, str], int]


@dataclass
class DependencyGraph(PBNode):
    """Module dependency graph."""

    nodes: list[str]
    edges: list[tuple[str, str]]
    types: dict[str, str]  # module types


@dataclass
class UIFlowGraph(PBNode):
    """UI flow graph."""

    windows: list[str]
    transitions: list[tuple[str, str, str]]  # from, to, event
    entry_points: list[str]


# ─── Analysis Results ──────────────────────────────────────────────────
@dataclass
class AnalysisResult(PBNode):
    """Analysis result container."""

    metrics: CodeMetrics
    dependencies: DependencyAnalysis
    security: SecurityAnalysis
    call_graph: CallGraph | None = None
    ui_flow: UIFlowGraph | None = None


@dataclass
class AnalysisReport(PBNode):
    """Analysis report generator."""

    result: AnalysisResult
    format: str = "html"  # html, markdown, text
    include_graphs: bool = True
