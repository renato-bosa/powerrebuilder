"""Example tests using factory_boy and mimesis for test data generation."""

import pytest
from mimesis import Person, Address, Datetime, Text
from mimesis.locales import Locale

from tests.factories import (
    VariableFactory,
    IntegerLiteralFactory,
    PbEntryDefinitionFactory,
    PowerBuilderCodeFactory,
)


class TestWithFactories:
    """Tests demonstrating factory_boy usage."""

    def test_ast_node_creation(self):


        

        """Test creating AST nodes with factories."""
        # Create a simple variable
        variable = VariableFactory(name="test_variable")
        assert variable.name == "test_variable"
        assert variable.source_anchor is not None
        assert variable.source_anchor.line >= 1
        assert variable.source_anchor.column >= 1

        # Create a literal
        literal = IntegerLiteralFactory(value=42)
        assert literal.value == 42

        # Create an assignment manually since dataclasses are complex with factories
        from model.ast import Assignment
        assignment = Assignment(
            target=VariableFactory(name="target_var"),
            value=IntegerLiteralFactory(value=100)
        )
        assert assignment.target.name == "target_var"
        assert assignment.value.value == 100

    def test_pb_entry_definition(self):


        

        """Test creating PowerBuilder entry definitions."""
        # Create multiple entries
        entries = PbEntryDefinitionFactory.create_batch(5)

        assert len(entries) == 5
        for entry in entries:
            assert entry.objectname.endswith('.sru')
            assert entry.version in ['10.5', '11.0', '12.5', '2017', '2019']
            assert entry.filesize > 0
            assert entry.offset >= 0

    def test_powerbuilder_code_generation(self):


        

        """Test generating PowerBuilder code snippets."""
        # Generate a window
        window_code = PowerBuilderCodeFactory.window_definition("w_test_window")
        assert "w_test_window" in window_code
        assert "from window" in window_code
        assert "on w_test_window.create" in window_code

        # Generate a function
        function_code = PowerBuilderCodeFactory.function_definition("f_calculate", "long")
        assert "function long f_calculate" in function_code
        assert "string as_param1" in function_code
        assert "return li_return" in function_code

        # Generate DataWindow syntax
        dw_syntax = PowerBuilderCodeFactory.datawindow_syntax()
        assert "release 12.5" in dw_syntax
        assert "datawindow(" in dw_syntax
        assert "table(column=" in dw_syntax


class TestWithMimesis:
    """Tests demonstrating mimesis usage for realistic test data."""

    def setup_method(self):


        

        """Set up mimesis providers."""
        self.person = Person(locale=Locale.EN)
        self.address = Address(locale=Locale.EN)
        self.datetime = Datetime(locale=Locale.EN)
        self.text = Text(locale=Locale.EN)

    def test_realistic_variable_names(self):


        

        """Generate realistic variable names."""
        # PowerBuilder naming conventions
        prefixes = {
            'string': 's_',
            'integer': 'i_',
            'long': 'l_',
            'boolean': 'b_',
            'date': 'd_',
            'window': 'w_',
            'datawindow': 'dw_',
        }

        # Generate variable names
        var_names = []
        for var_type, prefix in prefixes.items():
            # Use person names for meaningful variable names
            name = self.person.first_name().lower()
            var_name = f"{prefix}{name}"
            var_names.append((var_type, var_name))

        # All should follow convention
        for var_type, var_name in var_names:
            prefix = prefixes[var_type]
            assert var_name.startswith(prefix)

    def test_realistic_datawindow_data(self):


        

        """Generate realistic data for DataWindow testing."""
        # Create test data for a customer DataWindow
        customers = []
        for _ in range(10):
            customer = {
                'id': self.person.identifier(mask='#####'),
                'first_name': self.person.first_name(),
                'last_name': self.person.last_name(),
                'email': self.person.email(),
                'phone': self.person.phone_number(),
                'address': self.address.street_name(),
                'city': self.address.city(),
                'state': self.address.state(),
                'zip': self.address.zip_code(),
                'created_date': self.datetime.datetime().isoformat(),
                'notes': self.text.sentence(),
            }
            customers.append(customer)

        # Verify data
        assert len(customers) == 10
        for customer in customers:
            assert '@' in customer['email']
            assert len(customer['id']) == 5
            assert customer['created_date']

    def test_realistic_sql_generation(self):


        

        """Generate realistic SQL statements for DataWindow testing."""
        # Table and column names
        table_name = f"tbl_{self.text.word().lower()}"
        columns = [
            f"col_{self.text.word().lower()}" for _ in range(5)
        ]

        # Generate SELECT statement
        sql = f"SELECT {', '.join(columns)} FROM {table_name} WHERE {columns[0]} = ?"  # noqa: S608

        assert "SELECT" in sql
        assert table_name in sql
        assert all(col in sql for col in columns)

    def test_realistic_error_messages(self):


        

        """Generate realistic error messages for testing error handling."""
        error_templates = [
            "Failed to {action} {object}: {reason}",
            "Invalid {field} value: expected {expected}, got {actual}",
            "{operation} error at line {line}: {detail}",
            "Database error: {code} - {message}",
        ]

        errors = []
        for template in error_templates:
            error = template.format(
                action=self.text.word(),
                object=f"dw_{self.text.word()}",
                reason=self.text.sentence(),
                field=f"f_{self.text.word()}",
                expected=self.person.identifier(mask='###'),
                actual=self.person.identifier(mask='XXX'),
                operation="Parse",
                line=self.person.identifier(mask='##'),
                detail=self.text.sentence(),
                code=self.person.identifier(mask='####'),
                message=self.text.sentence(),
            )
            errors.append(error)

        # All errors should be non-empty
        assert all(errors)
        assert all(len(e) > 20 for e in errors)


class TestIntegrationWithFactories:
    """Integration tests using multiple factories together."""

    def test_complete_ast_generation(self):


        

        """Generate a complete AST using factories."""
        # Create a small program
        assignments = []

        # Generate some variable assignments
        for i in range(5):
            from model.ast import Assignment
            assignment = Assignment(
                target=VariableFactory(name=f"var_{i}"),
                value=IntegerLiteralFactory(value=i * 10)
            )
            assignments.append(assignment)

        # Verify structure
        assert len(assignments) == 5
        for i, assignment in enumerate(assignments):
            assert assignment.target.name == f"var_{i}"
            assert assignment.value.value == i * 10

    def test_realistic_pb_file_simulation(self):


        

        """Simulate a realistic PowerBuilder file structure."""
        # Create entry definitions for a typical PBD
        entries = []

        # Add windows
        for i in range(3):
            entry = PbEntryDefinitionFactory(
                objectname=f"w_window_{i}.srw",
                objecttype=13,  # Window type
            )
            entries.append(entry)

        # Add datawindows
        for i in range(5):
            entry = PbEntryDefinitionFactory(
                objectname=f"d_datawindow_{i}.srd",
                objecttype=18,  # DataWindow type
            )
            entries.append(entry)

        # Add functions
        for i in range(2):
            entry = PbEntryDefinitionFactory(
                objectname=f"f_function_{i}.srf",
                objecttype=0,  # Function type
            )
            entries.append(entry)

        # Verify structure
        assert len(entries) == 10
        window_count = sum(1 for e in entries if e.objecttype == 13)
        dw_count = sum(1 for e in entries if e.objecttype == 18)
        func_count = sum(1 for e in entries if e.objecttype == 0)

        assert window_count == 3
        assert dw_count == 5
        assert func_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
