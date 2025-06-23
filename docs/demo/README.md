# SIME Finch Demo - PowerBuilder to Flutter Conversion

This demo showcases the end-to-end conversion of a PowerBuilder application to Flutter.

## Running the Demo

1. Make sure you're in the project root directory:
   ```bash
   cd /path/to/sime-finch
   ```

2. Run the demo script:
   ```bash
   python demo/demo_conversion.py
   ```

3. The demo will:
   - Create a sample PowerBuilder application (Employee Manager)
   - Convert it to a Flutter application
   - Display conversion statistics and results

## Sample Application Features

The demo creates a PowerBuilder Employee Manager application with:

- **Main Window** (`w_employee_manager`): Employee data grid with Add, Delete, Save buttons
- **DataWindow** (`d_employee`): Employee table with columns for ID, name, email, phone, hire date, salary
- **Business Logic** (`n_employee_service`): Employee validation and bonus calculation

## Expected Output

After conversion, you'll find:

```
demo_output/
├── sample_pb_app/          # Original PowerBuilder files
│   ├── w_employee_manager.srw
│   ├── d_employee.srd
│   └── n_employee_service.sru
└── flutter_app/            # Generated Flutter application
    ├── lib/
    │   ├── main.dart
    │   ├── screens/
    │   │   └── employee_manager_screen.dart
    │   ├── widgets/
    │   │   └── employee_datawindow.dart
    │   ├── models/
    │   │   └── employee.dart
    │   └── services/
    │       └── employee_service.dart
    └── pubspec.yaml
```

## Conversion Features Demonstrated

1. **Window to Screen**: PowerBuilder windows → Flutter screens
2. **DataWindow to Widget**: DataWindow objects → Flutter DataTable widgets
3. **Business Logic to Service**: Non-visual objects → Dart service classes
4. **Event Handling**: PowerBuilder events → Flutter event handlers
5. **Data Binding**: DataWindow columns → Model classes

## Next Steps

After running the demo, you can:

1. Examine the generated Flutter code
2. Compare it with the original PowerBuilder code
3. Run the Flutter app (requires Flutter SDK):
   ```bash
   cd demo_output/flutter_app
   flutter pub get
   flutter run
   ```

## Customization

To test with your own PowerBuilder code:

1. Modify the `create_sample_app()` function in `demo_conversion.py`
2. Add your PowerBuilder source files
3. Run the demo again

## Troubleshooting

If the conversion fails:
- Check the logs for specific error messages
- Ensure PowerBuilder syntax is valid
- Verify file paths are correct
- Review the error recovery reports