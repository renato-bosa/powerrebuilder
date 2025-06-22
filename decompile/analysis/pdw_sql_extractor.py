"""PDW (Compiled PowerBuilder DataWindow) SQL and metadata extraction.

This module extracts SQL statements and metadata from compiled PDW files.
While we cannot recover the full DataWindow source code, we can extract
valuable information like SQL queries, table names, and column definitions.
"""

import logging
import re
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class PDWSQLExtractor:
    """Extract SQL and metadata from compiled PDW files."""
    
    @staticmethod
    def extract_sql_from_pdw(data: bytes, object_name: str = "") -> str | None:

        
        """Extract SQL statement from compiled PDW data.
        
        Args:
            data: Raw PDW file data
            object_name: Name of the DataWindow object for logging
            
        Returns:
            Extracted SQL statement or None
        """
        logger.info(f"Attempting SQL extraction from PDW file: {object_name}")
        
        # Try multiple extraction strategies
        sql = None
        
        # Strategy 1: Look for PBSELECT patterns
        sql = PDWSQLExtractor._extract_pbselect_sql(data)
        if sql:
            logger.info(f"Found SQL via PBSELECT pattern in {object_name}")
            return sql
            
        # Strategy 2: Look for standard SQL keywords
        sql = PDWSQLExtractor._extract_standard_sql(data)
        if sql:
            logger.info(f"Found SQL via standard patterns in {object_name}")
            return sql
            
        # Strategy 3: Try UTF-16 LE encoding
        sql = PDWSQLExtractor._extract_utf16_sql(data)
        if sql:
            logger.info(f"Found SQL via UTF-16 LE in {object_name}")
            return sql
            
        logger.warning(f"Could not extract SQL from PDW file: {object_name}")
        return None
    
    @staticmethod
    def _extract_pbselect_sql(data: bytes) -> str | None:

        
        """Extract SQL from PBSELECT format."""
        # Look for PBSELECT marker
        pbselect_idx = data.find(b'PBSELECT')
        if pbselect_idx < 0:
            pbselect_idx = data.find(b'P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00')
            
        if pbselect_idx >= 0:
            # Extract the SQL portion
            # PBSELECT statements are usually followed by the actual SQL
            start = pbselect_idx
            
            # Find the end - usually marked by various patterns
            end_markers = [b'\x00\x00\x00', b'release', b'datawindow', b'table(']
            end = len(data)
            
            for marker in end_markers:
                marker_idx = data.find(marker, start + 20)
                if marker_idx > 0 and marker_idx < end:
                    end = marker_idx
                    
            sql_bytes = data[start:end]
            
            # Clean and decode
            try:
                # Remove null bytes and decode
                sql_bytes = sql_bytes.replace(b'\x00', b'')
                sql = sql_bytes.decode('ascii', errors='ignore')
                
                # Clean up the SQL
                sql = PDWSQLExtractor._clean_sql(sql)
                if PDWSQLExtractor._is_valid_sql(sql):
                    return sql
            except Exception as e:
                logger.debug(f"Error decoding PBSELECT SQL: {e}")
                
        return None
    
    @staticmethod
    def _extract_standard_sql(data: bytes) -> str | None:

        
        """Extract SQL using standard SQL keyword patterns."""
        # Look for SELECT statement
        select_patterns = [
            b'SELECT ', b'select ', b'S\x00E\x00L\x00E\x00C\x00T\x00 \x00', # UTF-16 LE
        ]
        
        for pattern in select_patterns:
            idx = data.find(pattern)
            if idx >= 0:
                # Find the end of the SQL statement
                end = len(data)
                
                # Look for common end markers
                end_patterns = [
                    b'ORDER BY', b'order by', b'GROUP BY', b'group by', b'', b'\x00\x00\x00', b'~t', b'~n'
                ]
                
                # Special handling for ORDER BY/GROUP BY - they're part of the SQL
                sql_end_idx = end
                for end_pattern in end_patterns:
                    end_idx = data.find(end_pattern, idx + len(pattern))
                    if end_idx > 0:
                        # If it's ORDER BY or GROUP BY, find the real end after it
                        if end_pattern in [b'ORDER BY', b'order by', b'GROUP BY', b'group by']:
                            # Look for the end after the clause
                            real_end = PDWSQLExtractor._find_sql_end_after_clause(data, end_idx)
                            if real_end > end_idx:
                                sql_end_idx = min(sql_end_idx, real_end)
                        else:
                            sql_end_idx = min(sql_end_idx, end_idx)
                
                sql_bytes = data[idx:sql_end_idx]
                
                # Decode and clean
                try:
                    if b'\x00' in sql_bytes[:20]:  # UTF-16 LE
                        sql = sql_bytes.decode('utf-16-le', errors='ignore')
                    else:
                        sql = sql_bytes.decode('ascii', errors='ignore')
                    
                    sql = PDWSQLExtractor._clean_sql(sql)
                    if PDWSQLExtractor._is_valid_sql(sql):
                        return sql
                except Exception as e:
                    logger.debug(f"Error decoding standard SQL: {e}")
                    
        return None
    
    @staticmethod
    def _extract_utf16_sql(data: bytes) -> str | None:

        
        """Extract SQL from UTF-16 LE encoded data."""
        try:
            # Try to decode as UTF-16 LE
            text = data.decode('utf-16-le', errors='ignore')
            
            # Look for SQL patterns
            sql_match = re.search(
                r'(SELECT\s+[\s\S]+?(?:ORDER\s+BY[\s\S]+?)?(?:GROUP\s+BY[\s\S]+?)?(?:HAVING[\s\S]+?)?);?',
                text,
                re.IGNORECASE
            )
            
            if sql_match:
                sql = sql_match.group(1)
                sql = PDWSQLExtractor._clean_sql(sql)
                if PDWSQLExtractor._is_valid_sql(sql):
                    return sql
                    
        except Exception as e:
            logger.debug(f"Error extracting UTF-16 SQL: {e}")
            
        return None
    
    @staticmethod
    def _find_sql_end_after_clause(data: bytes, clause_start: int) -> int:

        
        """Find the end of SQL after ORDER BY or GROUP BY clause."""
        # Look for end markers after the clause
        search_start = clause_start + 8  # Skip past "ORDER BY" or "GROUP BY"
        
        end_markers = [
            b'\x00\x00\x00', b'~t', b'~n', b';',
            b'release', b'datawindow', b'table('
        ]
        
        min_end = len(data)
        for marker in end_markers:
            idx = data.find(marker, search_start)
            if idx > 0:
                min_end = min(min_end, idx)
                
        # Also look for the start of another SQL keyword that shouldn't be there
        invalid_keywords = [b'SELECT ', b'INSERT ', b'UPDATE ', b'DELETE ']
        for keyword in invalid_keywords:
            idx = data.find(keyword, search_start)
            if idx > 0:
                min_end = min(min_end, idx)
                
        return min_end
    
    @staticmethod
    def _clean_sql(sql: str) -> str:

        
        """Clean up extracted SQL."""
        # Remove common artifacts
        sql = sql.replace('PBSELECT', '').strip()
        sql = sql.replace('pbselect', '').strip()
        sql = re.sub(r'~[tn]', ' ', sql)  # Replace PowerBuilder newlines
        sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace
        sql = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sql)  # Remove control characters
        sql = sql.strip()
        
        # Remove trailing garbage
        sql = re.sub(r'(ORDER\s+BY[^;]+?)(?:[^\w\s,;().].*)?$', r'\1', sql, flags=re.IGNORECASE)
        
        return sql
    
    @staticmethod
    def _is_valid_sql(sql: str) -> bool:

        
        """Check if extracted text is valid SQL."""
        if not sql or len(sql) < 20:
            return False
            
        # Must start with SELECT
        if not sql.upper().startswith('SELECT'):
            return False
            
        # Must have FROM clause
        if 'FROM' not in sql.upper():
            return False
            
        # Should have reasonable characters
        if len(re.findall(r'[^\w\s.,;:()*=<>!\'"-]', sql)) > len(sql) * 0.1:
            return False
            
        return True
    
    @staticmethod
    def extract_metadata_from_pdw(data: bytes, object_name: str = "") -> dict[str, any]:

        
        """Extract metadata from PDW file.
        
        Returns dictionary with:
        - tables: List of table names
        - columns: List of column names
        - version: PDW version
        - has_sql: Whether SQL was found
        - can_decompile: Whether we can extract more than SQL
        """
        metadata = {
            'tables': [],
            'columns': [],
            'version': None,
            'has_sql': False,
            'can_decompile': False
        }
        
        # Get version from header
        header = data[:8]
        if header.startswith(b'PDW'):
            metadata['version'] = header.decode('ascii', errors='ignore').strip('\x00')
            metadata['can_decompile'] = True  # We can now decompile PDW files!
            
        # Extract SQL first
        sql = PDWSQLExtractor.extract_sql_from_pdw(data, object_name)
        if sql:
            metadata['has_sql'] = True
            metadata['sql'] = sql
            
            # Parse tables from SQL
            tables = PDWSQLExtractor._extract_tables_from_sql(sql)
            metadata['tables'] = list(tables)
            
            # Parse columns from SQL
            columns = PDWSQLExtractor._extract_columns_from_sql(sql)
            metadata['columns'] = list(columns)
            
        return metadata
    
    @staticmethod
    def _extract_tables_from_sql(sql: str) -> list[str]:

        
        """Extract table names from SQL."""
        tables = set()
        
        # Extract from FROM clause
        from_match = re.search(r'FROM\s+([^WHERE|GROUP|ORDER|HAVING]+)', sql, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1)
            # Split by commas and extract table names
            for part in from_clause.split(','):
                # Handle table aliases
                table_match = re.match(r'^\s*(\w+)(?:\s+\w+)?\s*$', part)
                if table_match:
                    tables.add(table_match.group(1))
                    
        # Also look for tables in JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.update(join_matches)
        
        return sorted(tables)
    
    @staticmethod
    def _extract_columns_from_sql(sql: str) -> list[str]:

        
        """Extract column names from SQL."""
        columns = set()
        
        # Extract from SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            
            # Parse column expressions
            # Handle table.column format
            col_matches = re.findall(r'(\w+)\.(\w+)', select_clause)
            for table, col in col_matches:
                columns.add(col)
                
            # Handle simple column names
            simple_matches = re.findall(r'(?:^|,)\s*(\w+)(?:\s+as\s+\w+)?(?:\s*,|\s*$)', select_clause, re.IGNORECASE)
            columns.update(simple_matches)
            
        # Extract from WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:GROUP|ORDER|HAVING|$)', sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            col_matches = re.findall(r'(\w+)\.(\w+)', where_clause)
            for table, col in col_matches:
                columns.add(col)
                
        # Remove SQL keywords that might be mistaken for columns
        sql_keywords = {'sum', 'count', 'max', 'min', 'avg', 'round', 'as', 'and', 'or', 'is', 'null'}
        columns = {col for col in columns if col.lower() not in sql_keywords}
        
        return sorted(columns)