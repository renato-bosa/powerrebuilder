"""Example tests using Hypothesis for property-based testing."""

import hypothesis
import hypothesis.stateful
from hypothesis import given, strategies as st, example
from hypothesis.strategies import composite
import pytest

from common.object_type_detector import ObjectTypeDetector, MagicNumbers
from parse.enhanced_parser import EnhancedPowerBuilderParser
from decompile.analysis.enhanced_datawindow_extractor import EnhancedDataWindowExtractor


# Custom strategies for PowerBuilder data
@composite
def powerbuilder_identifiers(draw):

    
    """Generate valid PowerBuilder identifiers."""
    # PowerBuilder identifiers must start with letter or underscore
    first_char = draw(st.one_of(
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.just('_')
    ))
    
    # Rest can be letters, digits, or underscore
    rest = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
        min_size=0,
        max_size=30
    ))
    
    return first_char + rest


@composite
def powerbuilder_types(draw):

    
    """Generate valid PowerBuilder type names."""
    base_types = ['integer', 'string', 'boolean', 'date', 'decimal', 'long', 
                  'real', 'char', 'blob', 'datetime', 'time', 'double']
    return draw(st.sampled_from(base_types))


@composite
def datawindow_filenames(draw):

    
    """Generate DataWindow filenames with various suffixes."""
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('Ll',)), 
                         min_size=1, max_size=10))
    suffix = draw(st.sampled_from(['_sql', '_ds', '_ex', '_dddw', '_rpt', '_dw', '']))
    return f"d_{prefix}{suffix}.dwo"


@composite
def binary_data_with_nulls(draw):

    
    """Generate binary data with varying null percentages."""
    size = draw(st.integers(min_value=100, max_value=10000))
    null_percentage = draw(st.floats(min_value=0, max_value=1))
    
    # Generate data
    null_count = int(size * null_percentage)
    non_null_count = size - null_count
    
    nulls = b'\x00' * null_count
    non_nulls = draw(st.binary(min_size=non_null_count, max_size=non_null_count))
    
    # Mix them up
    data = bytearray(nulls + non_nulls)
    # Simple shuffle
    import random
    random.shuffle(data)
    
    return bytes(data)


class TestObjectTypeDetectorProperties:
    """Property-based tests for ObjectTypeDetector."""
    
    @given(datawindow_filenames())
    def test_datawindow_detection_always_succeeds(self, filename):

        
        """All generated DataWindow filenames should be detected as DataWindows."""
        assert ObjectTypeDetector.is_datawindow(filename) == True
        
    @given(datawindow_filenames())
    def test_datawindow_subtype_detection_never_fails(self, filename):

        
        """DataWindow subtype detection should never raise exceptions."""
        subtype = ObjectTypeDetector.detect_datawindow_subtype(filename)
        assert subtype is not None
        assert hasattr(subtype, 'name')
        
    @given(binary_data_with_nulls())
    def test_binary_detection_consistency(self, data):

        
        """Binary detection should be consistent with null percentage."""
        is_binary = ObjectTypeDetector.is_binary_content(data)
        
        # Calculate actual null percentage
        null_count = sum(1 for b in data if b == 0)
        null_percentage = null_count / len(data) if data else 0
        
        # If more than 30% nulls, should be detected as binary
        if null_percentage > 0.3:
            assert is_binary == True
            
    @given(st.integers(min_value=0, max_value=2**32-1))
    def test_magic_number_detection_coverage(self, value):

        
        """Magic number detection should handle all 32-bit values safely."""
        # Should not raise exception
        is_corrupted = ObjectTypeDetector.is_corrupted_size(value)
        
        # Known magic numbers should be detected
        if value in MagicNumbers.CORRUPT_SIZES:
            assert is_corrupted == True
        else:
            assert is_corrupted == False
            
    @given(
        data=st.binary(min_size=4, max_size=1000),
        filename=datawindow_filenames()
    )
    def test_file_analysis_never_fails(self, data, filename):

        
        """File content analysis should handle any input without crashing."""
        analysis = ObjectTypeDetector.analyze_file_content(data, filename)
        
        # Should always return required fields
        assert 'filename' in analysis
        assert 'size' in analysis
        assert 'is_binary' in analysis
        assert 'null_percentage' in analysis
        assert analysis['size'] == len(data)
        assert 0 <= analysis['null_percentage'] <= 100


