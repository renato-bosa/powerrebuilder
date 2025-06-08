# Code Consolidation Opportunities

## 1. Parser Consolidation

### Current Duplication
```python
# In parse_coordinator.py
class PowerBuilderQueryParser(PowerBuilderBaseParser):
    EXTENSIONS = ['.srq']
    # ... implementation

# In sql_parser.py  
class PowerBuilderSQLParser(PowerBuilderBaseParser):
    EXTENSIONS = ['.srq']
    # ... different implementation
```

### Consolidated Solution
```python
# In parse/parsers/sql.py
class SQLParser(PowerBuilderBaseParser):
    EXTENSIONS = ['.srq']
    
    def __init__(self):
        super().__init__()
        self.grammar = load_grammar('sql.lark')
        self.legacy_parser = LegacySQLParser()  # For fallback
    
    def parse(self, content: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        try:
            # Try Lark grammar first
            tree = self.grammar.parse(content)
            return self.transform(tree)
        except Exception:
            # Fall back to legacy parser
            return self.legacy_parser.parse(content)
```

## 2. Grammar Loading Standardization

### Current Pattern (Inconsistent)
```python
# Some parsers do this:
self.grammar_path = GRAMMAR_DIR / "powerbuilder_core.lark"
with open(self.grammar_path, 'r') as f:
    grammar_text = f.read()
self.parser = Lark(grammar_text, ...)

# Others do this:
self.parser = Lark.open(str(GRAMMAR_DIR / "sql.lark"), ...)

# And grammar.py has:
def load_grammar(grammar_name: str) -> Lark:
    # Standardized loading
```

### Standardized Solution
```python
# All parsers should use:
from parse.utils.grammar_loader import load_grammar

class SomeParser(PowerBuilderBaseParser):
    def __init__(self):
        super().__init__()
        self.parser = load_grammar('grammar_name.lark')
```

## 3. Error Handling Pattern

### Current Duplication
```python
# Pattern repeated in multiple parsers:
try:
    tree = self.parser.parse(content)
except UnexpectedInput as e:
    logger.error(f"Parse error at line {e.line}, column {e.column}")
    return {"error": str(e), "partial_tree": e.get_context(content)}
except Exception as e:
    logger.error(f"Unexpected parse error: {e}")
    return {"error": str(e)}
```

### Consolidated Solution
```python
# In base_parser.py
class PowerBuilderBaseParser:
    def safe_parse(self, content: str, parser: Lark) -> Dict[str, Any]:
        """Common error handling for all parsers."""
        try:
            tree = parser.parse(content)
            return {"success": True, "tree": tree}
        except UnexpectedInput as e:
            logger.error(f"Parse error at line {e.line}, column {e.column}")
            return {
                "success": False,
                "error": str(e),
                "line": e.line,
                "column": e.column,
                "context": e.get_context(content)
            }
        except Exception as e:
            logger.error(f"Unexpected parse error: {e}")
            return {"success": False, "error": str(e)}
```

## 4. File Processing Pattern

### Current Duplication
```python
# Pattern in multiple coordinators:
output_path = Path(output_path)
output_path.mkdir(parents=True, exist_ok=True)

for file_path in input_path.rglob(pattern):
    try:
        # Process file
        result = process(file_path)
        # Save result
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        continue
```

### Consolidated Solution
```python
# In common/utils/pipeline.py
class PipelineStage:
    """Base class for all pipeline stages."""
    
    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        pattern: str = "*",
        progress: bool = True
    ) -> Dict[str, Any]:
        """Common directory processing logic."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(input_dir.rglob(pattern))
        results = {"success": 0, "failed": 0, "errors": []}
        
        with self.get_progress_tracker(len(files), progress) as tracker:
            for file_path in files:
                try:
                    self.process_file(file_path, output_dir)
                    results["success"] += 1
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    results["failed"] += 1
                    results["errors"].append({"file": str(file_path), "error": str(e)})
                finally:
                    tracker.update()
        
        return results
    
    def process_file(self, input_file: Path, output_dir: Path) -> None:
        """Override in subclasses."""
        raise NotImplementedError
```

