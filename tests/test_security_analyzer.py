"""Tests for the security analyzer module."""

import pytest
from model.security_analyzer import SecurityAnalyzer, analyze_security
from model.analysis import SecurityAnalysis
from model.ast.ast_nodes import VariableDeclaration, BinaryExpression
from model.ast.functions import FunctionCall
from model.ast.sql import SQLQuery
from model.entities.expressions import (
    PBStringLiteral, PBNumberLiteral, PBVariable
)


class TestSecurityAnalyzer:
    """Test cases for SecurityAnalyzer."""
    
    def test_detect_sql_injection(self):
        """Test detection of SQL injection vulnerabilities."""
        analyzer = SecurityAnalyzer()
        
        # Create a SQL query with string concatenation (simulating injection risk)
        sql_node = SQLQuery(
            query="SELECT * FROM users WHERE name = '" + "' + :user_input + '"
        )
        
        result = analyzer.analyze([sql_node], "test.pb")
        
        assert len(result.sql_injections) > 0
        # Check that it mentions SQL and concatenation/injection
        assert any(word in result.sql_injections[0].lower() for word in ["sql", "injection", "concatenation"])
        
    def test_detect_hardcoded_credentials(self):
        """Test detection of hardcoded credentials."""
        analyzer = SecurityAnalyzer()
        
        # Create a variable declaration with hardcoded password
        var_node = VariableDeclaration(
            name="db_password",
            type=None,
            initial_value=PBStringLiteral(value="MySecretPassword123!")
        )
        
        # Simulate code text extraction
        var_node.to_source = lambda: 'string db_password = "MySecretPassword123!"'
        
        result = analyzer.analyze([var_node], "config.pb")
        
        assert len(result.hardcoded_credentials) > 0
        assert "credential" in result.hardcoded_credentials[0].lower()
        
    def test_detect_insecure_functions(self):
        """Test detection of insecure function usage."""
        analyzer = SecurityAnalyzer()
        
        # Create a function call with variable arguments
        func_call = FunctionCall(
            function_name="execute",
            arguments=[
                BinaryExpression(
                    left=PBStringLiteral(value="cmd /c "),
                    operator="+",
                    right=PBVariable(name="user_command")
                )
            ]
        )
        
        result = analyzer.analyze([func_call], "commands.pb")
        
        assert len(result.insecure_functions) > 0
        assert "insecure" in result.insecure_functions[0].lower()
        
    def test_skip_safe_patterns(self):
        """Test that safe patterns are not flagged."""
        analyzer = SecurityAnalyzer()
        
        # Safe parameterized query
        safe_sql = SQLQuery(
            query="SELECT * FROM users WHERE id = :user_id"
        )
        
        # Placeholder password
        placeholder_var = VariableDeclaration(
            name="password",
            type=None,
            initial_value=PBStringLiteral(value="changeme")
        )
        placeholder_var.to_source = lambda: 'string password = "changeme"'
        
        # Safe function call with literal
        safe_func = FunctionCall(
            function_name="fileopen",
            arguments=[PBStringLiteral(value="report.txt")]
        )
        
        result = analyzer.analyze([safe_sql, placeholder_var, safe_func], "safe.pb")
        
        # Parameterized query should not be flagged
        assert not any("SELECT * FROM users WHERE id = :user_id" in issue for issue in result.sql_injections)
        
        # Placeholder passwords should be skipped
        assert not any("changeme" in issue for issue in result.hardcoded_credentials)
        
        # Function with literal argument is less risky
        assert len(result.insecure_functions) == 0
        
    def test_analyze_security_function(self):
        """Test the convenience analyze_security function."""
        nodes = [
            FunctionCall(
                function_name="shellexecute", 
                arguments=[PBVariable(name="cmd")]
            )
        ]
        
        result = analyze_security(nodes, "test.pb")
        
        assert isinstance(result, SecurityAnalysis)
        assert len(result.insecure_functions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])