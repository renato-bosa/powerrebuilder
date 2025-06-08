# SIME-Finch Project Architecture (Mermaid Diagrams)

---

## High-Level Pipeline

```mermaid
flowchart TD
    A[Extract PBL/PBD] --> B[Parse Extracted Source]
    B --> C[Decompile PCode]
    C --> D[Generate Backend/Frontend Code]
```

---

## extract/pbd_core

```mermaid
classDiagram
    class Library {
        +extract_all()
        +__getitem__()
        +context manager
    }
    class PbdObject {
        +raw_text_content
        +raw_pcode
        +inflate_datawindow()
        +extract_resources()
    }
    Library "1" --> "*" PbdObject : contains
```

---

## extract/pbd_io

```mermaid
classDiagram
    class file_operations
    class resource_utils
    class pe_scanner
    class scanner
    class utils
    class progress
    file_operations <.. resource_utils : uses
    scanner <.. pe_scanner : uses
    progress <.. utils : uses
```

---

## extract/pbd_cli

```mermaid
classDiagram
    class orchestrator {
        +extract_pbls()
    }
```

---

## parse/visitors

```mermaid
classDiagram
    class PowerBuilderFamixModelGenerator {
        +define_classes()
        +define_traits()
        +define_hierarchy()
        +define_properties()
        +define_relations()
        +generate()
    }
    PowerBuilderFamixModelGenerator --> FamixBuilder
```

---

## parse/grammar

```mermaid
flowchart TD
    A[powerbuilder.lark] --> B[powerbuilder_core.lark]
    A --> C[datawindow.lark]
    A --> D[sql.lark]
```

---

## model/ast

```mermaid
classDiagram
    class ASTNode
    class Expression
    class Statement
    class Function
    ASTNode <|-- Expression
    ASTNode <|-- Statement
    Statement <|-- Function
```

---

## model/attribute

```mermaid
classDiagram
    class Attribute
    class AttributeAccess
    AttributeAccess --> Attribute
```

---

## model/datawindow

```mermaid
classDiagram
    class DataWindow
    class Column
    class ComputeExpression
    DataWindow --> Column
    DataWindow --> ComputeExpression
```

---

## model/transaction

```mermaid
classDiagram
    class Transaction
    class Savepoint
    class TransactionOperation
    Transaction --> Savepoint
    Transaction --> TransactionOperation
```

---

## model/library

```mermaid
classDiagram
    class Library
    class Import
    class Export
    Library --> Import
    Library --> Export
```

---

## model/ui

```mermaid
classDiagram
    class Window
    class Control
    class Menu
    Window --> Control
    Window --> Menu
```

---

## model/source

```mermaid
classDiagram
    class SourceFile
    class SourcePosition
    SourceFile --> SourcePosition
```

---

## model/utils

```mermaid
classDiagram
    class Scope
    class Validator
    class TypeSystem
    Scope <.. Validator : uses
    Validator <.. TypeSystem : uses
```

---

## model/analysis

```mermaid
classDiagram
    class DependencyGraph
    class CallGraph
    class UIFlowGraph
    DependencyGraph --> CallGraph
    CallGraph --> UIFlowGraph
```

---

## model/pb_datawindow

```mermaid
classDiagram
    class PBDataWindow
    class PBColumn
    class PBTable
    PBDataWindow --> PBColumn
    PBDataWindow --> PBTable
```

---

## model/pb_transaction

```mermaid
classDiagram
    class PBTransaction
    class PBSavepoint
    class PBTransactionStatement
    PBTransaction --> PBSavepoint
    PBTransaction --> PBTransactionStatement
```

---

## decompile

```mermaid
classDiagram
    class PowerBuilderDecompiler {
        +decompile_pbd()
    }
    class StructuredDecompiler
    class PCodeDecoder
    PowerBuilderDecompiler --> StructuredDecompiler
    StructuredDecompiler --> PCodeDecoder
```

---

## generate

```mermaid
classDiagram
    class PythonGenerator
    class SQLGenerator
    class APIGenerator
    class ReactGenerator
    PythonGenerator --> Model
    SQLGenerator --> Model
    APIGenerator --> Model
    ReactGenerator --> Model
```

---

# End of Diagrams
