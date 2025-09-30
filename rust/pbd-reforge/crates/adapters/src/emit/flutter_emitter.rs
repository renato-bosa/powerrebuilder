//! Flutter Code Emitter with FFI Support
//!
//! Generates Flutter/Dart applications with FFI bindings and cross-platform support.
//! Ported from Python implementation with full feature parity.

use domain::model::{CoreModule, UiNode, UiTree};
use domain::translation::{EmissionUnit, EmitErr, EmittedFile, FeatureSet, TargetEmitter};
use std::collections::HashMap;

/// Flutter generator configuration
#[derive(Debug, Clone)]
pub struct FlutterGeneratorConfig {
    pub app_name: String,
    pub app_title: String,
    pub package_name: String,
    pub version: String,
    pub enable_ffi: bool,
    pub enable_portability: bool,
    pub target_platforms: Vec<String>,
    pub use_rust_backend: bool,
}

impl Default for FlutterGeneratorConfig {
    fn default() -> Self {
        Self {
            app_name: "app".to_string(),
            app_title: "App".to_string(),
            package_name: "com.example.app".to_string(),
            version: "0.1.0".to_string(),
            enable_ffi: true,
            enable_portability: true,
            target_platforms: vec![
                "ios".into(),
                "android".into(),
                "windows".into(),
                "macos".into(),
                "linux".into(),
            ],
            use_rust_backend: true,
        }
    }
}

pub struct FlutterEmitter {
    config: FlutterGeneratorConfig,
}

impl FlutterEmitter {
    pub fn new(config: FlutterGeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate main.dart with FFI integration
    fn generate_main_dart(&self) -> String {
        let ffi_imports = if self.config.enable_ffi {
            r#"
import 'dart:ffi';
import 'package:ffi/ffi.dart';
import 'ffi/bindings.dart';
import 'ffi/runtime.dart';"#
        } else {
            ""
        };

        let ffi_init = if self.config.enable_ffi {
            "  initializeFFI();"
        } else {
            ""
        };

        let ffi_init_fn = if self.config.enable_ffi {
            r#"
void initializeFFI() {
  final runtime = PowerBuilderRuntime();
  print("FFI initialized on ${runtime.platformInfo.archName}");
}
"#
        } else {
            ""
        };

        let provider = if self.config.enable_ffi {
            "        Provider.value(value: PowerBuilderRuntime()),"
        } else {
            ""
        };

        format!(
            r#"import 'package:flutter/material.dart';
import 'package:provider/provider.dart';{ffi_imports}

import 'models/domain.dart';
import 'services/state_manager.dart';
import 'ui/app_theme.dart';
import 'ui/screens/home_screen.dart';

void main() {{
{ffi_init}
  runApp(MyApp());
}}
{ffi_init_fn}
class MyApp extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => StateManager()),
{provider}
      ],
      child: MaterialApp(
        title: '{}',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        home: HomeScreen(),
      ),
    );
  }}
}}
"#,
            self.config.app_title
        )
    }

    /// Generate FFI runtime wrapper
    fn generate_ffi_runtime(&self) -> String {
        r#"import 'dart:ffi';
import 'dart:io' show Platform;
import 'dart:typed_data';
import 'dart:convert';
import 'package:ffi/ffi.dart';

import 'bindings.dart';

/// High-level runtime wrapper for FFI bindings
class FFIRuntime {
  static final FFIRuntime _instance = FFIRuntime._();
  factory FFIRuntime() => _instance;

  late final PowerBuilderRuntime _pbRuntime;

  FFIRuntime._() {
    _pbRuntime = PowerBuilderRuntime();
    _initialize();
    _initializeFFIFunctions();
  }

  void _initialize() {
    // Platform-specific initialization
    if (Platform.isIOS) {
      // iOS-specific setup
    } else if (Platform.isAndroid) {
      // Android-specific setup
    }
  }

  // Native function pointers
  late final Pointer<Uint8> Function(int) _loadEntityNative;
  late final void Function(int, Pointer<Uint8>, int) _saveEntityNative;
  late final Pointer<Uint8> Function(Pointer<Uint8>, int) _queryEntitiesNative;

  void _initializeFFIFunctions() {
    final dylib = _pbRuntime._nativeLib;
    _loadEntityNative = dylib.lookup<NativeFunction<Pointer<Uint8> Function(Uint64)>>('pb_load_entity').asFunction();
    _saveEntityNative = dylib.lookup<NativeFunction<Void Function(Uint64, Pointer<Uint8>, Uint32)>>('pb_save_entity').asFunction();
    _queryEntitiesNative = dylib.lookup<NativeFunction<Pointer<Uint8> Function(Pointer<Uint8>, Uint32)>>('pb_query_entities').asFunction();
  }

  String? getLastError() {
    return _pbRuntime.getLastErrorMessage();
  }

  T executeWithErrorHandling<T>(T Function() operation, String operationName) {
    try {
      final result = operation();
      return result;
    } catch (e) {
      final error = getLastError();
      throw FFIException('$operationName failed: ${error ?? e.toString()}');
    }
  }
}

class FFIException implements Exception {
  final String message;
  FFIException(this.message);

  @override
  String toString() => 'FFIException: $message';
}
"#
        .to_string()
    }

    /// Generate app theme
    fn generate_app_theme(&self) -> String {
        r#"import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      primarySwatch: Colors.blue,
      brightness: Brightness.light,
      scaffoldBackgroundColor: Colors.white,
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      primarySwatch: Colors.blue,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.grey[900],
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: Colors.grey[850],
        foregroundColor: Colors.white,
      ),
    );
  }
}
"#
        .to_string()
    }

    /// Generate pubspec.yaml
    fn generate_pubspec(&self) -> String {
        format!(
            r#"name: {}
description: Generated Flutter application
version: {}

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.0.0
  {}

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"#,
            self.config.app_name,
            self.config.version,
            if self.config.enable_ffi {
                "ffi: ^2.0.0"
            } else {
                ""
            }
        )
    }
}

