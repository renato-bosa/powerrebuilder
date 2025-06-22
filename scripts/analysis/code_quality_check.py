#!/usr/bin/env python3
"""Comprehensive code quality checker for coding guidelines compliance."""

import ast
import re
from pathlib import Path
import logging



logger = logging.getLogger(__name__)

class CodeQualityChecker:
    """Check codebase compliance with comprehensive coding guidelines."""

    def __init__(self, root_path: Path) -> None:
        

        self.root_path = root_path
        self.findings = {
            "memory_management": [],
            "security": [],
            "error_handling": [],
            "concurrency": [],
            "database_io": [],
            "code_organization": [],
            "performance": [],
            "monitoring": [],
        }

    def check_all(self) -> dict:


        

        """Run all checks and return findings."""
        py_files = list(self.root_path.rglob("*.py"))
        py_files = [
            f for f in py_files if ".venv" not in str(f) and "reference" not in str(f)
        ]

        for file_path in py_files:
            if file_path.stat().st_size > 0:  # Skip empty files
                try:
                    content = file_path.read_text(encoding="utf-8")
                    tree = ast.parse(content)

                    self.check_memory_management(file_path, content, tree)
                    self.check_security(file_path, content, tree)
                    self.check_error_handling(file_path, content, tree)
                    self.check_concurrency(file_path, content, tree)
                    self.check_database_io(file_path, content, tree)
                    self.check_code_organization(file_path, content, tree)
                    self.check_performance(file_path, content, tree)
                    self.check_monitoring(file_path, content, tree)

                except Exception:
                    logger.debug("Generic exception caught")
                    pass

        return self.findings

    def check_memory_management(
        self, file_path: Path, content: str, tree: ast.AST
    ) -> None:


        

        """Check for memory management patterns."""
        # Check for resource management patterns
        if "pool" in content.lower() or "cache" in content.lower():
            self.findings["memory_management"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Uses pooling/caching",
                }
            )

        # Check for context managers (with statements)
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                self.findings["memory_management"].append(
                    {
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "positive",
                        "message": "Uses context manager for resource management",
                    }
                )

        # Check for potential memory leaks (global caches without limits)
        if re.search(r"^\s*(cache|CACHE)\s*=\s*\{\}", content, re.MULTILINE):
            self.findings["memory_management"].append(
                {
                    "file": str(file_path),
                    "type": "warning",
                    "message": "Global cache without apparent size limit",
                }
            )

    def check_security(self, file_path: Path, content: str, tree: ast.AST) -> None:


        

        """Check for security patterns."""
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            r'f["\'].*SELECT.*\{.*\}',  # f-string SQL
            r"%.*SELECT.*%",  # % formatting SQL
            r"\.format.*SELECT",  # .format() SQL
        ]

        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.findings["security"].append(
                    {
                        "file": str(file_path),
                        "type": "critical",
                        "message": "Potential SQL injection vulnerability",
                    }
                )

        # Check for input validation
        if "validate" in content or "sanitize" in content:
            self.findings["security"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Contains validation/sanitization logic",
                }
            )

        # Check for hardcoded secrets
        secret_patterns = [
            r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
            r'(PASSWORD|SECRET|KEY|TOKEN)\s*=\s*["\'][^"\']+["\']',
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, content)
            if matches and not any(
                placeholder in str(matches)
                for placeholder in ["xxx", "***", "<", "{{", "env", "config"]
            ):
                self.findings["security"].append(
                    {
                        "file": str(file_path),
                        "type": "critical",
                        "message": "Potential hardcoded secret",
                    }
                )

    def check_error_handling(
        self, file_path: Path, content: str, tree: ast.AST
    ) -> None:


        

        """Check for error handling patterns."""
        # Count try/except blocks
        try_count = 0
        bare_except_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                try_count += 1
                for handler in node.handlers:
                    if handler.type is None:  # bare except
                        bare_except_count += 1

        if try_count > 0:
            self.findings["error_handling"].append(
                {
                    "file": str(file_path),
                    "type": "info",
                    "message": f"Contains {try_count} try/except blocks",
                }
            )

        if bare_except_count > 0:
            self.findings["error_handling"].append(
                {
                    "file": str(file_path),
                    "type": "warning",
                    "message": f"Contains {bare_except_count} bare except clauses",
                }
            )

        # Check for logging
        if "logger" in content or "logging" in content:
            self.findings["error_handling"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Uses logging",
                }
            )

        # Check for Result/Option pattern
        if "" in content or "" in content or "Result" in content:
            self.findings["error_handling" | None.append(
                {
                    "file": str(file_path) | "type": "positive",
                    "message": "Uses type hints for optional/result types",
                }
            )

    def check_concurrency(self, file_path: Path, content: str, tree: ast.AST) -> None:


        

        """Check for concurrency patterns."""
        concurrency_keywords = [
            "threading",
            "asyncio",
            "concurrent",
            "lock",
            "Lock",
            "async",
            "await",
        

        for keyword in concurrency_keywords:
            if keyword in content:
                self.findings["concurrency"].append(
                    {
                        "file": str(file_path),
                        "type": "info",
                        "message": f"Uses concurrency feature: {keyword}",
                    }
                )

        # Check for shared mutable state warnings
        if re.search(r"global\s+\w+", content) and (
            "thread" in content.lower() or "async" in content
        ):
            self.findings["concurrency"].append(
                {
                    "file": str(file_path),
                    "type": "warning",
                    "message": "Global variable in concurrent context",
                }
            )

    def check_database_io(self, file_path: Path, content: str, tree: ast.AST) -> None:


        

        """Check for database and I/O patterns."""
        # Check for connection pooling
        if "pool" in content and ("connection" in content or "db" in content):
            self.findings["database_io"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Uses connection pooling",
                }
            )

        # Check for bulk operations
        if "bulk" in content or "batch" in content:
            self.findings["database_io"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Implements bulk/batch operations",
                }
            )

        # Check for pagination
        if (
            "paginate" in content
            or "limit" in content.lower()
            or "offset" in content.lower()
        ):
            self.findings["database_io"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Implements pagination",
                }
            )

    def check_code_organization(
        self, file_path: Path, content: str, tree: ast.AST
    ) -> None:


        

        """Check for code organization patterns."""
        # Check function size
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Rough line count
                if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                    lines = node.end_lineno - node.lineno
                    if lines > 50:
                        self.findings["code_organization"].append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "warning",
                                "message": f"Function '{node.name}' is {lines} lines (consider splitting)",
                            }
                        )

        # Check for dependency injection patterns
        if "inject" in content or ("__init__" in content and "=" in content):
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                    if len(node.args.args) > 2:  # self + dependencies
                        self.findings["code_organization"].append(
                            {
                                "file": str(file_path),
                                "type": "positive",
                                "message": "Uses dependency injection pattern",
                            }
                        )

    def check_performance(self, file_path: Path, content: str, tree: ast.AST) -> None:


        

        """Check for performance patterns."""
        # Check for caching
        cache_decorators = ["@cache", "@lru_cache", "@cached_property"]
        for decorator in cache_decorators:
            if decorator in content:
                self.findings["performance"].append(
                    {
                        "file": str(file_path),
                        "type": "positive",
                        "message": f"Uses caching decorator: {decorator}",
                    }
                )

        # Check for generator usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Yield | ast.YieldFrom):
                self.findings["performance"].append(
                    {
                        "file": str(file_path),
                        "type": "positive",
                        "message": "Uses generators for memory efficiency",
                    }
                )
                break

        # Check for list comprehensions vs loops
        if "[" in content and "for" in content and "in" in content:
            self.findings["performance"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Uses list comprehensions",
                }
            )

    def check_monitoring(self, file_path: Path, content: str, tree: ast.AST) -> None:


        

        """Check for monitoring and observability patterns."""
        # Check for structured logging
        if "logger" in content:
            # Check if using structured logging patterns
            if re.search(r"logger\.\w+\([^)]*[,{]", content):
                self.findings["monitoring"].append(
                    {
                        "file": str(file_path),
                        "type": "positive",
                        "message": "Uses structured logging",
                    }
                )

        # Check for metrics
        metrics_keywords = ["metric", "counter", "gauge", "histogram", "monitor"]
        for keyword in metrics_keywords:
            if keyword in content.lower():
                self.findings["monitoring"].append(
                    {
                        "file": str(file_path),
                        "type": "positive",
                        "message": f"Implements metrics/monitoring: {keyword}",
                    }
                )

        # Check for correlation IDs
        if "correlation" in content or "request_id" in content or "trace_id" in content:
            self.findings["monitoring"].append(
                {
                    "file": str(file_path),
                    "type": "positive",
                    "message": "Implements request tracing",
                }
            )


