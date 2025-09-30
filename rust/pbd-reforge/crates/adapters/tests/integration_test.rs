//! Integration Tests for PBD Reforge
//!
//! Tests with real PowerBuilder PBD files from data/pbd_files/

use adapters::pb::pbd_reader::PbdReader;
use adapters::emit::*;
use domain::model::{CoreModule, CoreItem, UiTree, UiNode};
use domain::translation::TargetEmitter;
use std::path::{Path, PathBuf};
use std::fs;

// Test data directory
const PBD_DIR: &str = "/Users/michael/Projects/powerrebuilder/data/pbd_files";

// Helper function to get test PBD file
fn get_test_pbd(filename: &str) -> PathBuf {
    PathBuf::from(PBD_DIR).join(filename)
}

// Helper function to check if test data exists
fn has_test_data() -> bool {
    Path::new(PBD_DIR).exists()
}

#[test]
fn test_pbd_directory_exists() {
    assert!(
        has_test_data(),
        "Test data directory not found: {}. Please ensure PBD files are available.",
        PBD_DIR
    );
}

#[test]
fn test_parse_dcm_login_header() {
    if !has_test_data() {
        println!("Skipping test: no test data");
        return;
    }

    let path = get_test_pbd("dcm_login.pbd");
    let reader = PbdReader::open(&path).expect("Failed to open PBD file");

    // Parse header
    let header = reader.parse_header().expect("Failed to parse header");

    // Verify HDR* signature
    assert_eq!(&header.signature[0..4], b"HDR*");

    // Verify version is set
    assert!(header.version > 0, "Version should be > 0, got {}", header.version);

    println!("✓ Successfully parsed dcm_login.pbd header");
    println!("  Format: {}", header.format);
    println!("  Version: {}", header.version);
    println!("  Entry count: {}", header.entry_count);
}

#[test]
fn test_extract_dcm_login_objects() {
    if !has_test_data() {
        println!("Skipping test: no test data");
        return;
    }

    let path = get_test_pbd("dcm_login.pbd");
    let reader = PbdReader::open(&path).expect("Failed to open PBD file");

    let (objects, errors) = reader.extract_objects();

    println!("✓ Extracted {} objects", objects.len());
    println!("  Errors: {}", errors.len());

    // Should extract at least some objects
    assert!(objects.len() > 0, "Should extract at least one object");

    // Verify object structure
    for (i, obj) in objects.iter().take(5).enumerate() {
        println!("  Object {}: {} ({} bytes)",
            i, obj.name, obj.data.len());

        assert!(!obj.name.is_empty(), "Object name should not be empty");
        assert!(!obj.object_type.is_empty(), "Object type should not be empty");
        assert!(obj.data.len() > 0, "Object data should not be empty");
    }

    // Print errors if any
    if !errors.is_empty() {
        println!("\n  Extraction errors:");
        for error in errors.iter().take(3) {
            println!("    - {}", error);
        }
    }
}

#[test]
fn test_parse_all_pbd_files() {
    if !has_test_data() {
        println!("Skipping test: no test data");
        return;
    }

    let pbd_dir = Path::new(PBD_DIR);
    let mut success_count = 0;
    let mut fail_count = 0;

    for entry in fs::read_dir(pbd_dir).expect("Failed to read PBD directory") {
        let entry = entry.expect("Failed to read directory entry");
        let path = entry.path();

        if path.extension().and_then(|s| s.to_str()) != Some("pbd") {
            continue;
        }

        let filename = path.file_name().unwrap().to_str().unwrap();

        match PbdReader::open(&path) {
            Ok(reader) => {
                match reader.parse_header() {
                    Ok(header) => {
                        success_count += 1;
                        println!("✓ {} - {} entries", filename, header.entry_count);
                    }
                    Err(e) => {
                        fail_count += 1;
                        println!("✗ {} - parse error: {}", filename, e);
                    }
                }
            }
            Err(e) => {
                fail_count += 1;
                println!("✗ {} - open error: {}", filename, e);
            }
        }
    }

    println!("\nResults: {} succeeded, {} failed", success_count, fail_count);

    // Should parse most files successfully
    assert!(success_count > 0, "Should successfully parse at least one PBD file");
}

// ==============================================================================
// Code Generator Tests
// ==============================================================================

fn create_test_core_module() -> CoreModule {
    CoreModule {
        id: "test_module".to_string(),
        items: vec![
            CoreItem::Data {
                def: domain::model::DataDef {
                    name: "TestEntity".to_string(),
                    fields: vec![
                        ("id".to_string(), domain::decode::Ty::Int),
                        ("name".to_string(), domain::decode::Ty::String),
                    ],
                },
            },
        ],
    }
}

fn create_test_ui_tree() -> UiTree {
    UiTree {
        root: UiNode::Window {
            title: "Test Window".to_string(),
            children: vec![],
        },
    }
}

