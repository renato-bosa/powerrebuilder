# Python Syntax Error Analysis Report

Generated: 2025-07-23 17:43:54

Total files with errors: 21

## Summary

| File | Error Type | Line | Message |
|------|-----------|------|----------|
| decompile/analyzers/parser.py | SyntaxError | 46 | invalid syntax |
| decompile/analysis/control.py | SyntaxError | 161 | invalid syntax. Perhaps you forgot a comma? |
| decompile/reconstruction/expression.py | SyntaxError | 132 | invalid syntax |
| decompile/pcode/detector.py | SyntaxError | 14 | unmatched ')' |
| decompile/pcode/recovery.py | SyntaxError | 293 | invalid syntax |
| pcode/opcodes/variants.py | IndentationError | 426 | unexpected indent |
| parser/specialized/transactions.py | SyntaxError | 143 | invalid syntax |
| parser/specialized/types.py | SyntaxError | 84 | invalid syntax |
| parse/preprocessor/imports.py | SyntaxError | 71 | invalid syntax |
| model/types/powerbuilder.py | IndentationError | 24 | unexpected indent |
| model/types/validation.py | SyntaxError | 128 | invalid syntax |
| model/analysis/security.py | SyntaxError | 95 | invalid syntax |
| model/symbols/resolver.py | SyntaxError | 87 | invalid syntax |
| model/services/ast_processor.py | SyntaxError | 36 | invalid syntax |
| model/services/model_persistence.py | SyntaxError | 66 | invalid syntax |
| model/entities/method_call.py | IndentationError | 40 | unexpected indent |
| extract/utils/encoding.py | SyntaxError | 377 | invalid syntax |
| extract/components/validator.py | SyntaxError | 143 | invalid syntax |
| extract/components/recovery.py | SyntaxError | 76 | invalid syntax |
| extract/components/resources.py | SyntaxError | 91 | unmatched ')' |
| extract/components/statistics.py | SyntaxError | 83 | unmatched ')' |

## Detailed Analysis

### 1. src/decompile/analyzers/parser.py

**Error:** invalid syntax (line 46)

**Context:**
```python
      42:         for section in self.pcode_sections:
      43:             # Extract data for this specific section
      44:             if hasattr(section, "data") and section.data:
      45:                 pcode_chunks.append(section.data)
>>>   46:                 elif self.pcode_data and section.offset >= 0 and section.length > 0:
      47:                     # Extract from the full P-code data based on relative offsets
      48:                     rel_offset = section.offset - self.pcode_sections[0].offset
      49:                     chunk = self.pcode_data[rel_offset : rel_offset + section.length]
      50:                     pcode_chunks.append(chunk)
      51: 
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 2. src/decompile/analysis/control.py

**Error:** invalid syntax. Perhaps you forgot a comma? (line 161)

**Context:**
```python
     157:                     self.current_function.is_complete = True
     158: 
     159:                     # Start new function
     160:                     self.current_function = FunctionBoundary(
>>>  161:                     start_addr=inst.address, name=self._extract_function_name(inst)
     162: 
     163:                     self.function_boundaries.append(self.current_function)
     164:                     consecutive_returns = 0
     165:                     logger.debug("Function start detected at 0x%04X", inst.address)
     166: 
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 3. src/decompile/reconstruction/expression.py

**Error:** invalid syntax (line 132)

**Context:**
```python
     128:                             try:
     129:                                 statement = self._emulate_instruction(inst)
     130:                                 if statement:
     131:                                     block.statements.append(statement)
>>>  132:                                     except (IndexError, KeyError) as e:
     133:                                         # Handle common errors gracefully
     134:                                         logger.warning(
     135:                                         "Stack or lookup error emulating %s at %04X: %s", inst.opcode_name, inst.address, e
     136:                                         )
     137:                                         # Try to generate a meaningful comment instead of failing
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 4. src/decompile/pcode/detector.py

**Error:** unmatched ')' (line 14)

**Context:**
```python
      10: logger = logging.getLogger(__name__)
      11: 
      12: """Information about a single P-code section."""
      13: 
>>>   14: confidence: float = 0.0) -> None:
      15:     self.offset = offset
      16:     self.length = length
      17:     self.confidence = confidence  # 0.0 to 1.0
      18: 
      19:     return f"PCodeSection(offset = 0x{
```

**Suggestions:**
Unmatched closing parenthesis - check for:
  - Missing opening parenthesis
  - Extra closing parenthesis
  - Incomplete function/method definition above

---

### 5. src/decompile/pcode/recovery.py

**Error:** invalid syntax (line 293)

**Context:**
```python
     289:                                             next_inst = instructions[i + 1]
     290: 
     291:                                             # Multiple consecutive returns
     292:                                             if curr.opcode_name == "RETURN" and next_inst.opcode_name == "RETURN":
