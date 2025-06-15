# PowerBuilder to Flutter/Dart Conversion Rules

## Overview

This document defines the comprehensive mapping rules for converting PowerBuilder applications to Flutter/Dart. The conversion process preserves the business logic, data management, and UI structure while modernizing the technology stack.

## Table of Contents

1. [Type System Mapping](#type-system-mapping)
2. [Object Type Conversions](#object-type-conversions)
3. [UI Control Mappings](#ui-control-mappings)
4. [DataWindow Conversion](#datawindow-conversion)
5. [Event System Mapping](#event-system-mapping)
6. [Data Access Layer](#data-access-layer)
7. [State Management](#state-management)
8. [Navigation and Routing](#navigation-and-routing)
9. [Styling and Theming](#styling-and-theming)
10. [Best Practices](#best-practices)

---

## 1. Type System Mapping

### Basic Types

| PowerBuilder Type | Dart Type | Notes |
|------------------|-----------|-------|
| integer | int | 32-bit integer |
| long | int | Dart int is 64-bit |
| decimal(n,m) | double | Use decimal package for precision |
| real | double | Single precision float |
| double | double | Double precision float |
| string | String | Unicode by default |
| char(n) | String | Fixed length → String |
| boolean | bool | Direct mapping |
| date | DateTime | Date only |
| time | DateTime | Time only with date set to epoch |
| datetime | DateTime | Full timestamp |
| timestamp | DateTime | With timezone info |
| blob | Uint8List | Binary data |

### Complex Types

| PowerBuilder Type | Dart Type | Notes |
|------------------|-----------|-------|
| array[] | List<T> | Dynamic arrays |
| structure | class/freezed | Immutable data classes |
| any | dynamic | Use sparingly |
| powerobject | Object | Base class |
| nonvisualobject | Service class | Singleton or provider |
| datastore | Repository | Data access pattern |

---

## 2. Object Type Conversions

### Windows → Screens

PowerBuilder Window objects map to Flutter Screen widgets:

```dart
// PowerBuilder: w_customer_list
// Flutter: customer_list_screen.dart

class CustomerListScreen extends StatefulWidget {
  // Window parameters → constructor parameters
  final String? filterType;
  final int? customerId;
  
  // Window instance variables → State properties
  @override
  _CustomerListScreenState createState() => _CustomerListScreenState();
}
```

### User Objects → Widgets

PowerBuilder User Objects become reusable Flutter widgets:

```dart
// PowerBuilder: u_customer_detail
// Flutter: customer_detail_widget.dart

class CustomerDetailWidget extends StatelessWidget {
  // Object properties → widget properties
  final Customer customer;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
}
```

### Menu Objects → Navigation

PowerBuilder menus map to Flutter navigation patterns:

```dart
// PowerBuilder: m_main_menu
// Flutter: Drawer, BottomNavigationBar, or AppBar actions

Drawer(
  child: ListView(
    children: [
      ListTile(title: Text('Customers'), onTap: () => navigateToCustomers()),
      ListTile(title: Text('Orders'), onTap: () => navigateToOrders()),
    ],
  ),
)
```

---

## 3. UI Control Mappings

### Basic Controls

| PowerBuilder Control | Flutter Widget | Configuration |
|---------------------|----------------|---------------|
| StaticText | Text | Style with Theme |
| SingleLineEdit | TextField | With TextEditingController |
| MultiLineEdit | TextField | maxLines: null |
| CommandButton | ElevatedButton | With onPressed callback |
| CheckBox | Checkbox | With value binding |
| RadioButton | Radio | In RadioListTile |
| DropDownListBox | DropdownButton | With items list |
| ListBox | ListView | With ListTile items |
| ComboBox | Autocomplete | With options builder |
| Picture | Image | Asset/Network/File |
| PictureButton | IconButton | With icon |
| GroupBox | Container + Column | With decoration |
| Tab | TabBar + TabBarView | With TabController |

### Advanced Controls

| PowerBuilder Control | Flutter Widget | Implementation |
|---------------------|----------------|----------------|
| TreeView | TreeView (package) | Use flutter_treeview |
| ListView | ListView.builder | With custom item widgets |
| DataWindow | DataTable/Custom | See DataWindow section |
| Graph | charts_flutter | Map graph types |
| RichTextEdit | flutter_quill | Rich text editor |
| OLE | WebView/Platform | Platform-specific view |

---

## 4. DataWindow Conversion

DataWindows are the most complex PowerBuilder objects. They map to custom Flutter widgets with multiple presentation styles:

### Presentation Styles

| PowerBuilder Style | Flutter Implementation |
|-------------------|------------------------|
| Grid | DataTable with sorting/filtering |
| Freeform | Form with positioned fields |
| Tabular | ListView with custom rows |
| Group | Grouped ListView |
| Crosstab | Custom pivot table widget |
| Graph | charts_flutter widgets |
| Composite | Multiple embedded widgets |
| RichText | Formatted document view |

### DataWindow Components

```dart
class DataWindowWidget extends StatefulWidget {
  // Data source
  final Future<List<T>> Function()? retrieveData;
  
  // CRUD operations
  final Future<void> Function(T)? onInsert;
  final Future<void> Function(T)? onUpdate;
  final Future<void> Function(T)? onDelete;
  
  // Features
  final bool allowSort;
  final bool allowFilter;
  final bool allowExport;
  
  // Column definitions
  final List<DataWindowColumn> columns;
}
```

### Column Mapping

| DataWindow Column Property | Flutter DataColumn Property |
|---------------------------|----------------------------|
| name | DataColumn label |
| data_type | Type validation |
| format | Text formatting |
| width | Column width constraints |
| alignment | Text alignment |
| edit_style | Input widget type |
| validation | Form validation |

---

## 5. Event System Mapping

### Window Events

| PowerBuilder Event | Flutter Equivalent |
|-------------------|-------------------|
| open | initState() |
| close | dispose() |
| activate | onResume (with lifecycle) |
| deactivate | onPause (with lifecycle) |
| resize | LayoutBuilder |
| key | RawKeyboardListener |

### Control Events

| PowerBuilder Event | Flutter Callback |
|-------------------|------------------|
| clicked | onPressed/onTap |
| doubleclicked | onDoubleTap |
| getfocus | FocusNode.addListener |
| losefocus | FocusNode.addListener |
| modified | onChanged |
| itemchanged | onChanged (dropdown) |
| selectionchanged | onSelectionChanged |

### DataWindow Events

| PowerBuilder Event | Flutter Implementation |
|-------------------|------------------------|
| itemchanged | Cell edit callback |
| itemerror | Validation error handler |
| retrieverow | Stream builder update |
| updatestart | Pre-save validation |
| updateend | Post-save callback |
| rowfocuschanged | Selection callback |

---

## 6. Data Access Layer

### Transaction Objects → Repositories

PowerBuilder SQLCA maps to repository pattern:

```dart
abstract class CustomerRepository {
  Future<List<Customer>> findAll();
  Future<Customer?> findById(int id);
  Future<Customer> save(Customer customer);
  Future<void> delete(int id);
}

class SqlCustomerRepository implements CustomerRepository {
  final Database database;
  
  // SQL operations using database connection
}
```

### Embedded SQL → Repository Methods

| PowerBuilder SQL | Repository Method |
|-----------------|-------------------|
| SELECT ... INTO | findOne() |
| DECLARE cursor | findAll() with pagination |
| INSERT | create() |
| UPDATE | update() |
| DELETE | delete() |
| COMMIT | Transaction handling |

---

## 7. State Management

### PowerBuilder State → Flutter State

| PowerBuilder Concept | Flutter Pattern |
|---------------------|-----------------|
| Instance variables | State class properties |
| Shared variables | Static properties |
| Global variables | Provider/Riverpod |
| Window parameters | Constructor parameters |
| Message object | Navigation arguments |

### Recommended State Management

1. **Local State**: StatefulWidget for UI state
2. **Shared State**: Provider/Riverpod for app state
3. **Remote State**: Repository + FutureBuilder
4. **Complex State**: BLoC pattern for business logic

---

## 8. Navigation and Routing

### Window Operations

| PowerBuilder | Flutter Navigation |
|--------------|-------------------|
| Open(window) | Navigator.push() |
| OpenSheet() | showModalBottomSheet() |
| OpenWithParm() | Navigator.push with arguments |
| Close() | Navigator.pop() |
| CloseWithReturn() | Navigator.pop with result |

### Navigation Patterns

```dart
// Named routes
Navigator.pushNamed(context, '/customer/detail', arguments: customerId);

// Direct navigation
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => CustomerDetailScreen(customerId: id),
  ),
);

// Dialog
showDialog(
  context: context,
  builder: (context) => CustomerEditDialog(customer: customer),
);
```

---

## 9. Styling and Theming

### Visual Properties

| PowerBuilder Property | Flutter Theme Property |
|----------------------|------------------------|
| BackColor | backgroundColor |
| TextColor | foregroundColor |
| Font | TextStyle |
| Border | Border/BoxDecoration |
| Enabled | enabled property |
| Visible | Visibility widget |

### Design System

Create a centralized design system:

```dart
class AppDesignSystem {
  // Colors
  static const primaryColor = Color(0xFF2196F3);
  static const secondaryColor = Color(0xFF03DAC6);
  
  // Typography
  static const headingStyle = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
  );
  
  // Spacing
  static const defaultPadding = EdgeInsets.all(16.0);
  
  // Themes
  static final lightTheme = ThemeData(...);
  static final darkTheme = ThemeData(...);
}
```

---

## 10. Best Practices

### Code Organization

```
lib/
├── core/           # Core utilities, themes
├── data/           # Repositories, models
├── domain/         # Business logic
├── presentation/   # UI layer
│   ├── screens/    # Full screens
│   ├── widgets/    # Reusable widgets
│   └── providers/  # State management
└── main.dart       # App entry point
```

### Conversion Guidelines

1. **Preserve Business Logic**: Keep PowerBuilder business rules intact
2. **Modernize UI**: Use Material Design or Cupertino widgets
3. **Async Operations**: Convert to Future/Stream patterns
4. **Error Handling**: Use try-catch and Result types
5. **Testing**: Write unit and widget tests
6. **Documentation**: Document complex conversions

### Performance Optimization

1. Use `const` constructors where possible
2. Implement lazy loading for large datasets
3. Optimize images and assets
4. Use ListView.builder for long lists
5. Implement proper disposal of resources

### Migration Strategy

1. **Phase 1**: Core data models and repositories
2. **Phase 2**: Business logic services
3. **Phase 3**: UI screens and widgets
4. **Phase 4**: Integration and testing
5. **Phase 5**: Performance optimization

---

## Appendix: Code Templates

### Screen Template
```dart
class ${Name}Screen extends StatefulWidget {
  // Parameters from PowerBuilder window
  
  @override
  _${Name}ScreenState createState() => _${Name}ScreenState();
}

class _${Name}ScreenState extends State<${Name}Screen> {
  // Instance variables from PowerBuilder
  
  @override
  void initState() {
    super.initState();
    // Open event logic
  }
  
  @override
  Widget build(BuildContext context) {
    // Window controls layout
  }
  
  @override
  void dispose() {
    // Close event logic
    super.dispose();
  }
}
```

### Repository Template
```dart
abstract class ${Name}Repository {
  Future<List<${Model}>> findAll();
  Future<${Model}?> findById(int id);
  Future<${Model}> save(${Model} model);
  Future<void> delete(int id);
}
```

### Model Template
```dart
@freezed
class ${Name} with _$${Name} {
  const factory ${Name}({
    // Properties from PowerBuilder structure
  }) = _${Name};
  
  factory ${Name}.fromJson(Map<String, dynamic> json) =>
      _$${Name}FromJson(json);
}
```

---

This document serves as the authoritative guide for converting PowerBuilder applications to Flutter/Dart. It should be updated as new patterns and best practices emerge during the conversion process.