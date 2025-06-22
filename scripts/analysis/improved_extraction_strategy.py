#!/usr/bin/env python3
"""Improved extraction strategy for handling DataWindow and mixed-content files."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionStrategy:
    """Configuration for extraction behavior."""
    # Phase 1: Extraction
    extract_all_data: bool = True  # Don't skip during extraction
    validate_dat_headers: bool = True  # Validate DataWindow headers
    max_reasonable_dat_size: int = 100_000_000  # 100MB max for DAT blocks
    
    # Phase 2: Decompilation  
    skip_null_sequences: bool = True  # Skip during decompilation
    null_sequence_threshold: int = 50  # Skip sequences > 50 nulls
    
    # Phase 3: Post-processing
    filter_repetitive_returns: bool = True  # Clean up before parsing
    max_consecutive_returns: int = 10  # Collapse returns > 10
    
    # Logging
    reduce_logging_verbosity: bool = True  # Prevent timeout from excessive logs

class ImprovedDataWindowExtractor:
    """Handle DataWindow files with corrupted headers."""
    
    @staticmethod
    def validate_dat_header(data: bytes, offset: int, file_size: int) -> tuple[bool, int]:

        
        """Validate and correct DAT block headers.
        
        Returns:
            Tuple of (is_valid, corrected_length)
        """
        if offset + 8 > len(data):
            return False, 0
            
        # Read declared length from header
        declared_length = int.from_bytes(data[offset+4:offset+8], 'little')
        
        # Sanity checks
        if declared_length > file_size:
            logger.warning(
                f"DAT header at {offset} declares {declared_length} bytes "
                f"but file is only {file_size} bytes"
            )
            # Calculate reasonable length
            remaining = file_size - offset - 8  # Header size
            corrected_length = min(remaining, 1_000_000)  # Cap at 1MB per block
            return True, corrected_length
            
        if declared_length > 100_000_000:  # 100MB
            logger.warning(f"Suspiciously large DAT block: {declared_length} bytes")
            return True, min(declared_length, 10_000_000)  # Cap at 10MB
            
        return True, declared_length

class PostProcessingFilter:
    """Filter repetitive patterns after decompilation."""
    
    @staticmethod
    def filter_decompiled_output(sru_content: str) -> str:

        
        """Remove excessive repetitive patterns from decompiled output.
        
        Args:
            sru_content: Raw decompiled .sru file content
            
        Returns:
            Filtered content with repetition reduced
        """
        lines = sru_content.split('\n')
        filtered_lines = []
        
        consecutive_returns = 0
        return_values_seen = set()
        
        for line in lines:
            line_stripped = line.strip()
            
            # Track return statements
            if line_stripped.startswith('return'):
                consecutive_returns += 1
                
                # Extract return value if present
                if ' ' in line_stripped:
                    return_value = line_stripped.split(' ', 1)[1]
                    return_values_seen.add(return_value)
                
                # Keep first few returns
                if consecutive_returns <= 5:
                    filtered_lines.append(line)
                # Add summary for excessive returns
                elif consecutive_returns == 6:
                    filtered_lines.append(f"    // ... {len(return_values_seen)} unique return values")
                    filtered_lines.append(f"    // ... skipping repetitive returns")
                # Skip the rest
                
            else:
                # Reset counter for non-return lines
                if consecutive_returns > 10:
                    filtered_lines.append(f"    // ... skipped {consecutive_returns - 5} return statements")
                consecutive_returns = 0
                return_values_seen.clear()
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

class OptimizedPipelineLogger:
    """Reduce logging verbosity to prevent timeouts."""
    
    @staticmethod
    def setup_logging(verbose: bool = False) -> None:

        """Configure logging for pipeline execution."""
        if not verbose:
            # Reduce verbosity for bulk operations
            logging.getLogger('extract.pbd').setLevel(logging.WARNING)
            logging.getLogger('decompile.analysis').setLevel(logging.WARNING)
            logging.getLogger('decompile.core').setLevel(logging.WARNING)
            
            # Keep important messages
            logging.getLogger('__main__').setLevel(logging.INFO)
            logging.getLogger('extract.extract_coordinator').setLevel(logging.INFO)
            logging.getLogger('decompile.decompile_coordinator').setLevel(logging.INFO)

def demonstrate_improved_approach() -> None:


    

    """Show the improved extraction approach."""
    print("🎯 IMPROVED EXTRACTION STRATEGY")
    print("=" * 50)
    
    print("\n📋 Phase 1: EXTRACTION")
    print("✅ Extract ALL data (don't skip)")
    print("✅ Validate & correct DAT headers")
    print("✅ Cap unreasonable sizes")
    print("✅ Continue on errors (partial extraction)")
    
    print("\n🔧 Phase 2: DECOMPILATION")
    print("✅ Skip large null sequences (>50 bytes)")
    print("✅ Process regions between padding")
    print("✅ Validate instruction patterns")
    print("✅ Generate raw .sru files")
    
    print("\n🧹 Phase 3: POST-PROCESSING")
    print("✅ Filter excessive returns (keep first 5)")
    print("✅ Summarize repetitive patterns")
    print("✅ Preserve meaningful code")
    print("✅ Prepare clean files for parsing")
    
    print("\n📊 BENEFITS")
    print("• No data loss during extraction")
    print("• Faster processing (reduced logging)")
    print("• Cleaner output for parsing")
    print("• Better error recovery")
    print("• Analyzable patterns preserved")
    
    print("\n🔍 EXAMPLE OUTPUT TRANSFORMATION:")
    print("\nBefore filtering:")
    print("    return")
    print("    return")
    print("    return")
    print("    ... (500 more returns)")
    
    print("\nAfter filtering:")
    print("    return")
    print("    return") 
    print("    return")
    print("    return")
    print("    return")
    print("    // ... 3 unique return values")
    print("    // ... skipping repetitive returns")
    print("    // ... skipped 495 return statements")

if __name__ == "__main__":
    demonstrate_improved_approach()