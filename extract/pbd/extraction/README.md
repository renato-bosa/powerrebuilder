# PBD Extraction Module

This module handles extraction of resources from PowerBuilder binary files (PBL/PBD).

## Architecture

### Core Components

1. **extractor.py** - Base PBL/PBD extraction logic
   - Handles file I/O and entry processing
   - Provides core extraction functions
   - Integrates with ResourceExtractionManager

2. **unified_resource_extractor.py** - Comprehensive resource extraction
   - Signature-based extraction for all resource types
   - Heuristic extraction for unknown patterns
   - Built-in validation and testing framework
   - Extensible through protocol-based registration

3. **resource_extraction_manager.py** - High-level coordinator
   - Multi-file extraction coordination
   - Global resource deduplication
   - Cache management
   - Performance monitoring and reporting

### Specialized Extractors

4. **enhanced_image_extractor.py** - Image-specific extraction
   - Comprehensive image format support
   - PowerBuilder-specific formats (PBM, PBI)
   - Image validation and metadata extraction

5. **string_extractor.py** - String resource extraction
   - Encoding detection and conversion
   - Language-specific string extraction
   - String pattern recognition

### Support Components

6. **resource_catalog.py** - Resource cataloging and indexing
7. **library.py** - PBL/PBD library handling

## Usage

For most use cases, use the ResourceExtractionManager which coordinates all extractors:

```python
manager = ResourceExtractionManager(output_path)
resources = manager.extract_from_file(pbd_file_path)
```

## Future Enhancements

- Corruption detection and recovery (from archived EnhancedExtractor)
- Additional resource type support
- Performance optimizations for large files