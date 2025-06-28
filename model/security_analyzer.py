"""Security analyzer for PowerBuilder code.

This module analyzes PowerBuilder code for potential security vulnerabilities including:
- SQL injection vulnerabilities
- Hardcoded credentials
- Use of insecure functions
- Unvalidated user input
"""

import logging
import re
from typing import Any

from model.core.analysis import SecurityAnalysis
from model.ast.ast_nodes import BinaryExpression, VariableDeclaration
from model.ast.functions import FunctionCall
from model.ast.sql import SQLQuery, SqlStatement
from model.entities.expressions import (
    PBBooleanLiteral,
    PBNullLiteral,
    PBNumberLiteral,
    PBStringLiteral,
)
from model.utils.base import PBNode

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """Analyzes PowerBuilder code for security vulnerabilities."""

    # Patterns for detecting hardcoded credentials
    CREDENTIAL_PATTERNS = [
        r'password\s*=\s*["\']([^"\']+)["\']', r'pwd\s*=\s*["\']([^"\']+)["\']', r'passwd\s*=\s*["\']([^"\']+)["\']', r'pass\s*=\s*["\']([^"\']+)["\']', r'secret\s*=\s*["\']([^"\']+)["\']', r'api_key\s*=\s*["\']([^"\']+)["\']', r'apikey\s*=\s*["\']([^"\']+)["\']', r'token\s*=\s*["\']([^"\']+)["\']', r'auth\s*=\s*["\']([^"\']+)["\']', r'connection.*string\s*=\s*["\']([^"\']+)["\']', ]

    # PowerBuilder functions that could be insecure if misused
    INSECURE_FUNCTIONS = {
        "run": "Command execution - validate input", "execute": "Dynamic execution - validate input", "shellexecute": "Shell command execution - validate input", "openuserobject": "Dynamic object creation - validate type", "createobject": "Dynamic object creation - validate type", "fileopen": "File access - validate path", "filewrite": "File write - validate path and content", "registryget": "Registry access - validate key", "registryset": "Registry modification - validate key and value", "setlibrarylist": "Library loading - validate paths", "addtolibrarylist": "Library loading - validate paths", }

    # SQL keywords that indicate dynamic query construction
    SQL_DYNAMIC_KEYWORDS = {
        "execute immediate", "prepare", "execute", "dynamic", }

    def __init__(self) -> None:




        """Initialize the security analyzer."""
        self.sql_injections: list[dict[str, Any]] = []
        self.hardcoded_credentials: list[dict[str, Any]] = []
        self.insecure_functions: list[dict[str, Any]] = []

    def analyze(self, ast_nodes: list[PBNode], source_file: str | None = None) -> SecurityAnalysis:




        """Analyze AST nodes for security vulnerabilities.

        Args:
            ast_nodes: List of AST nodes to analyze
            source_file: Optional source file path for context

        Returns:
            SecurityAnalysis object containing found vulnerabilities
        """
        self.sql_injections.clear()
        self.hardcoded_credentials.clear()
        self.insecure_functions.clear()

        for node in ast_nodes:
            self._analyze_node(node, source_file)

        return SecurityAnalysis(
            sql_injections=[self._format_issue(issue) for issue in self.sql_injections], hardcoded_credentials=[self._format_issue(issue) for issue in self.hardcoded_credentials], insecure_functions=[self._format_issue(issue) for issue in self.insecure_functions],
        )

    def _analyze_node(self, node: PBNode, source_file: str | None = None) -> None:


        """Recursively analyze a node and its children.

        Args:
            node: AST node to analyze
            source_file: Optional source file path
        """
        if isinstance(node, SqlStatement) or isinstance(node, SQLQuery):
            self._check_sql_injection(node, source_file)

        if isinstance(node, (VariableDeclaration, BinaryExpression)):
            self._check_hardcoded_credentials(node, source_file)

        if isinstance(node, FunctionCall):
            self._check_insecure_functions(node, source_file)

        # Recursively analyze children
        if hasattr(node, "__dict__"):
            for attr_name, attr_value in node.__dict__.items():
                if isinstance(attr_value, PBNode):
                    self._analyze_node(attr_value, source_file)
                elif isinstance(attr_value, list):
                    for item in attr_value:
                        if isinstance(item, PBNode):
                            self._analyze_node(item, source_file)

    def _check_sql_injection(self, node: PBNode, source_file: str | None = None) -> None:


        """Check for SQL injection vulnerabilities.

        Args:
            node: SQL-related AST node
            source_file: Optional source file path
        """
        sql_text = self._extract_sql_text(node)
        if not sql_text:
            return

        # Check for string concatenation in SQL
        if any(op in sql_text.lower() for op in ["+", "||", "&"]):
            # Look for variable references that might be user input
            if re.search(r":\w+|@\w+|\?\w*", sql_text):
                self.sql_injections.append({
                    "type": "potential_sql_injection", "severity": "high", "description": "SQL query uses string concatenation with variables", "code": sql_text[:200], # First 200 chars
                    "file": source_file, "line": getattr(node, "line", None), "recommendation": "Use parameterized queries instead of string concatenation",
                })

        # Check for dynamic SQL execution
        if any(keyword in sql_text.lower() for keyword in self.SQL_DYNAMIC_KEYWORDS):
            self.sql_injections.append({
                "type": "dynamic_sql", "severity": "medium", "description": "Dynamic SQL execution detected", "code": sql_text[:200], "file": source_file, "line": getattr(node, "line", None), "recommendation": "Validate and sanitize all inputs used in dynamic SQL",
            })

    def _check_hardcoded_credentials(self, node: PBNode, source_file: str | None = None) -> None:


        """Check for hardcoded credentials.

        Args:
            node: Variable or assignment node
            source_file: Optional source file path
        """
        code_text = self._extract_code_text(node)
        if not code_text:
            return

        for pattern in self.CREDENTIAL_PATTERNS:
            matches = re.finditer(pattern, code_text, re.IGNORECASE)
            for match in matches:
                credential_value = match.group(1)
                # Skip obvious placeholders
                if credential_value.lower() in ["", "password", "pwd", "xxx", "***", "...", "changeme"]:
                    continue

                self.hardcoded_credentials.append({
                    "type": "hardcoded_credential", "severity": "critical", "description": f"Hardcoded credential found: {match.group(0)}", "code": match.group(0), "file": source_file, "line": getattr(node, "line", None), "recommendation": "Store credentials securely using environment variables or secure credential storage",
                })

    def _check_insecure_functions(self, node: FunctionCall, source_file: str | None = None) -> None:


        """Check for use of insecure functions.

        Args:
            node: Function call node
            source_file: Optional source file path
        """
        func_name = getattr(node, "function_name", "").lower()

        if func_name in self.INSECURE_FUNCTIONS:
            warning = self.INSECURE_FUNCTIONS[func_name]

            # Check if arguments might contain user input
            has_variable_args = any(
                not isinstance(arg, (PBStringLiteral, PBNumberLiteral, PBBooleanLiteral, PBNullLiteral)) 
                for arg in getattr(node, "arguments", [])
            )

            if has_variable_args:
                self.insecure_functions.append({
                    "type": "insecure_function", "severity": "high" if "execute" in func_name or "shell" in func_name else "medium", "description": f"Potentially insecure use of {func_name}() with variable arguments", "code": self._extract_code_text(node)[:200], "file": source_file, "line": getattr(node, "line", None), "recommendation": warning,
                })

    def _extract_sql_text(self, node: PBNode) -> str:




        """Extract SQL text from a SQL node.

        Args:
            node: SQL-related node

        Returns:
            SQL text or empty string
        """
        if hasattr(node, "sql"):
            return str(node.sql)
        elif hasattr(node, "query"):
            return str(node.query)
        elif hasattr(node, "statement"):
            return str(node.statement)
        return ""

    def _extract_code_text(self, node: PBNode) -> str:




        """Extract code text from a node.

        Args:
            node: AST node

        Returns:
            Code text or empty string
        """
        if hasattr(node, "to_source"):
            return node.to_source()
        elif hasattr(node, "__str__"):
            return str(node)
        return ""

    def _format_issue(self, issue: dict[str, Any]) -> str:




        """Format an issue for the report.

        Args:
            issue: Issue dictionary

        Returns:
            Formatted issue string
        """
        parts = [f"[{issue["severity"].upper()}]"]

        if issue.get("file"):
            parts.append(f"{issue["file"]}")
            if issue.get("line"):
                parts.append(f":{issue["line"]}")

        parts.append(f"- {issue["description"]}")

        if issue.get("recommendation"):
            parts.append(f"({issue["recommendation"]})")

        return " ".join(parts)


def analyze_security(ast_nodes: list[PBNode], source_file: str | None = None) -> SecurityAnalysis:








    """Convenience function to analyze security vulnerabilities.

    Args:
        ast_nodes: List of AST nodes to analyze
        source_file: Optional source file path

    Returns:
        SecurityAnalysis object with results
    """
    analyzer = SecurityAnalyzer()
    return analyzer.analyze(ast_nodes, source_file)