#[test]
fn test_flutter_emitter_generates_all_files() {
    let config = FlutterGeneratorConfig::default();
    let emitter = FlutterEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Flutter emission failed");

    // Expected files
    let expected = vec![
        "lib/main.dart",
        "pubspec.yaml",
        "lib/ui/app_theme.dart",
        "lib/services/state_manager.dart",
        "lib/models/domain.dart",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Flutter emitter generated {} files", result.files.len());

    // Verify main.dart contains expected code
    let main_dart = result.files.iter()
        .find(|f| f.path == "lib/main.dart")
        .expect("main.dart not found");

    assert!(main_dart.content.contains("void main()"));
    assert!(main_dart.content.contains("MyApp"));

    println!("  ✓ main.dart has valid structure");
}

#[test]
fn test_react_emitter_generates_all_files() {
    let config = ReactGeneratorConfig::default();
    let emitter = ReactEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("React emission failed");

    let expected = vec![
        "src/App.tsx",
        "src/context/StateContext.tsx",
        "src/main.tsx",
        "package.json",
        "tsconfig.json",
        "vite.config.ts",
        "index.html",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ React emitter generated {} files", result.files.len());

    // Verify App.tsx
    let app_tsx = result.files.iter()
        .find(|f| f.path == "src/App.tsx")
        .expect("App.tsx not found");

    assert!(app_tsx.content.contains("function App()"));
    assert!(app_tsx.content.contains("ThemeProvider"));

    println!("  ✓ App.tsx has valid React structure");
}

#[test]
fn test_vue_emitter_generates_all_files() {
    let config = VueGeneratorConfig::default();
    let emitter = VueEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Vue emission failed");

    let expected = vec![
        "src/App.vue",
        "src/main.ts",
        "src/stores/app.ts",
        "src/router/index.ts",
        "package.json",
        "vite.config.ts",
        "tsconfig.json",
        "index.html",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Vue emitter generated {} files", result.files.len());

    // Verify App.vue
    let app_vue = result.files.iter()
        .find(|f| f.path == "src/App.vue")
        .expect("App.vue not found");

    assert!(app_vue.content.contains("<script setup"));
    assert!(app_vue.content.contains("RouterView"));

    println!("  ✓ App.vue has valid Vue 3 structure");
}

#[test]
fn test_svelte_emitter_generates_all_files() {
    let config = SvelteGeneratorConfig::default();
    let emitter = SvelteEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Svelte emission failed");

    let expected = vec![
        "src/App.svelte",
        "src/main.ts",
        "src/stores/app.ts",
        "package.json",
        "vite.config.ts",
        "svelte.config.js",
        "index.html",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Svelte emitter generated {} files", result.files.len());

    // Verify App.svelte
    let app_svelte = result.files.iter()
        .find(|f| f.path == "src/App.svelte")
        .expect("App.svelte not found");

    assert!(app_svelte.content.contains("<script lang=\"ts\">"));
    assert!(app_svelte.content.contains("<main>"));

    println!("  ✓ App.svelte has valid structure");
}

#[test]
fn test_python_emitter_generates_all_files() {
    let config = PythonGeneratorConfig::default();
    let emitter = PythonEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Python emission failed");

    let expected = vec![
        "main.py",
        "database.py",
        "models.py",
        "controllers.py",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "README.md",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Python emitter generated {} files", result.files.len());

    // Verify main.py
    let main_py = result.files.iter()
        .find(|f| f.path == "main.py")
        .expect("main.py not found");

    assert!(main_py.content.contains("from litestar import Litestar"));
    assert!(main_py.content.contains("app = Litestar"));

    // Verify models.py
    let models_py = result.files.iter()
        .find(|f| f.path == "models.py")
        .expect("models.py not found");

    assert!(models_py.content.contains("from sqlmodel import"));
    assert!(models_py.content.contains("class Entity"));

    println!("  ✓ main.py and models.py have valid Python/Litestar structure");
}

#[test]
fn test_docs_emitter_generates_all_files() {
    let config = DocsGeneratorConfig::default();
    let emitter = DocsEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Docs emission failed");

    let expected = vec![
        "README.md",
        "ARCHITECTURE.md",
        "API.md",
        "DEPLOYMENT.md",
        "MIGRATION_NOTES.md",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Docs emitter generated {} files", result.files.len());

    // Verify README.md
    let readme = result.files.iter()
        .find(|f| f.path == "README.md")
        .expect("README.md not found");

    assert!(readme.content.contains("# PowerBuilder Migration"));
    assert!(readme.content.contains("Generated from PowerBuilder"));

    // Verify ARCHITECTURE.md
    let arch = result.files.iter()
        .find(|f| f.path == "ARCHITECTURE.md")
        .expect("ARCHITECTURE.md not found");

    assert!(arch.content.contains("# Architecture Documentation"));
    assert!(arch.content.contains("Functional Domain Modeling"));

    println!("  ✓ Documentation files have comprehensive content");
}

#[test]
fn test_all_emitters_produce_valid_output() {
    let module = create_test_core_module();

    let emitters: Vec<(&str, Box<dyn TargetEmitter>)> = vec![
        ("Flutter", Box::new(FlutterEmitter::new(FlutterGeneratorConfig::default()))),
        ("React", Box::new(ReactEmitter::new(ReactGeneratorConfig::default()))),
        ("Vue", Box::new(VueEmitter::new(VueGeneratorConfig::default()))),
        ("Svelte", Box::new(SvelteEmitter::new(SvelteGeneratorConfig::default()))),
        ("Python", Box::new(PythonEmitter::new(PythonGeneratorConfig::default()))),
        ("Docs", Box::new(DocsEmitter::new(DocsGeneratorConfig::default()))),
    ];

    for (name, emitter) in emitters {
        let result = emitter.emit_core(&module);
        assert!(result.is_ok(), "{} emitter failed: {:?}", name, result.err());

        let emission = result.unwrap();
        assert!(emission.files.len() > 0, "{} emitter produced no files", name);

        println!("✓ {} emitter: {} files", name, emission.files.len());
    }

    println!("\n✅ All 6 emitters produce valid output!");
}

#[test]
fn test_rust_emitter_generates_all_files() {
    let config = RustGeneratorConfig::default();
    let emitter = RustEmitter::new(config);

    let module = create_test_core_module();
    let result = emitter.emit_core(&module).expect("Rust emission failed");

    let expected = vec![
        "Cargo.toml",
        "src/lib.rs",
        "README.md",
        "benches/benchmarks.rs",
        ".gitignore",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Rust emitter generated {} files", result.files.len());

    // Verify Cargo.toml
    let cargo_toml = result.files.iter()
        .find(|f| f.path == "Cargo.toml")
        .expect("Cargo.toml not found");

    assert!(cargo_toml.content.contains("[package]"));
    assert!(cargo_toml.content.contains("serde"));

    // Verify lib.rs
    let lib_rs = result.files.iter()
        .find(|f| f.path == "src/lib.rs")
        .expect("lib.rs not found");

    assert!(lib_rs.content.contains("pub struct"));
    assert!(lib_rs.content.contains("impl"));

    println!("  ✓ Rust code has valid structure");
}

#[test]
fn test_iced_emitter_generates_all_files() {
    let config = IcedGeneratorConfig::default();
    let emitter = IcedEmitter::new(config);

    let ui_tree = create_test_ui_tree();
    let result = emitter.emit_ui(&ui_tree).expect("Iced emission failed");

    let expected = vec![
        "Cargo.toml",
        "src/main.rs",
        "src/state.rs",
        "src/message.rs",
        "src/update.rs",
        "src/view.rs",
        "README.md",
        ".gitignore",
    ];

    for expected_file in expected {
        assert!(
            result.files.iter().any(|f| f.path == expected_file),
            "Missing file: {}",
            expected_file
        );
    }

    println!("✓ Iced emitter generated {} files", result.files.len());

    // Verify main.rs
    let main_rs = result.files.iter()
        .find(|f| f.path == "src/main.rs")
        .expect("main.rs not found");

    assert!(main_rs.content.contains("fn main()"));
    assert!(main_rs.content.contains("Application"));
    assert!(main_rs.content.contains("The Elm Architecture"));

    // Verify state.rs
    let state_rs = result.files.iter()
        .find(|f| f.path == "src/state.rs")
        .expect("state.rs not found");

    assert!(state_rs.content.contains("pub struct AppState"));

    println!("  ✓ Iced app has valid Elm architecture structure");
}

#[test]
fn test_all_8_emitters_produce_valid_output() {
    let module = create_test_core_module();
    let ui_tree = create_test_ui_tree();

    let emitters: Vec<(&str, Box<dyn TargetEmitter>)> = vec![
        ("Flutter", Box::new(FlutterEmitter::new(FlutterGeneratorConfig::default()))),
        ("React", Box::new(ReactEmitter::new(ReactGeneratorConfig::default()))),
        ("Vue", Box::new(VueEmitter::new(VueGeneratorConfig::default()))),
        ("Svelte", Box::new(SvelteEmitter::new(SvelteGeneratorConfig::default()))),
        ("Python", Box::new(PythonEmitter::new(PythonGeneratorConfig::default()))),
        ("Docs", Box::new(DocsEmitter::new(DocsGeneratorConfig::default()))),
        ("Rust", Box::new(RustEmitter::new(RustGeneratorConfig::default()))),
        ("Iced", Box::new(IcedEmitter::new(IcedGeneratorConfig::default()))),
    ];

    for (name, emitter) in emitters {
        // Test core emission for non-UI generators
        if name != "Iced" {
            let result = emitter.emit_core(&module);
            assert!(result.is_ok(), "{} emitter failed: {:?}", name, result.err());

            if let Ok(emission) = result {
                if emission.files.len() > 0 {
                    println!("✓ {} emitter (core): {} files", name, emission.files.len());
                }
            }
        }

        // Test UI emission for UI generators
        if name == "Iced" {
            let result = emitter.emit_ui(&ui_tree);
            assert!(result.is_ok(), "{} emitter failed: {:?}", name, result.err());

            let emission = result.unwrap();
            assert!(emission.files.len() > 0, "{} emitter produced no files", name);
            println!("✓ {} emitter (UI): {} files", name, emission.files.len());
        }
    }

    println!("\n✅ All 8 emitters produce valid output!");
}
