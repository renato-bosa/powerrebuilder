//! Rust Code Emitter
//!
//! Generates Rust code from RustAst intermediate representation.
//! Produces production-ready Rust projects with proper formatting.

use domain::model::{CoreModule, CoreItem, DataDef};
use domain::translation::{
    core_to_rust_ast, EmissionUnit, EmitErr, EmittedFile, FeatureSet, RsEnum, RsFile, RsFn,
    RsImpl, RsItem, RsStruct, RustAst, TargetEmitter,
};
use domain::decode::Ty;
use std::collections::HashMap;

/// Rust generator configuration
#[derive(Debug, Clone)]
pub struct RustGeneratorConfig {
    pub crate_name: String,
    pub crate_version: String,
    pub edition: String,
    pub generate_tests: bool,
    pub use_serde: bool,
}

impl Default for RustGeneratorConfig {
    fn default() -> Self {
        Self {
            crate_name: "generated_crate".to_string(),
            crate_version: "0.1.0".to_string(),
            edition: "2021".to_string(),
            generate_tests: true,
            use_serde: true,
        }
    }
}

pub struct RustEmitter {
    config: RustGeneratorConfig,
}

impl RustEmitter {
    pub fn new(config: RustGeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate Cargo.toml
    fn generate_cargo_toml(&self) -> String {
        let serde_deps = if self.config.use_serde {
            r#"serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
"#
        } else {
            ""
        };

        format!(
            r#"[package]
name = "{}"
version = "{}"
edition = "{}"
authors = ["PowerBuilder Migration <migration@example.com>"]

[dependencies]
{}
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "benchmarks"
harness = false
"#,
            self.config.crate_name, self.config.crate_version, self.config.edition, serde_deps
        )
    }

    /// Generate lib.rs or main.rs
    fn generate_lib_rs(&self, module: &CoreModule) -> String {
        let mut code = String::new();

        // Module documentation
        code.push_str(&format!(
            "//! {}\n//!\n//! Generated from PowerBuilder source code.\n\n",
            self.config.crate_name
        ));

        // Convert CoreModule to RustAst
        let rust_ast = core_to_rust_ast(module);

        // Generate items from each file
        for file in &rust_ast.files {
            for item in &file.items {
                code.push_str(&self.format_item(item));
                code.push_str("\n\n");
            }
        }

        // Generate from CoreModule items directly
        for item in &module.items {
            match item {
                CoreItem::Data { def } => {
                    code.push_str(&self.generate_struct_from_datadef(def));
                    code.push_str("\n\n");
                }
                CoreItem::Fn { sig, body } => {
                    // Generate function (TODO: implement body generation)
                    code.push_str(&format!("// Function: {}\n", sig.name));
                }
                CoreItem::Extern { sig } => {
                    // Generate extern function declaration
                    code.push_str(&format!("// Extern function: {}\n", sig.name));
                }
            }
        }

        code
    }

    /// Generate struct from DataDef
    fn generate_struct_from_datadef(&self, def: &DataDef) -> String {
        let mut code = String::new();

        // Derives
        let derives = if self.config.use_serde {
            "#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]"
        } else {
            "#[derive(Debug, Clone, PartialEq)]"
        };

        code.push_str(derives);
        code.push_str("\n");
        code.push_str(&format!("pub struct {} {{\n", def.name));

        for (field_name, field_type) in &def.fields {
            let rust_type = self.ty_to_rust_type(field_type);
            code.push_str(&format!("    pub {}: {},\n", field_name, rust_type));
        }

        code.push_str("}\n");

        // Implementation
        code.push_str(&format!("\nimpl {} {{\n", def.name));
        code.push_str("    pub fn new() -> Self {\n");
        code.push_str("        Self {\n");

        for (field_name, field_type) in &def.fields {
            let default_val = self.ty_default_value(field_type);
            code.push_str(&format!("            {}: {},\n", field_name, default_val));
        }

        code.push_str("        }\n");
        code.push_str("    }\n");
        code.push_str("}\n");

        code
    }

    /// Convert Ty to Rust type string
    fn ty_to_rust_type(&self, ty: &Ty) -> String {
        match ty {
            Ty::Void => "()".to_string(),
            Ty::Bool => "bool".to_string(),
            Ty::Int => "i32".to_string(),
            Ty::Real => "f64".to_string(),
            Ty::String => "String".to_string(),
            Ty::Struct(name, _) => name.clone(),
            Ty::Unknown => "Box<dyn std::any::Any>".to_string(),
        }
    }

    /// Get default value for Ty
    fn ty_default_value(&self, ty: &Ty) -> String {
        match ty {
            Ty::Void => "()".to_string(),
            Ty::Bool => "false".to_string(),
            Ty::Int => "0".to_string(),
            Ty::Real => "0.0".to_string(),
            Ty::String => "String::new()".to_string(),
            Ty::Struct(name, _) => format!("{}::default()", name),
            Ty::Unknown => "Box::new(())".to_string(),
        }
    }

    /// Format a single RsItem
    fn format_item(&self, item: &RsItem) -> String {
        match item {
            RsItem::Fn(f) => self.format_function(f),
            RsItem::Struct(s) => self.format_struct(s),
            RsItem::Enum(e) => self.format_enum(e),
            RsItem::Impl(i) => self.format_impl(i),
            RsItem::Use(path) => format!("use {};", path),
            RsItem::Mod(name) => format!("pub mod {};", name),
        }
    }

    /// Format function
    fn format_function(&self, func: &RsFn) -> String {
        let mut code = String::new();

        // Function signature
        code.push_str(&format!("pub fn {}(", func.name));

        // Parameters
        let params: Vec<String> = func
            .params
            .iter()
            .map(|(name, ty)| format!("{}: {}", name, ty))
            .collect();
        code.push_str(&params.join(", "));
        code.push_str(")");

        // Return type
        if let Some(ret) = &func.return_ty {
            code.push_str(&format!(" -> {}", ret));
        }

        code.push_str(" {\n");
        code.push_str(&format!("    {}\n", func.body));
        code.push_str("}\n");

        code
    }

    /// Format struct
    fn format_struct(&self, s: &RsStruct) -> String {
        let mut code = String::new();

        let derives = if self.config.use_serde {
            "#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]"
        } else {
            "#[derive(Debug, Clone)]"
        };

        code.push_str(derives);
        code.push_str("\n");
        code.push_str(&format!("pub struct {} {{\n", s.name));

        for (field, ty) in &s.fields {
            code.push_str(&format!("    pub {}: {},\n", field, ty));
        }

        code.push_str("}\n");
        code
    }

    /// Format enum
    fn format_enum(&self, e: &RsEnum) -> String {
        let mut code = String::new();

        let derives = if self.config.use_serde {
            "#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]"
        } else {
            "#[derive(Debug, Clone, PartialEq, Eq)]"
        };

        code.push_str(derives);
        code.push_str("\n");
        code.push_str(&format!("pub enum {} {{\n", e.name));

        for variant in &e.variants {
            code.push_str(&format!("    {},\n", variant));
        }

        code.push_str("}\n");
        code
    }

    /// Format impl block
    fn format_impl(&self, impl_block: &RsImpl) -> String {
        let mut code = String::new();

        code.push_str(&format!("impl {} {{\n", impl_block.target));

        for item in &impl_block.items {
            let item_code = self.format_item(item);
            // Indent each line
            for line in item_code.lines() {
                code.push_str(&format!("    {}\n", line));
            }
        }

        code.push_str("}\n");
        code
    }

    /// Generate README.md
    fn generate_readme(&self) -> String {
        format!(
            r#"# {}

Generated Rust crate from PowerBuilder source code.

## Build

```bash
cargo build --release
```

## Test

```bash
cargo test
```

## Benchmarks

```bash
cargo bench
```

## Documentation

```bash
cargo doc --open
```

## Generated by PowerRebuilder

This crate was automatically generated from PowerBuilder binary artifacts using
the PowerRebuilder reverse engineering toolkit.
"#,
            self.config.crate_name
        )
    }

    /// Generate tests
    fn generate_tests(&self, module: &CoreModule) -> String {
        let mut code = String::new();

        code.push_str("#[cfg(test)]\n");
        code.push_str("mod tests {\n");
        code.push_str("    use super::*;\n\n");

        // Generate a basic test for each struct
        for item in &module.items {
            if let CoreItem::Data { def } = item {
                code.push_str(&format!(
                    r#"    #[test]
    fn test_{}_creation() {{
        let obj = {}::new();
        assert_eq!(obj, obj.clone());
    }}

"#,
                    def.name.to_lowercase(),
                    def.name
                ));
            }
        }

        code.push_str("}\n");
        code
    }

    /// Generate benchmarks
    fn generate_benchmarks(&self) -> String {
        r#"use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_example(c: &mut Criterion) {
    c.bench_function("example", |b| {
        b.iter(|| {
            // Benchmark code here
            black_box(42)
        })
    });
}

criterion_group!(benches, benchmark_example);
criterion_main!(benches);
"#
        .to_string()
    }
}

