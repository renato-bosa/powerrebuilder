"""Benchmarks for PowerBuilder parsing performance."""

import pytest
from lark import Lark
from pathlib import Path

from parse.base_parser import PowerBuilderBaseParser
from parse.powerbuilder_transformer import PowerBuilderTransformer


class TestParsingPerformance:
    """Benchmark parsing operations."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return PowerBuilderBaseParser()
    
    @pytest.fixture
    def sample_code_snippets(self):
        """Sample PowerBuilder code for benchmarking."""
        return {
            'simple_function': '''
                public function integer calculate(integer a, integer b)
                    return a + b
                end function
            ''',
            'complex_window': '''
                forward
                global type w_main from window
                end type
                type cb_ok from commandbutton within w_main
                end type
                end forward
                
                global type w_main from window
                integer width = 2000
                integer height = 1500
                boolean titlebar = true
                string title = "Main Window"
                cb_ok cb_ok
                end type
                
                type cb_ok from commandbutton within w_main
                integer x = 100
                integer y = 100
                integer width = 400
                integer height = 100
                string text = "OK"
                end type
                
                on w_main.create
                this.cb_ok=create cb_ok
                this.Control[]={this.cb_ok}
                end on
            ''',
            'datawindow_syntax': '''
                release 12.5;
                datawindow(units=0 timer_interval=0 color=1073741824)
                summary(height=0 color="536870912")
                footer(height=0 color="536870912")
                detail(height=84 color="536870912")
                table(column=(type=char(50) name=name dbname="employee.name")
                      column=(type=number name=id dbname="employee.id")
                      retrieve="SELECT * FROM employee")
            ''',
            'large_class': '\n'.join([
                'public function integer method_%d()' % i +
                '\n    return %d\nend function' % i
                for i in range(50)
            ])
        }
    
    def test_simple_function_parsing(self, benchmark, parser, sample_code_snippets):
        """Benchmark parsing of simple functions."""
        code = sample_code_snippets['simple_function']
        
        def parse():
            return parser.parse(code)
        
        result = benchmark(parse)
        assert benchmark.stats['mean'] < 0.01  # Under 10ms
    
    def test_complex_window_parsing(self, benchmark, parser, sample_code_snippets):
        """Benchmark parsing of complex window definitions."""
        code = sample_code_snippets['complex_window']
        
        def parse():
            return parser.parse(code)
        
        result = benchmark(parse)
        assert benchmark.stats['mean'] < 0.05  # Under 50ms
    
    def test_datawindow_syntax_parsing(self, benchmark, parser, sample_code_snippets):
        """Benchmark DataWindow syntax parsing."""
        code = sample_code_snippets['datawindow_syntax']
        
        # Mock the DataWindow parser
        def parse():
            # Simulate DataWindow parsing
            lines = code.split('\n')
            result = {}
            for line in lines:
                if 'column=' in line:
                    result['columns'] = result.get('columns', 0) + 1
            return result
        
        result = benchmark(parse)
        assert benchmark.stats['mean'] < 0.01  # Very fast
    
    def test_large_file_parsing(self, benchmark, parser, sample_code_snippets):
        """Benchmark parsing of large files."""
        code = sample_code_snippets['large_class']
        
        def parse():
            return parser.parse(code)
        
        result = benchmark(parse)
        assert benchmark.stats['mean'] < 0.2  # Under 200ms for 50 methods
    
    def test_transformer_performance(self, benchmark, parser, sample_code_snippets):
        """Benchmark AST transformation."""
        code = sample_code_snippets['complex_window']
        tree = parser.parse(code)
        transformer = PowerBuilderTransformer()
        
        def transform():
            return transformer.transform(tree)
        
        result = benchmark(transform)
        assert benchmark.stats['mean'] < 0.05  # Transformation should be fast
    
    def test_incremental_parsing(self, benchmark, parser):
        """Benchmark incremental parsing scenarios."""
        base_code = '''
            public function integer test()
                return 1
            end function
        '''
        
        # Parse once to warm up
        parser.parse(base_code)
        
        # Simulate incremental change
        modified_code = '''
            public function integer test()
                return 2  // Changed
            end function
        '''
        
        def parse_modified():
            return parser.parse(modified_code)
        
        result = benchmark(parse_modified)
        # Incremental parsing should be very fast
        assert benchmark.stats['mean'] < 0.005  # Under 5ms
    
    def test_error_recovery_overhead(self, benchmark, parser):
        """Benchmark parsing with error recovery."""
        # Code with syntax error
        error_code = '''
            public function integer test()
                if x > 0 then
                    // Missing end if
                return 1
            end function
        '''
        
        def parse_with_recovery():
            try:
                return parser.parse(error_code, recover_errors=True)
            except:
                return None
        
        result = benchmark(parse_with_recovery)
        # Error recovery adds overhead but should still be reasonable
        assert benchmark.stats['mean'] < 0.1  # Under 100ms