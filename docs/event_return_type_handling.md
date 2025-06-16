# Event Return Type Handling Implementation

## Overview

This document describes the implementation of event return type handling in the EventConverter class, which properly converts PowerBuilder event return values to Flutter/Dart equivalents.

## PowerBuilder Events with Return Values

PowerBuilder uses integer return values to control behavior in certain events:

1. **CloseQuery Event** - Returns 0 to allow window close, 1 to prevent close
2. **ItemError Event** - Returns action codes (0=reject, 1=accept, 2=reject but allow focus change, 3=reject with no message)
3. **Key Events** - Returns 0 if key not processed, 1 if key was processed
4. **ItemChanging Event** - Returns 0 to accept change, 1 to reject change
5. **UpdateStart Event** - Returns 0 to allow update, 1 to prevent update
6. **RowFocusChanging Event** - Returns 0 to allow row change, 1 to prevent row change

## Implementation Details

### Event Mappings Enhanced

The `event_map` dictionary in EventConverter now includes:

- `return_type`: The expected return type (bool, int)
- `return_mapping`: Dictionary mapping PowerBuilder return values to Dart values

Example:
```python
"closequery": {
    "flutter_method": "onCloseQuery",
    "callback": True,
    "signature": "Future<bool> Function()",
    "return_type": "bool",
    "return_mapping": {
        0: "true",   # Allow close
        1: "false"   # Prevent close
    }
}
```

### Return Type Handling Methods

1. **`_get_callback_return_type()`** - Enhanced to handle:
   - `Future<bool>`
   - `Future<int>`
   - `bool`
   - `int`
   - `void`

2. **`_convert_event_body()`** - Enhanced to:
   - Accept return type and mapping parameters
   - Convert PowerBuilder return statements to mapped Dart values
   - Add default returns when needed
   - Preserve event-specific logic

3. **`_extract_return_value()`** - New method to:
   - Extract numeric return values from PowerBuilder return statements
   - Handle various formatting (whitespace, negative numbers)

4. **`_infer_return_type()`** - New method to:
   - Infer return type from event body when not explicitly specified
   - Detect int, bool, and String return types

### Event Registration

The `get_event_registration()` method now generates proper callback signatures:

- Simple callbacks: `onPressed: _handler`
- Value callbacks: `onChanged: (value) => _handler(value)`
- Multi-parameter callbacks: `onValidationError: (row, col, val, err) => _handler(row, col, val, err)`

### Validation Action Enum

Added `get_event_enums()` method that generates the ValidationAction enum for itemerror events:

```dart
enum ValidationAction {
  reject,                      // 0: Reject value and show message
  accept,                      // 1: Accept value
  rejectAllowFocusChange,      // 2: Reject but allow focus change
  rejectNoMessage,             // 3: Reject without showing message
}
```

## Flutter/Dart Output Examples

### CloseQuery Event
```dart
Future<bool> _closeQueryHandler() async {
  // TODO: Convert PowerBuilder statement: IF not saved THEN
  return false;  // return 1 maps to false
  // TODO: Convert PowerBuilder statement: END IF
  return true;   // return 0 maps to true
}
```

### ItemError Event
```dart
int _itemErrorHandler(int rowIndex, String columnName, dynamic value, String errorMessage) {
  // TODO: Convert PowerBuilder statement: MessageBox('Error', 'Invalid value')
  return ValidationAction.reject.index;  // return 0 maps to reject
}
```

### Key Event
```dart
bool _keyHandler(KeyEvent event) {
  // TODO: Convert PowerBuilder statement: IF key = KeyF1! THEN
  // TODO: Convert PowerBuilder statement: ShowHelp()
  return true;  // return 1 maps to true
  // TODO: Convert PowerBuilder statement: END IF
  return false; // Default return
}
```

## Testing

Comprehensive test suite implemented in `test_event_return_types.py` covering:

- All event types with return values
- Return value extraction and mapping
- Return type inference
- Default return values
- Event registration code generation
- Enum generation

All 13 tests pass successfully.

## Future Enhancements

1. Complete PowerBuilder statement conversion in `_convert_event_body()`
2. Support for more complex return expressions
3. Integration with expression converter for full statement translation
4. Support for custom event return types beyond bool/int