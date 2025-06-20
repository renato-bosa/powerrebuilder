# Actionable TODO List for SIME Finch

## 🔴 Critical - Fix Immediately

### Test Infrastructure
- [ ] Fix circular import: `extract/__init__.py` → `retry_operation`
- [ ] Fix test collection errors (5 failures preventing tests from running)
- [ ] Resolve import errors in test files
- [ ] Set up pytest to run without failures

### Missing Core Components  
- [ ] Implement `GrammarManager` class in `parse/grammar.py`
- [ ] Implement `PowerBuilderPreprocessor` methods:
  - [ ] `preprocess_file()`
  - [ ] `remove_comments()`
  - [ ] `handle_includes()`
  - [ ] `normalize_line_endings()`
- [ ] Fix `NotImplementedError` in `sql_transformer.py` line 765

## 🟠 High Priority - Core Functionality

### Parsing Improvements (Target: 70% success rate)
- [ ] Extend PowerBuilder grammar for:
  - [ ] Complex control structures (nested loops, goto)
  - [ ] Advanced expressions (array access, function calls)
  - [ ] Custom type definitions
  - [ ] Enum handling
- [ ] Implement type system components:
  - [ ] `PBType` class
  - [ ] `DataType` class  
  - [ ] `TypeChecker` class
  - [ ] `TypeInference` class
- [ ] Add error recovery for malformed syntax
- [ ] Complete AST-to-model conversion for all node types

### P-Code Decompilation
- [ ] Expand opcode coverage in `PCodeDecoderV2`:
  - [ ] Method call opcodes
  - [ ] Array operations
  - [ ] Object instantiation
  - [ ] Exception handling
- [ ] Integrate control flow graph with decompiler
- [ ] Generate actual method bodies instead of stubs
- [ ] Implement expression reconstruction from P-code

### Event/Method Conversion
- [ ] Wire up event handlers in generated code:
  - [ ] Map control names to handler methods
  - [ ] Generate event handler signatures
  - [ ] Implement event parameter passing
- [ ] Translate PowerScript to Dart/Python:
  - [ ] Control structures (if/else, loops)
  - [ ] Function calls
  - [ ] Variable declarations
  - [ ] Database operations

## 🟡 Medium Priority - Feature Completion

### DataWindow Enhancements
- [ ] Implement binary blob extraction from DataWindow columns
- [ ] Parse computed field expressions fully
- [ ] Extract validation rules and apply in generated code
- [ ] Handle all DataWindow presentation styles

### SQL Features
- [ ] Implement SQL optimization engine
- [ ] Add query formatting/beautification
- [ ] Support complex joins and subqueries
- [ ] Handle stored procedure calls

### Code Generation
- [ ] Implement unit test generation from PowerBuilder tests
- [ ] Add documentation generation from comments
- [ ] Create migration guide generation
- [ ] Support additional output formats (React Native, Vue.js)

## 🟢 Lower Priority - Polish & Enhancement

### Test Coverage (Target: 60%)
- [ ] Write tests for converters (currently 0%):
  - [ ] `UIConverter`
  - [ ] `TypeConverter`
  - [ ] `EventConverter`
  - [ ] `DataWindowConverter`
  - [ ] `ExpressionConverter`
- [ ] Add tests for parse module:
  - [ ] Transformers
  - [ ] Type resolution
  - [ ] Error recovery
- [ ] Create integration tests:
  - [ ] Full pipeline (extract → parse → generate)
  - [ ] Error scenarios
  - [ ] Large file handling

### Performance
- [ ] Profile and optimize extraction for large PBDs
- [ ] Implement parallel processing for multiple files
- [ ] Add caching for parsed results
- [ ] Optimize memory usage for large projects

### Documentation
- [ ] Write API documentation for all public modules
- [ ] Create user guide with examples
- [ ] Document architecture and design decisions
- [ ] Add inline code documentation

## 📊 Quick Wins (Can do immediately)

1. **Fix imports**: Simple import fixes to get tests running
2. **Remove obsolete TODOs**: Clean up completed or outdated TODO comments  
3. **Add progress bars**: Enhance user feedback during processing
4. **Fix simple bugs**: Like missing null checks, off-by-one errors
5. **Update dependencies**: Ensure all packages are current

## 🎯 Sprint Plan (2-week sprints)

### Sprint 1: Foundation
- Fix all test infrastructure issues
- Implement GrammarManager and Preprocessor
- Get baseline test coverage working
- Document current limitations

### Sprint 2: Parser Enhancement  
- Extend grammar for 50% more syntax coverage
- Implement type system
- Add error recovery
- Improve AST generation

### Sprint 3: Decompilation
- Expand P-code opcode support
- Generate method implementations
- Wire up event handlers
- Test with real PBD files

### Sprint 4: Testing & Polish
- Achieve 40% test coverage
- Fix discovered bugs
- Optimize performance
- Update documentation

## 📈 Success Metrics

- **Week 1**: Tests running, baseline coverage established
- **Week 2**: 50% parsing success rate
- **Week 4**: 70% parsing success rate, basic decompilation working
- **Week 6**: Event handlers connected, 40% test coverage
- **Week 8**: 60% test coverage, core features complete

## 🚨 Blockers to Address First

1. **Test infrastructure** - Nothing can be validated until tests run
2. **GrammarManager** - Multiple features depend on this
3. **Import errors** - Preventing module integration
4. **Type system** - Needed for proper code generation