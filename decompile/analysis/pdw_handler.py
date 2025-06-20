"""Unified handler for PDW (Compiled PowerBuilder DataWindow) files.

This module provides a single interface for handling PDW files,
integrating detection, SQL extraction, and comprehensive decompilation.
"""

import logging
from typing import Optional, Union, Dict, Any

from decompile.analysis.pdw_detector import detect_pdw_format, log_pdw_warning, can_extract_from_pdw
from decompile.analysis.pdw_sql_extractor import PDWSQLExtractor
from decompile.analysis.pdw_comprehensive_extractor import PDWComprehensiveExtractor, PDWDataWindow
from decompile.analysis.pdw_blob_extractor import PDWBlobExtractor, ExtractedBlob

logger = logging.getLogger(__name__)


class PDWHandler:
    """Unified handler for PDW files."""
    
    @staticmethod
    def process_pdw_file(data: bytes, filename: str = "", 
                        extract_mode: str = "comprehensive",
                        extract_blobs: bool = True) -> Dict[str, Any]:
        """Process a PDW file and extract available information.
        
        Args:
            data: Raw PDW file data
            filename: Optional filename for logging
            extract_mode: "sql_only", "metadata", or "comprehensive"
            extract_blobs: Whether to extract binary blobs (default: True)
            
        Returns:
            Dictionary containing extracted information
        """
        result = {
            'is_pdw': False,
            'version': None,
            'sql': None,
            'datawindow': None,
            'blobs': [],
            'error': None
        }
        
        # Detect PDW format
        pdw_info = detect_pdw_format(data, filename)
        
        if not pdw_info.is_compiled:
            result['error'] = "Not a PDW file"
            return result
        
        result['is_pdw'] = True
        result['version'] = pdw_info.version
        
        # Log info about the file
        log_pdw_warning(filename, pdw_info)
        
        try:
            if extract_mode == "sql_only":
                # Extract just SQL
                sql = PDWSQLExtractor.extract_sql_from_pdw(data, filename)
                result['sql'] = sql
                
            elif extract_mode == "metadata":
                # Extract SQL and metadata
                metadata = PDWSQLExtractor.extract_metadata_from_pdw(data, filename)
                result.update(metadata)
                
            else:  # comprehensive
                # Full decompilation
                dw = PDWComprehensiveExtractor.decompile_pdw(data, filename)
                result['datawindow'] = dw
                result['sql'] = dw.sql
                
                # Generate source approximation
                result['source_approximation'] = dw.get_source_approximation()
                
                # Extract binary blobs if requested
                if extract_blobs:
                    try:
                        blobs = PDWBlobExtractor.extract_blobs(data, filename)
                        result['blobs'] = blobs
                        if blobs:
                            logger.info(f"Extracted {len(blobs)} binary blobs from {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to extract blobs from {filename}: {e}")
                
        except Exception as e:
            logger.error(f"Error processing PDW file {filename}: {e}")
            result['error'] = str(e)
            
        return result
    
    @staticmethod
    def can_handle_file(data: bytes) -> bool:
        """Check if this handler can process the given data."""
        pdw_info = detect_pdw_format(data)
        return pdw_info.is_compiled
    
    @staticmethod
    def extract_for_datawindow_pipeline(data: bytes, object_name: str) -> Optional[str]:
        """Extract DataWindow syntax for the decompile pipeline.
        
        This method is designed to integrate with the existing DataWindow extraction pipeline.
        
        Args:
            data: Raw PDW file data
            object_name: Name of the DataWindow object
            
        Returns:
            Reconstructed DataWindow source or None
        """
        result = PDWHandler.process_pdw_file(data, object_name, extract_mode="comprehensive")
        
        if result.get('error'):
            return None
            
        # Return the source approximation
        return result.get('source_approximation')
    
    @staticmethod
    def get_pdw_summary(data: bytes, filename: str = "") -> str:
        """Get a human-readable summary of PDW file contents."""
        result = PDWHandler.process_pdw_file(data, filename, extract_mode="comprehensive")
        
        if result.get('error'):
            return f"Error: {result['error']}"
        
        lines = []
        lines.append(f"PDW File Summary: {filename}")
        lines.append("=" * 60)
        
        if result.get('version'):
            lines.append(f"Version: {result['version']}")
            
        if result.get('datawindow'):
            dw = result['datawindow']
            
            if dw.sql:
                lines.append("\nSQL Query:")
                lines.append("-" * 40)
                # Truncate long SQL
                sql_preview = dw.sql[:200] + "..." if len(dw.sql) > 200 else dw.sql
                lines.append(sql_preview)
                
            if dw.tables:
                lines.append(f"\nTables: {', '.join(dw.tables)}")
                
            if dw.columns:
                lines.append(f"\nColumns ({len(dw.columns)}):")
                for col in dw.columns[:10]:  # First 10
                    lines.append(f"  - {col.name}")
                if len(dw.columns) > 10:
                    lines.append(f"  ... and {len(dw.columns) - 10} more")
                    
            if dw.properties:
                lines.append("\nProperties:")
                for key, value in list(dw.properties.items())[:5]:
                    lines.append(f"  {key}: {value}")
        
        if result.get('blobs'):
            blobs = result['blobs']
            lines.append(f"\nBinary Blobs ({len(blobs)}):")
            for blob in blobs[:5]:  # First 5
                lines.append(f"  - {blob.blob_type.name} at 0x{blob.offset:08X} ({blob.size} bytes)")
            if len(blobs) > 5:
                lines.append(f"  ... and {len(blobs) - 5} more")
                    
        return "\n".join(lines)
    
    @staticmethod
    def extract_and_save_blobs(data: bytes, filename: str, output_dir: str) -> Dict[int, str]:
        """Extract blobs from PDW file and save them to disk.
        
        Args:
            data: Raw PDW file data
            filename: PDW filename for logging
            output_dir: Directory to save extracted blobs
            
        Returns:
            Dictionary mapping blob index to saved file path
        """
        # Extract blobs
        blobs = PDWBlobExtractor.extract_blobs(data, filename)
        
        if not blobs:
            logger.info(f"No blobs found in {filename}")
            return {}
        
        # Get base name without extension
        import os
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Save blobs
        saved_files = PDWBlobExtractor.save_blobs(blobs, output_dir, base_name)
        
        return saved_files