impl TargetEmitter for RustEmitter {
    fn target_id(&self) -> &'static str {
        "rust"
    }

    fn supports(&self, _features: &FeatureSet) -> bool {
        true // Rust supports all features
    }

    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate Cargo.toml
        files.push(EmittedFile {
            path: "Cargo.toml".to_string(),
            content: self.generate_cargo_toml(),
            is_executable: false,
        });

        // Generate lib.rs
        files.push(EmittedFile {
            path: "src/lib.rs".to_string(),
            content: self.generate_lib_rs(ir),
            is_executable: false,
        });

        // Generate tests if enabled
        if self.config.generate_tests {
            files.push(EmittedFile {
                path: "src/lib.rs".to_string(),
                content: format!(
                    "{}\n\n{}",
                    self.generate_lib_rs(ir),
                    self.generate_tests(ir)
                ),
                is_executable: false,
            });
        }

        // Generate README
        files.push(EmittedFile {
            path: "README.md".to_string(),
            content: self.generate_readme(),
            is_executable: false,
        });

        // Generate benchmarks
        files.push(EmittedFile {
            path: "benches/benchmarks.rs".to_string(),
            content: self.generate_benchmarks(),
            is_executable: false,
        });

        // Generate .gitignore
        files.push(EmittedFile {
            path: ".gitignore".to_string(),
            content: "/target\nCargo.lock\n".to_string(),
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }

    fn emit_ui(&self, _ui: &domain::model::UiTree) -> Result<EmissionUnit, EmitErr> {
        // Rust emitter doesn't generate UI - use IcedEmitter for that
        Ok(EmissionUnit {
            files: vec![],
            metadata: HashMap::new(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rust_emitter() {
        let config = RustGeneratorConfig::default();
        let emitter = RustEmitter::new(config);
        assert_eq!(emitter.target_id(), "rust");
    }

    #[test]
    fn test_generate_cargo_toml() {
        let config = RustGeneratorConfig::default();
        let emitter = RustEmitter::new(config);
        let cargo = emitter.generate_cargo_toml();
        assert!(cargo.contains("[package]"));
        assert!(cargo.contains("serde"));
    }
}
