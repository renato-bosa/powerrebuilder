# DataWindow Implementation Plan for Flutter/Dart

## Executive Summary

The PowerBuilder DataWindow is the most complex control to migrate, combining data grid, forms, reports, and database integration. This plan proposes a **hybrid approach**: deconstruct into reusable components while providing a high-level abstraction that preserves PowerBuilder semantics.

## Understanding the DataWindow

### What DataWindow Provides
1. **Multiple Presentation Styles**:
   - Grid (tabular data)
   - Freeform (single record form)
   - Tabular (grid with bands)
   - Group (grouped data with headers)
   - Crosstab (pivot table)
   - Graph (charts)
   - Label (for printing labels)
   - N-Up (multiple records per row)
   - OLE 2.0 (embedded objects)
   - RichText (formatted documents)

2. **Core Features**:
   - Direct database binding
   - Automatic CRUD operations
   - Built-in sorting and filtering
   - Computed fields with expressions
   - Validation rules
   - Conditional formatting
   - Print preview and export
   - Events for data manipulation

3. **Advanced Features**:
   - Master-detail relationships
   - Dropdown DataWindows
   - Nested/composite DataWindows
   - Dynamic DataWindow creation
   - External data sources
   - ShareData functionality

## Implementation Strategy: Hybrid Approach

### Level 1: Core Components (Deconstruction)

Break DataWindow into reusable Flutter components:

```dart
// 1. Data Provider Component
class DataWindowDataProvider<T> extends ChangeNotifier {
  List<T> _data = [];
  List<T> _filteredData = [];
  Map<String, SortDirection> _sorts = {};
  Map<String, dynamic> _filters = {};
  
  // CRUD operations
  Future<void> retrieve({Map<String, dynamic>? params});
  Future<bool> update(T item);
  Future<bool> insert(T item);
  Future<bool> delete(T item);
  
  // Data manipulation
  void sort(String column, SortDirection direction);
  void filter(String column, dynamic value);
  void clearFilters();
}

// 2. Presentation Components
abstract class DataWindowPresentation<T> extends StatelessWidget {
  final DataWindowDataProvider<T> dataProvider;
  final DataWindowDefinition definition;
}

class GridPresentation<T> extends DataWindowPresentation<T> {
  // DataTable-based grid view
}

class FreeformPresentation<T> extends DataWindowPresentation<T> {
  // Form-based single record view
}

class CrosstabPresentation<T> extends DataWindowPresentation<T> {
  // Pivot table view
}

// 3. Column Definition
class DataWindowColumn {
  final String name;
  final String dbName;
  final Type dataType;
  final String? displayFormat;
  final String? editFormat;
  final ValidationRule? validation;
  final String? computedExpression;
  final EditStyle editStyle;
  
  // Column behaviors
  bool get isComputed => computedExpression != null;
  bool get isUpdateable => !isComputed && editStyle != EditStyle.none;
}

// 4. Validation Engine
class ValidationEngine {
  bool validate(dynamic value, ValidationRule rule);
  String? getErrorMessage(ValidationRule rule);
}

// 5. Expression Engine
class ExpressionEngine {
  dynamic evaluate(String expression, Map<String, dynamic> context);
  bool evaluateCondition(String condition, Map<String, dynamic> context);
}

// 6. Event System
class DataWindowEventDispatcher {
  // PowerBuilder-compatible events
  Stream<ItemChangedEvent> get onItemChanged;
  Stream<RowFocusChangedEvent> get onRowFocusChanged;
  Stream<RetrieveStartEvent> get onRetrieveStart;
  Stream<RetrieveEndEvent> get onRetrieveEnd;
  Stream<UpdateStartEvent> get onUpdateStart;
  Stream<UpdateEndEvent> get onUpdateEnd;
}
```

### Level 2: High-Level DataWindow Widget (Abstraction)

Combine components into a PowerBuilder-compatible widget:

```dart
class DataWindow<T> extends StatefulWidget {
  // PowerBuilder-compatible properties
  final String dataObject;  // DataWindow definition name
  final Transaction? transaction;  // Database connection
  final DataWindowPresentationStyle presentationStyle;
  final bool allowInsert;
  final bool allowUpdate;
  final bool allowDelete;
  
  // Event handlers (PowerBuilder-compatible)
  final ItemChangedCallback? onItemChanged;
  final RowFocusChangedCallback? onRowFocusChanged;
  final RetrieveCallback? onRetrieveStart;
  final RetrieveCallback? onRetrieveEnd;
  
  // Methods (PowerBuilder-compatible)
  DataWindowController<T> get controller;
  
  const DataWindow({
    Key? key,
    required this.dataObject,
    this.transaction,
    this.presentationStyle = DataWindowPresentationStyle.grid,
    this.allowInsert = true,
    this.allowUpdate = true,
    this.allowDelete = true,
    // ... event handlers
  }) : super(key: key);
}

// Controller with PowerBuilder-compatible methods
class DataWindowController<T> {
  // Data retrieval
  Future<int> retrieve([List<dynamic>? args]);
  Future<int> retrieveByKey(dynamic key);
  
  // Data modification
  int insertRow(int row);
  int deleteRow(int row);
  ItemStatus getItemStatus(int row, String column);
  void setItem(int row, String column, dynamic value);
  dynamic getItem(int row, String column);
  
  // Navigation
  int getRow();
  void setRow(int row);
  void scrollToRow(int row);
  
  // Filtering and sorting
  void setFilter(String filter);
  void filter();
  void setSort(String sort);
  void sort();
  
  // Data sharing
  void shareData(DataWindowController other);
  void shareDataOff(DataWindowController other);
  
  // Export/Import
  Future<String> saveAs(SaveAsType type, {bool includeHeaders = true});
  Future<int> importFile(ImportFileType type, String filename);
  
  // Validation
  bool validate();
  List<ValidationError> getValidationErrors();
  
  // State management
  void reset();
  void resetUpdate();
  int update();
  
  // Computed fields
  dynamic compute(String expression, int row);
  
  // Dynamic modification
  void modify(String modString);
  String describe(String attribute);
}
```