impl TargetEmitter for FlutterEmitter {
    fn target_id(&self) -> &'static str {
        "flutter"
    }

    fn supports(&self, features: &FeatureSet) -> bool {
        // Flutter supports UI, async, and FFI
        true
    }

    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate main.dart
        files.push(EmittedFile {
            path: "lib/main.dart".to_string(),
            content: self.generate_main_dart(),
            is_executable: false,
        });

        // Generate pubspec.yaml
        files.push(EmittedFile {
            path: "pubspec.yaml".to_string(),
            content: self.generate_pubspec(),
            is_executable: false,
        });

        // Generate app theme
        files.push(EmittedFile {
            path: "lib/ui/app_theme.dart".to_string(),
            content: self.generate_app_theme(),
            is_executable: false,
        });

        // Generate state manager
        files.push(EmittedFile {
            path: "lib/services/state_manager.dart".to_string(),
            content: self.generate_state_manager(),
            is_executable: false,
        });

        // Generate domain models
        files.push(EmittedFile {
            path: "lib/models/domain.dart".to_string(),
            content: self.generate_domain_models(),
            is_executable: false,
        });

        if self.config.enable_ffi {
            files.push(EmittedFile {
                path: "lib/ffi/runtime.dart".to_string(),
                content: self.generate_ffi_runtime(),
                is_executable: false,
            });
        }

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }

    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate home screen from UI tree
        let home_screen = self.generate_home_screen(ui)?;
        files.push(EmittedFile {
            path: "lib/ui/screens/home_screen.dart".to_string(),
            content: home_screen,
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }
}

impl FlutterEmitter {
    fn generate_home_screen(&self, ui: &UiTree) -> Result<String, EmitErr> {
        let (title, children) = match &ui.root {
            UiNode::Window { title, children, .. } => (title.clone(), children),
            _ => ("Home".to_string(), &vec![]),
        };

        let widgets = children
            .iter()
            .filter_map(|child| self.node_to_widget(child).ok())
            .collect::<Vec<_>>()
            .join(",\n            ");

        Ok(format!(
            r#"import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/state_manager.dart';

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    final stateManager = Provider.of<StateManager>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('{}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            {}
          ],
        ),
      ),
    );
  }}
}}
"#,
            title,
            if widgets.is_empty() {
                "const Center(child: Text('Welcome')),"
            } else {
                &widgets
            }
        ))
    }

    /// Convert UiNode to Flutter widget code
    fn node_to_widget(&self, node: &UiNode) -> Result<String, EmitErr> {
        match node {
            UiNode::Window { .. } | UiNode::Container { .. } | UiNode::Menu { .. } | UiNode::Control { .. } => {
                // Default widget for unsupported nodes
                Ok(r#"Text('Widget')"#.to_string())
            }
        }
    }

    /// Generate state manager
    fn generate_state_manager(&self) -> String {
        r#"import 'package:flutter/foundation.dart';
import 'dart:async';

import '../models/domain.dart';

/// Functional state management with effects
class StateManager extends ChangeNotifier {
  // State
  final List<Entity> _entities = [];
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Entity> get entities => List.unmodifiable(_entities);
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  // Commands
  Future<void> dispatch(Command command) async {
    try {
      _setLoading(true);
      _clearError();

      await _processCommand(command);
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  Future<void> _processCommand(Command command) async {
    // Command processing logic
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String? error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
  }
}

enum CommandType { create, update, delete, query }

class Command {
  final CommandType type;
  final dynamic data;

  Command.create(this.data) : type = CommandType.create;
  Command.update(this.data) : type = CommandType.update;
  Command.delete(this.data) : type = CommandType.delete;
  Command.query(this.data) : type = CommandType.query;
}
"#
        .to_string()
    }

    /// Generate domain models
    fn generate_domain_models(&self) -> String {
        r#"import 'dart:typed_data';

/// Domain entity
class Entity {
  final int id;
  final String name;
  final Map<String, dynamic> data;
  final DateTime createdAt;
  final DateTime updatedAt;

  Entity({
    required this.id,
    required this.name,
    required this.data,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Entity.fromJson(Map<String, dynamic> json) {
    return Entity(
      id: json['id'] as int,
      name: json['name'] as String,
      data: json['data'] as Map<String, dynamic>,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'data': data,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
    };
  }
}
"#
        .to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_flutter_emitter() {
        let config = FlutterGeneratorConfig::default();
        let emitter = FlutterEmitter::new(config);
        assert_eq!(emitter.target_id(), "flutter");
    }

    #[test]
    fn test_generate_main_dart() {
        let config = FlutterGeneratorConfig::default();
        let emitter = FlutterEmitter::new(config);
        let main_dart = emitter.generate_main_dart();
        assert!(main_dart.contains("void main()"));
        assert!(main_dart.contains("MyApp"));
    }
}
