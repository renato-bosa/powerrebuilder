# Architectural Decision Records (ADRs)

## ADR-001: Pipeline Architecture

**Date:** December 2024  
**Status:** Accepted  
**Context:** Need to process PowerBuilder files through multiple transformation stages

**Decision:** Use a sequential pipeline architecture with file-based communication between stages

**Consequences:**
- ✅ Simple to understand and debug
- ✅ Each stage can be run independently
- ❌ Not memory efficient for large projects
- ❌ No streaming capability

**Future Consideration:** Migrate to stream-based pipeline in v2.0

---

## ADR-002: Parser Technology

**Date:** December 2024  
**Status:** Accepted  
**Context:** Need robust parser for PowerBuilder syntax

**Decision:** Use Lark parser with LALR(1) algorithm

**Rationale:**
- Pure Python (no C dependencies)
- Good error recovery
- Clean grammar syntax
- Active maintenance

**Alternatives Considered:**
- ANTLR: More powerful but Java dependency
- PLY: Less feature-rich
- Hand-written: Too error-prone

---

## ADR-003: AST Representation

**Date:** December 2024  
**Status:** Accepted  
**Context:** Need rich AST for accurate code transformation

**Decision:** Use dataclasses with inheritance hierarchy

**Benefits:**
- Type hints built-in
- Immutable by default option
- Clean syntax
- Good IDE support

**Trade-offs:**
- Python 3.7+ requirement
- Some boilerplate for visitors

---

## ADR-004: Code Generation Strategy

**Date:** December 2024  
**Status:** Accepted  
**Context:** Need flexible code generation for multiple targets

**Decision:** Use Jinja2 templates

**Rationale:**
- Separation of logic and presentation
- Designer-friendly
- Powerful control structures
- Wide adoption

**Implementation:**
```
AST → Context Building → Template Rendering → Code
```

---

## ADR-005: Error Handling Philosophy

**Date:** December 2024  
**Status:** Accepted  
**Context:** Dealing with corrupted/malformed PowerBuilder files

**Decision:** Graceful degradation with maximum recovery

**Principles:**
1. Never crash on bad input
2. Extract what's possible
3. Log all issues with context
4. Provide recovery mechanisms

**Example:**
```python
try:
    extract_perfect()
except:
    try:
        extract_with_recovery()
    except:
        extract_partial()
```

---

## ADR-006: Module Structure

**Date:** December 2024  
**Status:** Accepted  
**Context:** Organizing large codebase

**Decision:** Domain-driven module organization

**Structure:**
```
/extract     - Domain: PB binary format
/parse       - Domain: PB syntax
/model       - Domain: Abstract representation  
/decompile   - Domain: Bytecode analysis
/generate    - Domain: Target languages
```

**Benefits:**
- Clear boundaries
- Easy to navigate
- Minimizes coupling

---

## ADR-007: Testing Strategy

**Date:** December 2024  
**Status:** Proposed  
**Context:** Ensuring quality and reliability

**Decision:** Pyramid testing approach

**Layers:**
1. Unit tests (60%) - Fast, isolated
2. Integration tests (30%) - Module boundaries
3. E2E tests (10%) - Full pipeline

**Tools:**
- pytest for all tests
- hypothesis for property testing
- tox for multi-version testing

---

## ADR-008: Configuration Management

**Date:** December 2024  
**Status:** Accepted  
**Context:** Managing tool configuration

**Decision:** Use pyproject.toml as single source of truth

**Benefits:**
- Standard Python approach
- Tool integration (pip, build)
- Single file to manage

**Includes:**
- Dependencies
- Tool configs (ruff, mypy, pytest)
- Project metadata

---

## ADR-009: CLI Design

**Date:** December 2024  
**Status:** Accepted  
**Context:** User interface for the tool

**Decision:** Click-based CLI with subcommands

**Pattern:**
```bash
sime-finch extract [options]
sime-finch parse [options]
sime-finch decompile [options]
sime-finch generate [options]
sime-finch all [options]
```

**Benefits:**
- Intuitive structure
- Built-in help
- Easy testing
- Extensible

---

## ADR-010: Progress Tracking

**Date:** December 2024  
**Status:** Accepted  
**Context:** Long-running operations need feedback

**Decision:** Pluggable progress tracking with tqdm default

**Interface:**
```python
class BaseProgressTracker(ABC):
    @abstractmethod
    def update(self, amount=1): pass
```

**Implementations:**
- TqdmProgressTracker (default)
- SilentProgressTracker (for CI)
- Future: WebProgressTracker

---

## ADR-011: Opcode Definition Format

**Date:** December 2024  
**Status:** Accepted  
**Context:** Managing P-Code instruction definitions

**Decision:** YAML format with structured schema

**Example:**
```yaml
0xE4:
  category: "control_flow"
  variants:
    0x80:
      mnemonic: "JUMP"
      operands: ["target_offset"]
      stack_effect: "0 -> 0"
```

**Benefits:**
- Human readable
- Easy to extend
- Version control friendly

---

## ADR-012: Type System Design

**Date:** December 2024  
**Status:** Under Review  
**Context:** PowerBuilder has rich type system

**Decision:** Mirror PB types with Python classes

**Mapping:**
- PB Integer → PBIntegerType
- PB String → PBStringType  
- PB Array → PBArrayType
- PB Object → PBCustomType

**Future:** Add type inference engine

---

## ADR-013: Symbol Table Architecture

**Date:** December 2024  
**Status:** Proposed  
**Context:** Need to resolve symbols across scopes

**Decision:** Hierarchical symbol tables with lexical scoping

**Structure:**
```python
class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}
    
    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
```

---

## ADR-014: Memory Management

**Date:** December 2024  
**Status:** Proposed  
**Context:** Large PB projects can consume significant memory

**Decision:** Implement lazy loading and streaming where possible

**Strategies:**
1. Stream large files
2. Process in chunks
3. Clear AST nodes after use
4. Use weak references

---

## ADR-015: Plugin Architecture

**Date:** December 2024  
**Status:** Future  
**Context:** Extensibility for custom transformations

**Decision:** Hook-based plugin system

**Hooks:**
- pre_extract
- post_parse  
- pre_generate
- custom_transform

**Implementation:** TBD in v2.0

---

## Decision Log

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| 001 | Pipeline Architecture | Accepted | High |
| 002 | Lark Parser | Accepted | High |
| 003 | Dataclass AST | Accepted | Medium |
| 004 | Jinja2 Templates | Accepted | Medium |
| 005 | Graceful Degradation | Accepted | High |
| 006 | Domain Modules | Accepted | Medium |
| 007 | Testing Pyramid | Proposed | Medium |
| 008 | pyproject.toml | Accepted | Low |
| 009 | Click CLI | Accepted | Medium |
| 010 | Progress Tracking | Accepted | Low |
| 011 | YAML Opcodes | Accepted | Medium |
| 012 | Type System | Review | High |
| 013 | Symbol Tables | Proposed | High |
| 014 | Memory Management | Proposed | Medium |
| 015 | Plugins | Future | Low |

## Review Schedule

- Quarterly ADR review
- Update status as implemented
- Archive superseded decisions
- Document lessons learned