### Level 3: DataWindow Definition System

PowerBuilder DataWindow definitions (.srd files) need conversion:

```dart
// DataWindow definition model
class DataWindowDefinition {
  final String name;
  final String? selectSql;
  final List<DataWindowColumn> columns;
  final Map<String, ComputedField> computedFields;
  final DataWindowPresentationStyle presentationStyle;
  final Map<String, dynamic> properties;
  
  // Runtime creation
  static DataWindowDefinition fromSRD(String srdContent);
  static DataWindowDefinition fromSQL(String sql);
  static DataWindowDefinition dynamic(List<ColumnDefinition> columns);
}

// Definition repository
class DataWindowRepository {
  static final _definitions = <String, DataWindowDefinition>{};
  
  static void register(String name, DataWindowDefinition definition);
  static DataWindowDefinition? get(String name);
  static DataWindowDefinition getOrThrow(String name);
}
```

### Level 4: Supporting Infrastructure

#### A. Database Transaction Management
```dart
abstract class Transaction {
  Future<List<Map<String, dynamic>>> select(String sql, [List<dynamic>? params]);
  Future<int> execute(String sql, [List<dynamic>? params]);
  Future<void> commit();
  Future<void> rollback();
  DBConnection get connection;
}
```

#### B. Edit Styles
```dart
// PowerBuilder edit styles
class EditStyleFactory {
  static Widget createEditWidget(EditStyle style, DataWindowColumn column) {
    switch (style.type) {
      case EditStyleType.edit:
        return TextField();
      case EditStyleType.dropdownListBox:
        return DropdownButton();
      case EditStyleType.checkbox:
        return Checkbox();
      case EditStyleType.radioButton:
        return Radio();
      case EditStyleType.dropdownDataWindow:
        return DropdownDataWindow();
      case EditStyleType.editMask:
        return MaskedTextField();
      // ... etc
    }
  }
}
```

#### C. Export/Import Handlers
```dart
abstract class DataWindowExporter {
  String export(List<Map<String, dynamic>> data, DataWindowDefinition definition);
}

class ExcelExporter extends DataWindowExporter {}
class CSVExporter extends DataWindowExporter {}
class XMLExporter extends DataWindowExporter {}
class JSONExporter extends DataWindowExporter {}
class PDFExporter extends DataWindowExporter {}
```

## Migration Path

### Phase 1: Core Implementation
1. Implement DataWindowDataProvider with basic CRUD
2. Create GridPresentation using DataTable
3. Build simple DataWindowDefinition loader
4. Implement basic column types and edit styles

### Phase 2: PowerBuilder Compatibility
1. Add all PowerBuilder-compatible methods to controller
2. Implement event system with correct signatures
3. Add computed field support with expression parser
4. Implement validation rules

### Phase 3: Advanced Features
1. Add all presentation styles
2. Implement ShareData functionality
3. Add dynamic DataWindow creation
4. Support nested/composite DataWindows

### Phase 4: Optimization
1. Virtual scrolling for large datasets
2. Lazy loading with pagination
3. Caching and state persistence
4. Performance profiling

## Usage Example

```dart
// In Flutter app
class CustomerListScreen extends StatefulWidget {
  @override
  State<CustomerListScreen> createState() => _CustomerListScreenState();
}

class _CustomerListScreenState extends State<CustomerListScreen> {
  late DataWindowController<Customer> dwController;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DataWindow<Customer>(
        dataObject: 'd_customer_list',  // PowerBuilder DataWindow name
        transaction: AppTransaction(),   // Database connection
        presentationStyle: DataWindowPresentationStyle.grid,
        onItemChanged: (row, column, data) {
          // Handle data changes
          if (column == 'credit_limit' && data > 10000) {
            // Business logic
          }
        },
        onRetrieveEnd: (rowCount) {
          // Post-retrieval logic
        },
      ),
    );
  }
  
  void _saveChanges() async {
    if (dwController.validate()) {
      int result = await dwController.update();
      if (result > 0) {
        // Success
      }
    }
  }
}
```

## Benefits of This Approach

1. **Preserves PowerBuilder Semantics**: Developers familiar with PowerBuilder will recognize the API
2. **Reusable Components**: Lower-level components can be used independently
3. **Extensible**: New presentation styles and features can be added
4. **Type-Safe**: Leverages Dart's type system
5. **Reactive**: Uses Flutter's reactive patterns
6. **Testable**: Components can be unit tested separately

## Challenges to Address

1. **Expression Parser**: Need robust parser for PowerBuilder expressions
2. **SQL Generation**: Dynamic SQL generation for updates/inserts
3. **Performance**: Large datasets need optimization
4. **State Management**: Complex state with nested data
5. **Event Order**: Must match PowerBuilder event firing order

## Conclusion

This hybrid approach provides the best of both worlds:
- **Deconstruction** allows reuse and Flutter-idiomatic code
- **Abstraction** preserves PowerBuilder compatibility and developer familiarity

The implementation can start simple (Phase 1) and progressively add PowerBuilder features, allowing for incremental migration of PowerBuilder applications.