## 5. DataWindow Detection Consolidation

### Current Duplication
```python
# In extract/pbd_core/datawindow.py
DW_SIGNATURES = [
    b"release ",
    b"DWHD",
    b"HA$PBExportHeader$",
    # ...
]

# In decompile/analysis/datawindow_extractor.py
# Similar signature detection logic
```

### Consolidated Solution
```python
# In common/utils/datawindow_utils.py
class DataWindowDetector:
    """Shared DataWindow detection and validation logic."""
    
    SIGNATURES = {
        'binary': [b"DWHD", b"\x00\x00\x00\x00DWHD"],
        'text': [b"release ", b"HA$PBExportHeader$"],
        'markers': {
            'start': b"$PBExportComments$",
            'end': b"\x00\x00"
        }
    }
    
    @classmethod
    def detect_format(cls, data: bytes) -> Optional[str]:
        """Detect DataWindow format from data."""
        for format_type, signatures in cls.SIGNATURES.items():
            if format_type == 'markers':
                continue
            for sig in signatures:
                if sig in data[:1024]:  # Check first 1KB
                    return format_type
        return None
    
    @classmethod
    def validate_syntax(cls, syntax: str) -> bool:
        """Validate extracted DataWindow syntax."""
        required_keywords = ['release', 'datawindow', 'table']
        return all(keyword in syntax.lower() for keyword in required_keywords)
```

## 6. Progress Tracking Standardization

### Current Situation
- Only extract module uses progress tracking
- Other modules could benefit from it

### Standardized Solution
```python
# In common/utils/progress.py
def get_progress_tracker(total: int, description: str, silent: bool = False):
    """Factory for progress trackers."""
    if silent:
        return SilentProgressTracker(total, description)
    else:
        return TqdmProgressTracker(total, description)

# Use in all coordinators:
with get_progress_tracker(len(files), "Processing files") as progress:
    for file in files:
        # Process
        progress.update()
```

## 7. JSON Summary Generation

### Current Duplication
```python
# Similar pattern in parse_coordinator.py and main.py:
summary = {
    "processed_at": datetime.now().isoformat(),
    "input_directory": str(input_dir),
    "output_directory": str(output_dir),
    "files_processed": count,
    # ... more stats
}
```

### Consolidated Solution
```python
# In common/utils/reporting.py
class PipelineSummary:
    """Standardized summary generation for pipeline stages."""
    
    def __init__(self, stage_name: str, input_dir: Path, output_dir: Path):
        self.stage_name = stage_name
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.start_time = datetime.now()
        self.stats = defaultdict(int)
    
    def add_result(self, success: bool, file_path: Path = None, error: str = None):
        """Track processing results."""
        if success:
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
            if error:
                self.stats.setdefault('errors', []).append({
                    'file': str(file_path) if file_path else 'unknown',
                    'error': error
                })
    
    def generate(self) -> Dict[str, Any]:
        """Generate final summary."""
        return {
            "stage": self.stage_name,
            "processed_at": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir),
            "statistics": dict(self.stats)
        }
```

## Implementation Priority

1. **High Priority** (Fixes bugs/inconsistencies):
   - SQL parser consolidation
   - Parser hierarchy fixes
   - Grammar loading standardization

2. **Medium Priority** (Reduces duplication):
   - Error handling patterns
   - File processing patterns
   - Progress tracking

3. **Low Priority** (Nice to have):
   - DataWindow detection utilities
   - JSON summary generation
   - Common base classes

## Benefits

1. **Reduced Code**: ~30% less duplicate code
2. **Consistency**: Same patterns everywhere
3. **Maintainability**: Fix bugs in one place
4. **Testability**: Test common patterns once
5. **Extensibility**: Easy to add new file types/stages