>>>  293:                                                 if (:
     294:                                                     i + 2 < len(instructions)
     295:                                                     and instructions[i + 2].opcode_name == "RETURN"
     296:                                                     ):
     297:                                                         analysis["invalid_sequences"].append(
     298:                                                         {
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 6. src/decompile/pcode/opcodes/variants.py

**Error:** unexpected indent (line 426)

**Context:**
```python
     422:                                                             values.append("TYPE_4")
     423:                                                         elif low_nibble == 0x09:
     424: 
     425:                                                             values.append("TYPE_9")
>>>  426:                                                                 elif low_nibble == 0x0E:
     427:                                                                     values.append("TYPE_E")
     428:                                                                     elif low_nibble == 0x0F:
     429:                                                                         values.append(
     430:                                                                         "TYPE_F")
     431: 
```

**Suggestions:**
Unexpected indentation - check for:
  - Mixed tabs and spaces
  - Incorrect indentation level
  - Missing or extra indentation
  - Current line has 64 spaces of indentation
  - Previous code line has 60 spaces

---

### 7. src/parse/parser/specialized/transactions.py

**Error:** invalid syntax (line 143)

**Context:**
```python
     139:                                             if len(parts) > 1:
     140:                                                 transaction_part = parts[1].strip()
     141:                                                 if ";" in transaction_part:
     142:                                                     transaction_object = transaction_part.split(";")[0].strip().lower()
>>>  143:                                                     else:
     144:                                                         transaction_object = transaction_part.split()[0].strip().lower()
     145: 
     146:                                                         # Create the transaction object
     147:                                                         transaction = PBTransaction(transaction_object=transaction_object)
     148: 
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 8. src/parse/parser/specialized/types.py

**Error:** invalid syntax (line 84)

**Context:**
```python
      80:         for child in tree.children:
      81:             if isinstance(child, Token):
      82:                 if child.type == "IDENTIFIER" and name is None:
      83:                     name = str(child)
>>>   84:                     elif child.value.lower() == "global":
      85:                         is_global = True
      86:                         elif child.value.lower() == "enumerated":
      87:                             is_enumerated = True
      88: 
      89:                             if child.data == "from_clause":
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage
  - Unclosed string on line 84

---

### 9. src/parse/preprocessor/imports.py

**Error:** invalid syntax (line 71)

**Context:**
```python
      67: 
      68:     # Handle different node types
      69:     if isinstance(node, FunctionCall | PBFunctionCall | PBMethodCall):
      70:         self._handle_function_call(node, context)
>>>   71:         elif isinstance(node, PBConstructorCall):
      72:             self._handle_constructor_call(node, context)
      73:             elif isinstance(node, VariableDeclaration):
      74:                 self._handle_variable_declaration(node, context)
      75:                 elif hasattr(node, "data"):
      76:                     # Handle parser tree nodes
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 10. src/model/types/powerbuilder.py

**Error:** unexpected indent (line 24)

**Context:**
```python
      20: 
      21: @property
      22: def is_basic(self) -> bool:
      23:     """Check if this is a basic type."""
>>>   24:         return False
      25: 
      26: @property
      27: def is_custom(self) -> bool:
      28:     """Check if this is a custom type."""
      29:         return False
```

**Suggestions:**
Unexpected indentation - check for:
  - Mixed tabs and spaces
  - Incorrect indentation level
  - Missing or extra indentation
  - Current line has 8 spaces of indentation
  - Previous code line has 4 spaces

---

### 11. src/model/types/validation.py

**Error:** invalid syntax (line 128)

**Context:**
```python
     124:                     key = (type(value), value)
     125:                     if key in seen:
     126:                         return False
     127:                         seen.add(key)
>>>  128:                         else:
     129:                             # For unhashable types, use id() as a fallback
     130:                             key = id(value)
     131:                             if key in seen:
     132:                                 return False
     133:                                 seen.add(key)
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 12. src/model/analysis/security.py

**Error:** invalid syntax (line 95)

**Context:**
```python
      91:             if hasattr(node, "__dict__"):
      92:                 for attr_name, attr_value in node.__dict__.items():
      93:                     if isinstance(attr_value, PBNode):
      94:                         self._analyze_node(attr_value, source_file)
>>>   95:                         elif isinstance(attr_value, list):
      96:                             for item in attr_value:
      97:                                 if isinstance(item, PBNode):
      98:                                     self._analyze_node(
      99:                                     item, source_file)
     100: 
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 13. src/model/symbols/resolver.py

**Error:** invalid syntax (line 87)

**Context:**
```python
      83:                     if self._resolve_symbol_reference(reference):
      84:                         self.context.references.append(reference)
      85:                         if reference.target_module:
      86:                             module_info.dependencies.add(reference.target_module)
>>>   87:                             else:
      88:                                 self.context.unresolved_references.append(
      89:                                 reference)
      90: 
      91:                                 """Resolve a single symbol reference.
      92: 
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 14. src/model/services/ast_processor.py

**Error:** invalid syntax (line 36)

**Context:**
```python
      32:         # Process based on format
      33:         if 'ast' in ast_data:
      34:             # New format with metadata
      35:             model = self._process_structured_ast(file_path, ast_data)
>>>   36:             else:
      37:                 # Legacy format - just the AST
      38:                 model = self._process_legacy_ast(file_path, ast_data)
      39: 
      40:                 self._processed_files += 1
      41:                 return model
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 15. src/model/services/model_persistence.py

**Error:** invalid syntax (line 66)

**Context:**
```python
      62:                     if models:
      63:                         return models[0] if len(models) == 1 else {'models': models}
      64:                         return models[0] if len(models) == 1 else {'models': models}
      65:                         return {}
>>>   66:                         else:
      67:                             # Legacy format - raw model
      68:                             return data
      69: 
      70:                             logger.error("Failed to load model from %s: %s", file_path, e)
      71:                             return {}
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 16. src/model/entities/method_call.py

**Error:** unexpected indent (line 40)

**Context:**
```python
      36:     - "scope": Current scope for variable resolution
      37: 
      38:     bool: True if valid, False otherwise
      39:     """
>>>   40:     if not self.class_name and not self.is_dynamic:
      41:         return False
      42: 
      43:         return False
      44: 
      45:         # Validate arguments if we have type information
```

**Suggestions:**
Unexpected indentation - check for:
  - Mixed tabs and spaces
  - Incorrect indentation level
  - Missing or extra indentation
  - Current line has 4 spaces of indentation
  - Previous code line has 4 spaces

---

### 17. src/extract/utils/encoding.py

**Error:** invalid syntax (line 377)

**Context:**
```python
     373:                 self.domain_dict.update(learned_data.get("words", []))
     374:                 logger.info(
     375:                 f"Loaded {len(learned_data.get('words', []))} learned words"
     376:                 )
>>>  377:                 except Exception as e:
     378:                     logger.warning(
     379:                     "Failed to load learned vocabulary: %s", e)
     380: 
     381:                     """Initialize regex-based pattern fixes for common corruptions."""
     382:                     return [
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 18. src/extract/components/validator.py

**Error:** invalid syntax (line 143)

**Context:**
```python
     139:                                 # Validate each extracted file
     140:                                 for file_path in extracted_files:
     141:                                     if not self._validate_extracted_file(file_path):
     142:                                         result["corrupted_entries"].append(file_path.name)
>>>  143:                                         result["statistics"]["corrupted_count"] += 1                                            result["statistics"]["valid_count"] += 1
     144: 
     145:                                             # Update statistics
     146:                                             result["statistics"]["found_count"] = len(extracted_files)
     147: 
     148:                                             # Determine overall validity
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage
  - Unclosed string on line 143

---

### 19. src/extract/components/recovery.py

**Error:** invalid syntax (line 76)

**Context:**
```python
      72:         # Read file data
      73:         try:
      74:             with file_path.open("rb") as f:
      75:                 file_data = f.read()
>>>   76:                 except Exception as e:
      77:                     logger.error(
      78:                     "Failed to read file %s: %s", file_path, e)
      79:                     return {
      80: "success": False,
      81: "error": str(e),
```

**Suggestions:**
Invalid syntax - check for:
  - Missing colons after if/for/while/def/class
  - Missing commas in lists/tuples/dicts
  - Unclosed strings, brackets, or parentheses
  - Invalid operator usage

---

### 20. src/extract/components/resources.py

**Error:** unmatched ')' (line 91)

**Context:**
```python
      87:                         )
      88: 
      89:                         extracted_paths = []
      90: 
>>>   91:                         found_resources):
      92:                             # Generate output filename
      93:                             filename = self._generate_resource_filename(
      94:                             file_path.stem, resource_type, i, offset
      95:                             )
      96:                             output_path = output_dir / filename
```

**Suggestions:**
Unmatched closing parenthesis - check for:
  - Missing opening parenthesis
  - Extra closing parenthesis
  - Incomplete function/method definition above

---

### 21. src/extract/components/statistics.py

**Error:** unmatched ')' (line 83)

**Context:**
```python
      79:                                 self._stats["sizes"]["largest_entry"] = size
      80:                                 self._stats["sizes"]["largest_entry_name"] = entry_name
      81: 
      82:                                 self._stats["sizes"]["smallest_entry"] == 0
>>>   83:                                 or size < self._stats["sizes"]["smallest_entry"]):
      84:                                     self._stats["sizes"]["smallest_entry"] = size
      85:                                     self._stats["sizes"]["smallest_entry_name"] = entry_name
      86: 
      87:                                     # Add to current file details
      88:                                     if self._current_file and self._current_file in self._stats[:
```

**Suggestions:**
Unmatched closing parenthesis - check for:
  - Missing opening parenthesis
  - Extra closing parenthesis
  - Incomplete function/method definition above

---

## Manual Fix Instructions

1. **Backup files first:** Create backups before making changes
2. **Fix one file at a time:** Test after each fix
3. **Common fixes:**
   - Add missing colons after control statements
   - Fix indentation (use 4 spaces, not tabs)
   - Add 'pass' to empty code blocks
   - Close unclosed parentheses/brackets/quotes
   - Remove or complete incomplete code fragments

## Quick Fix Commands

```bash
# Check syntax of a specific file
python3 -m py_compile path/to/file.py

# Format with black (may fix some issues)
black --check path/to/file.py

# Use autopep8 for automatic fixes
autopep8 --in-place --aggressive path/to/file.py
```