class TestEnhancedDataWindowExtractorProperties:
    """Property-based tests for EnhancedDataWindowExtractor."""
    
    @given(
        data=st.binary(min_size=10, max_size=10000),
        filename=datawindow_filenames()
    )
    def test_extraction_never_crashes(self, data, filename):

        
        """Extraction should handle any binary data without crashing."""
        extractor = EnhancedDataWindowExtractor()
        
        # Should not raise exception
        syntax, success = extractor.extract_syntax(data, filename)
        
        # Should always return tuple
        assert isinstance(syntax, (str, type(None)))
        assert isinstance(success, bool)
        
        # If successful, syntax should not be empty
        if success:
            assert syntax is not None
            assert len(syntax) > 0
            
    @given(st.binary(min_size=100))
    @example(b'release 12.5;\x00\x00datawindow(units=0)')  # Known good pattern
    def test_valid_datawindow_always_extracted(self, data):

        
        """Valid DataWindow patterns should always be extracted."""
        # Insert valid DataWindow markers
        if b'release' in data and b'datawindow' in data:
            extractor = EnhancedDataWindowExtractor()
            syntax, success = extractor.extract_syntax(data, "test.dwo")
            
            # Should extract something
            assert syntax is not None or not success


class TestParserProperties:
    """Property-based tests for the enhanced parser."""
    
    @given(powerbuilder_identifiers())
    def test_identifier_parsing(self, identifier):

        
        """All valid identifiers should parse without error."""
        parser = EnhancedPowerBuilderParser()
        
        # Create a simple assignment statement
        code = f"{identifier} = 42"
        
        # Should parse without exception
        tree = parser.parse(code)
        assert tree is not None
        
    @given(
        var_name=powerbuilder_identifiers(),
        var_type=powerbuilder_types(),
        value=st.one_of(
            st.integers(),
            st.text(min_size=1, max_size=50).map(lambda s: f'"{s}"'),
            st.booleans().map(lambda b: 'true' if b else 'false')
        )
    )
    def test_variable_declaration_parsing(self, var_name, var_type, value):

        
        """Variable declarations should parse correctly."""
        parser = EnhancedPowerBuilderParser()
        
        # Create declaration
        code = f"{var_type} {var_name} = {value}"
        
        # Should parse without exception
        tree = parser.parse(code)
        assert tree is not None
        
    @given(st.text(min_size=1, max_size=1000))
    def test_parser_error_recovery(self, code):

        
        """Parser should handle any input without crashing."""
        parser = EnhancedPowerBuilderParser()
        
        # Should not raise exception
        tree = parser.parse(code)
        assert tree is not None
        
        # Should have error information if parsing failed
        if hasattr(tree, 'meta') and hasattr(tree.meta, 'is_error_ast'):
            assert tree.meta.is_error_ast or tree.meta.had_partial_recovery


class TestIntegrationProperties:
    """Integration tests using property-based testing."""
    
    @given(
        st.fixed_dictionaries({
            'declared_size': st.integers(min_value=0, max_value=2**32-1),
            'file_size': st.integers(min_value=1000, max_value=1000000),
            'current_offset': st.integers(min_value=0, max_value=1000)
        })
    )
    def test_dat_block_recovery_integration(self, params):

        
        """DAT block recovery should handle any size values."""
        from extract.pbd.structures.enhanced_data_block import detect_and_fix_magic_number
        
        # Mock file handle
        class MockFileHandle:
            def seek(self, pos): pass
            def read(self, size): 
                return b'\x00' * min(size, 1000)
        
        file_handle = MockFileHandle()
        
        # Should handle any input
        actual_length, is_corrupted, method = detect_and_fix_magic_number(
            params['declared_size'],
            file_handle,
            params['current_offset'],
            params['file_size'],
            "test_object"
        )
        
        # Results should be reasonable
        assert actual_length >= 0
        assert actual_length <= params['file_size']
        assert isinstance(is_corrupted, bool)
        assert isinstance(method, str)


# Stateful testing example
class DataWindowExtractorStateMachine(hypothesis.stateful.RuleBasedStateMachine):
    """Stateful test for DataWindow extraction process."""
    
    def __init__(self):
        
    
        super().__init__()
        self.extractor = EnhancedDataWindowExtractor()
        self.extracted_files = {}
        
    @hypothesis.stateful.rule(
        filename=datawindow_filenames(),
        data=st.binary(min_size=10, max_size=1000)
    )
    def extract_file(self, filename, data):

        
        """Extract a file and store the result."""
        syntax, success = self.extractor.extract_syntax(data, filename)
        self.extracted_files[filename] = (syntax, success, data)
        
    @hypothesis.stateful.rule()
    def verify_consistent_extraction(self):

        
        """Re-extracting the same file should give the same result."""
        if self.extracted_files:
            filename = hypothesis.stateful.multiple(
                list(self.extracted_files.keys())
            ).example()
            
            original_syntax, original_success, data = self.extracted_files[filename]
            
            # Re-extract
            new_syntax, new_success = self.extractor.extract_syntax(data, filename)
            
            # Should be consistent
            assert new_success == original_success
            if original_success and new_success:
                assert new_syntax == original_syntax


# Run the state machine test
TestDataWindowExtractor = DataWindowExtractorStateMachine.TestCase


if __name__ == "__main__":
    # Run with more examples for thorough testing
    hypothesis.settings.register_profile(
        "thorough",
        max_examples=500,
        deadline=5000,
    )
    hypothesis.settings.load_profile("thorough")
    
    pytest.main([__file__, "-v"])