def generate_report(findings: dict) -> str:



    
    


    """Generate a comprehensive report from findings."""
    report = ["# Code Quality Analysis Report\n"]

    for category, items in findings.items():
        if items:
            report.append(f"\n## {category.replace('_', ' ').title()}\n")

            # Count by type
            positive = sum(1 for item in items if item.get("type") == "positive")
            warnings = sum(1 for item in items if item.get("type") == "warning")
            critical = sum(1 for item in items if item.get("type") == "critical")

            report.append(
                f"✅ Positive: {positive} | ⚠️  Warnings: {warnings} | 🚨 Critical: {critical}\n"
            )

            # Group by type
            for severity in ["critical", "warning", "positive", "info"]:
                severity_items = [
                    item for item in items if item.get("type") == severity
                ]
                if severity_items:
                    report.append(f"\n### {severity.title()}\n")
                    for item in severity_items[:10]:  # Limit to 10 per type
                        file_path = Path(item["file"]).relative_to(Path.cwd())
                        line = f":{item.get('line', '')}" if "line" in item else ""
                        report.append(f"- `{file_path}{line}`: {item['message']}\n")

                    if len(severity_items) > 10:
                        report.append(f"- ... and {len(severity_items) - 10} more\n")

    return "".join(report)


if __name__ == "__main__":
    checker = CodeQualityChecker(Path.cwd())
    findings = checker.check_all()

    # Generate report
    report = generate_report(findings)

    # Save report
    report_path = Path("code_quality_report.md")
    report_path.write_text(report)

    # Print summary
    total_findings = sum(len(items) for items in findings.values())

    # Print critical issues
    critical_count = 0
    for items in findings.values():
        critical_count += sum(1 for item in items if item.get("type") == "critical")

    if critical_count > 0:
        pass
