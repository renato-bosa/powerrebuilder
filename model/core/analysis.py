"""Analysis and visualization tools for PowerBuilder code.

This module contains classes for analyzing and visualizing PowerBuilder code.
"""

from __future__ import annotations

from dataclasses import dataclass

from model.utils.base import PBNode


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


# ─── Code Analysis Implementation ─────────────────────────────────────
class CodeAnalyzer:
    """Analyzes PowerBuilder code to collect metrics and dependencies."""

    def __init__(self) -> None:
        """Initialize the code analyzer."""
        self.metrics = {
            "lines_of_code": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "function_count": 0,
            "class_count": 0,
            "complexity": 0.0,
        }
        self.imports: dict[str, set[str]] = {}
        self.exports: dict[str, set[str]] = {}
        self.functions: list[str] = []
        self.classes: list[str] = []

    def analyze_code(self, source_code: str, filename: str | None = None) -> CodeMetrics:
        """Analyze source code to collect metrics.
        
        Args:
            source_code: PowerBuilder source code
            filename: Optional filename for context
            
        Returns:
            CodeMetrics object with collected metrics
        """
        lines = source_code.split('\n')
        self.metrics["lines_of_code"] = 0
        self.metrics["comment_lines"] = 0
        self.metrics["blank_lines"] = 0
        
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Count blank lines
            if not stripped:
                self.metrics["blank_lines"] += 1
                continue
                
            # Handle block comments
            if "/*" in stripped:
                in_block_comment = True
            if in_block_comment:
                self.metrics["comment_lines"] += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
                
            # Handle line comments
            if stripped.startswith("//"):
                self.metrics["comment_lines"] += 1
                continue
                
            # Count actual code lines
            self.metrics["lines_of_code"] += 1
            
            # Look for function definitions
            if any(keyword in stripped.lower() for keyword in ["function", "subroutine", "event"]):
                self.metrics["function_count"] += 1
                
            # Look for class definitions
            if any(keyword in stripped.lower() for keyword in ["class", "type", "structure"]):
                self.metrics["class_count"] += 1
                
        # Calculate complexity (simplified McCabe complexity)
        self.metrics["complexity"] = self._calculate_complexity(source_code)
        
        return CodeMetrics(
            lines_of_code=self.metrics["lines_of_code"],
            comment_lines=self.metrics["comment_lines"],
            blank_lines=self.metrics["blank_lines"],
            function_count=self.metrics["function_count"],
            class_count=self.metrics["class_count"],
            complexity=self.metrics["complexity"],
        )

    def analyze_dependencies(self, ast_nodes: list, module_name: str) -> DependencyAnalysis:
        """Analyze dependencies from AST nodes.
        
        Args:
            ast_nodes: List of AST nodes
            module_name: Name of the current module
            
        Returns:
            DependencyAnalysis object
        """
        imports = {module_name: set()}
        exports = {module_name: set()}
        
        for node in ast_nodes:
            # Extract imports
            if hasattr(node, "__class__") and "Import" in node.__class__.__name__:
                if hasattr(node, "module_name"):
                    imports[module_name].add(node.module_name)
                    
            # Extract exports (public functions/classes)
            if hasattr(node, "visibility") and node.visibility == "public":
                if hasattr(node, "name"):
                    exports[module_name].add(node.name)
                    
        # Detect cycles (simplified)
        cycles = self._detect_dependency_cycles(imports)
        
        return DependencyAnalysis(
            imports=imports,
            exports=exports,
            cycles=cycles,
        )

    def _calculate_complexity(self, source_code: str) -> float:
        """Calculate cyclomatic complexity.
        
        Args:
            source_code: Source code to analyze
            
        Returns:
            Complexity score
        """
        # Count decision points
        decision_keywords = [
            "if", "elseif", "else", "case", "when", "for", "while", 
            "do", "choose", "catch", "&&", "||", "and", "or"
        ]
        
        complexity = 1  # Base complexity
        
        for keyword in decision_keywords:
            # Simple count of decision points
            complexity += source_code.lower().count(f" {keyword} ")
            complexity += source_code.lower().count(f"\n{keyword} ")
            complexity += source_code.lower().count(f"\t{keyword} ")
            
        # Normalize by function count
        if self.metrics["function_count"] > 0:
            complexity = complexity / self.metrics["function_count"]
            
        return round(complexity, 2)

    def _detect_dependency_cycles(self, imports: dict[str, set[str]]) -> list[list[str]]:
        """Detect circular dependencies.
        
        Args:
            imports: Import relationships
            
        Returns:
            List of dependency cycles
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(module: str, path: list[str]) -> None:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            for dep in imports.get(module, set()):
                if dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    if cycle not in cycles:
                        cycles.append(cycle)
                elif dep not in visited:
                    dfs(dep, path.copy())
                    
            rec_stack.remove(module)
            
        for module in imports:
            if module not in visited:
                dfs(module, [])
                
        return cycles


# ─── Convenience Functions ────────────────────────────────────────────
def analyze_code(source_code: str, filename: str | None = None) -> CodeMetrics:
    """Analyze source code to collect metrics.
    
    Args:
        source_code: PowerBuilder source code
        filename: Optional filename for context
        
    Returns:
        CodeMetrics object
    """
    analyzer = CodeAnalyzer()
    return analyzer.analyze_code(source_code, filename)


def collect_metrics(ast_nodes: list, source_code: str | None = None) -> CodeMetrics:
    """Collect metrics from AST nodes and optionally source code.
    
    Args:
        ast_nodes: List of AST nodes
        source_code: Optional source code for line counting
        
    Returns:
        CodeMetrics object
    """
    analyzer = CodeAnalyzer()
    
    # Count from AST nodes
    for node in ast_nodes:
        if hasattr(node, "__class__"):
            class_name = node.__class__.__name__
            if "Function" in class_name or "Method" in class_name:
                analyzer.metrics["function_count"] += 1
            elif "Class" in class_name or "Type" in class_name:
                analyzer.metrics["class_count"] += 1
    
    # If source code provided, analyze it for line counts
    if source_code:
        return analyzer.analyze_code(source_code)
    else:
        # Return partial metrics from AST only
        return CodeMetrics(
            lines_of_code=0,
            comment_lines=0,
            blank_lines=0,
            function_count=analyzer.metrics["function_count"],
            class_count=analyzer.metrics["class_count"],
            complexity=0.0,
        )
