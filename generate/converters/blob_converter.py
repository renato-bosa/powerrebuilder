"""PowerBuilder blob/binary data type converter.

Handles conversion of PowerBuilder blob data types to appropriate Dart/Flutter
representations, including Base64 encoding, file handling, and image processing.
"""

import base64
import logging
from typing import Any, Dict, Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class BlobConverter:
    """Converts PowerBuilder blob data to Flutter/Dart representations."""
    
    def __init__(self):
        """Initialize the blob converter."""
        # Mime type detection for common formats
        self.mime_mappings = {
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
            b'BM': 'image/bmp',
            b'II\x2A\x00': 'image/tiff',
            b'MM\x00\x2A': 'image/tiff',
            b'%PDF': 'application/pdf',
            b'PK\x03\x04': 'application/zip',
            b'\x1F\x8B': 'application/gzip',
            b'Rar!': 'application/x-rar-compressed',
        }
        
        # Image formats that can be displayed directly in Flutter
        self.image_formats = {
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
        }
        
        # File size thresholds
        self.INLINE_THRESHOLD = 10 * 1024  # 10KB - inline small blobs
        self.MEMORY_THRESHOLD = 1024 * 1024  # 1MB - use memory for medium blobs
        # Larger blobs should use file storage
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(x.title() for x in snake_str.split('_'))
    
    def convert_blob(self, blob_data: bytes, 
                     field_name: str,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert PowerBuilder blob data to Flutter representation.
        
        Args:
            blob_data: Raw blob bytes
            field_name: Name of the blob field
            context: Optional context (e.g., DataWindow, column info)
            
        Returns:
            Dictionary with conversion info including:
            - dart_type: The Dart type to use
            - implementation: Code implementation
            - imports: Required imports
            - helper_code: Any helper methods needed
        """
        if not blob_data:
            return self._empty_blob_response()
        
        # Detect mime type
        mime_type = self._detect_mime_type(blob_data)
        blob_size = len(blob_data)
        
        # Determine best representation based on size and type
        if mime_type in self.image_formats:
            return self._convert_image_blob(blob_data, field_name, mime_type, blob_size)
        elif blob_size <= self.INLINE_THRESHOLD:
            return self._convert_inline_blob(blob_data, field_name)
        elif blob_size <= self.MEMORY_THRESHOLD:
            return self._convert_memory_blob(blob_data, field_name, mime_type)
        else:
            return self._convert_file_blob(blob_data, field_name, mime_type)
    
    def _empty_blob_response(self) -> Dict[str, Any]:
        """Return response for empty blob."""
        return {
            'dart_type': 'Uint8List?',
            'implementation': 'null',
            'imports': ['import \'dart:typed_data\';'],
            'helper_code': None
        }
    
    def _detect_mime_type(self, data: bytes) -> str:
        """Detect MIME type from blob data."""
        # Check magic bytes
        for magic, mime in self.mime_mappings.items():
            if data.startswith(magic):
                return mime
        
        # Default to octet-stream
        return 'application/octet-stream'
    
    def _convert_image_blob(self, data: bytes, field_name: str, 
                           mime_type: str, size: int) -> Dict[str, Any]:
        """Convert image blob for Flutter display."""
        if size <= self.INLINE_THRESHOLD:
            # Small image - use base64 inline
            base64_data = base64.b64encode(data).decode('utf-8')
            return {
                'dart_type': 'Widget',
                'implementation': f'Image.memory(base64Decode("{base64_data}"))',
                'imports': [
                    'import \'dart:convert\';',
                    'import \'dart:typed_data\';',
                    'import \'package:flutter/material.dart\';'
                ],
                'helper_code': None
            }
        else:
            # Larger image - use provider pattern
            return {
                'dart_type': 'ImageProvider',
                'implementation': f'MemoryImage(_{field_name}Data)',
                'imports': [
                    'import \'dart:typed_data\';',
                    'import \'package:flutter/material.dart\';'
                ],
                'helper_code': f'''
  late final Uint8List _{field_name}Data;
  
  Future<void> _load{self._to_pascal_case(field_name)}() async {{
    // Load from database or file
    _{field_name}Data = await repository.get{self._to_pascal_case(field_name)}Data();
  }}'''
            }
    
    def _convert_inline_blob(self, data: bytes, field_name: str) -> Dict[str, Any]:
        """Convert small blob as inline base64."""
        base64_data = base64.b64encode(data).decode('utf-8')
        return {
            'dart_type': 'Uint8List',
            'implementation': f'base64Decode("{base64_data}")',
            'imports': [
                'import \'dart:convert\';',
                'import \'dart:typed_data\';'
            ],
            'helper_code': None
        }
    
    def _convert_memory_blob(self, data: bytes, field_name: str, 
                            mime_type: str) -> Dict[str, Any]:
        """Convert medium blob for memory storage."""
        return {
            'dart_type': 'Uint8List',
            'implementation': f'_{field_name}Data',
            'imports': ['import \'dart:typed_data\';'],
            'helper_code': f'''
  late final Uint8List _{field_name}Data;
  
  Future<void> _load{self._to_pascal_case(field_name)}() async {{
    // Load blob data from repository
    _{field_name}Data = await repository.get{self._to_pascal_case(field_name)}();
  }}
  
  String get {self._to_camel_case(field_name)}MimeType => '{mime_type}';'''
        }
    
    def _convert_file_blob(self, data: bytes, field_name: str, 
                          mime_type: str) -> Dict[str, Any]:
        """Convert large blob for file storage."""
        return {
            'dart_type': 'File?',
            'implementation': f'_{field_name}File',
            'imports': [
                'import \'dart:io\';',
                'import \'dart:typed_data\';'
            ],
            'helper_code': f'''
  File? _{field_name}File;
  
  Future<void> _load{self._to_pascal_case(field_name)}() async {{
    // Load blob to temporary file
    final tempDir = await getTemporaryDirectory();
    final fileName = '{field_name}_${{DateTime.now().millisecondsSinceEpoch}}';
    _{field_name}File = File('${{tempDir.path}}/$fileName');
    
    // Stream blob data to file
    final data = await repository.get{self._to_pascal_case(field_name)}Stream();
    await _{field_name}File!.writeAsBytes(data);
  }}
  
  Future<void> _cleanup{self._to_pascal_case(field_name)}() async {{
    if (_{field_name}File != null && await _{field_name}File!.exists()) {{
      await _{field_name}File!.delete();
    }}
  }}
  
  String get {self._to_camel_case(field_name)}MimeType => '{mime_type}';'''
        }
    
    def generate_blob_repository_methods(self, blob_fields: List[Dict[str, Any]]) -> str:
        """Generate repository methods for blob handling.
        
        Args:
            blob_fields: List of blob field definitions
            
        Returns:
            Dart code for repository methods
        """
        methods = []
        
        for field in blob_fields:
            name = field['name']
            camel_name = self._to_camel_case(name)
            pascal_name = self._to_pascal_case(name)
            
            methods.append(f'''
  Future<Uint8List> get{pascal_name}() async {{
    final result = await database.query(
      tableName,
      columns: ['{name}'],
      where: 'id = ?',
      whereArgs: [id],
    );
    
    if (result.isNotEmpty && result.first['{name}'] != null) {{
      return result.first['{name}'] as Uint8List;
    }}
    return Uint8List(0);
  }}
  
  Stream<Uint8List> get{pascal_name}Stream() async* {{
    // For large blobs, stream in chunks
    const chunkSize = 1024 * 1024; // 1MB chunks
    final totalSize = await _get{pascal_name}Size();
    
    for (var offset = 0; offset < totalSize; offset += chunkSize) {{
      final chunk = await _get{pascal_name}Chunk(offset, chunkSize);
      yield chunk;
    }}
  }}''')
        
        return '\n'.join(methods)
    
    def generate_blob_widget(self, field_name: str, mime_type: Optional[str] = None) -> str:
        """Generate a Flutter widget for displaying blob data.
        
        Args:
            field_name: Name of the blob field
            mime_type: Optional MIME type hint
            
        Returns:
            Dart code for blob display widget
        """
        if mime_type and mime_type.startswith('image/'):
            return f'''
class {self._to_pascal_case(field_name)}Display extends StatelessWidget {{
  final Uint8List? data;
  final double? width;
  final double? height;
  final BoxFit fit;
  
  const {self._to_pascal_case(field_name)}Display({{
    Key? key,
    required this.data,
    this.width,
    this.height,
    this.fit = BoxFit.contain,
  }}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {{
    if (data == null || data!.isEmpty) {{
      return Container(
        width: width,
        height: height,
        color: Colors.grey[300],
        child: const Icon(Icons.image_not_supported),
      );
    }}
    
    return Image.memory(
      data!,
      width: width,
      height: height,
      fit: fit,
      errorBuilder: (context, error, stackTrace) {{
        return Container(
          width: width,
          height: height,
          color: Colors.grey[300],
          child: const Icon(Icons.broken_image),
        );
      }},
    );
  }}
}}'''
        else:
            # Generic blob display
            return f'''
class {self._to_pascal_case(field_name)}Display extends StatelessWidget {{
  final Uint8List? data;
  final String? mimeType;
  final VoidCallback? onDownload;
  
  const {self._to_pascal_case(field_name)}Display({{
    Key? key,
    required this.data,
    this.mimeType,
    this.onDownload,
  }}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {{
    if (data == null || data!.isEmpty) {{
      return const ListTile(
        leading: Icon(Icons.insert_drive_file),
        title: Text('No data'),
        subtitle: Text('Blob is empty'),
      );
    }}
    
    final sizeInKB = (data!.length / 1024).toStringAsFixed(2);
    
    return ListTile(
      leading: Icon(_getIconForMimeType(mimeType)),
      title: Text('{field_name}'),
      subtitle: Text('Size: $sizeInKB KB'),
      trailing: onDownload != null
          ? IconButton(
              icon: const Icon(Icons.download),
              onPressed: onDownload,
            )
          : null,
    );
  }}
  
  IconData _getIconForMimeType(String? mimeType) {{
    if (mimeType == null) return Icons.insert_drive_file;
    
    if (mimeType.startsWith('image/')) return Icons.image;
    if (mimeType.startsWith('video/')) return Icons.video_file;
    if (mimeType.startsWith('audio/')) return Icons.audio_file;
    if (mimeType.contains('pdf')) return Icons.picture_as_pdf;
    if (mimeType.contains('zip') || mimeType.contains('rar')) {{
      return Icons.folder_zip;
    }}
    
    return Icons.insert_drive_file;
  }}
}}'''
    
    def get_blob_handling_imports(self) -> List[str]:
        """Get all imports needed for blob handling."""
        return [
            "import 'dart:convert';",
            "import 'dart:io';",
            "import 'dart:typed_data';",
            "import 'package:flutter/material.dart';",
            "import 'package:path_provider/path_provider.dart';",
        ]