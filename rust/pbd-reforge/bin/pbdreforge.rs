//! PBD Reforge - PowerBuilder Reverse Engineering
//!
//! Composition root that wires together all layers:
//! - Domain (pure business logic)
//! - Application (use cases and services)
//! - Adapters (infrastructure and I/O)

use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::fs;
use adapters::pb::pbd_reader::PbdReader;
use adapters::emit::*;
use domain::model::UiTree;
use domain::model::{CoreModule, CoreItem, DataDef};
use domain::translation::TargetEmitter;
use domain::decode::Ty;

#[derive(Parser)]
#[command(name = "pbdreforge")]
#[command(about = "PowerBuilder reverse engineering toolkit", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Enable verbose logging
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Import a PowerBuilder library
    Import {
        /// Path to PBL/PBD file
        path: PathBuf,

        /// PowerBuilder version hint (e.g., "12.5")
        #[arg(short, long)]
        version: Option<String>,
    },

    /// Decode P-code from PBD file
    Decode {
        /// Path to PBD file
        path: PathBuf,

        /// PowerBuilder version (auto-detect if not specified)
        #[arg(short, long)]
        version: Option<String>,

        /// Output directory for decompiled code
        #[arg(short, long)]
        out: Option<PathBuf>,
    },

    /// Generate target code
    Emit {
        /// Target (e.g., "rust", "rust+iced")
        target: String,

        /// Output directory
        #[arg(short, long)]
        out: PathBuf,
    },

    /// Validate round-trip transformation
    Validate {
        /// Generated output directory
        out: PathBuf,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // Initialize tracing
    let subscriber = tracing_subscriber::fmt()
        .with_max_level(if cli.verbose {
            tracing::Level::DEBUG
        } else {
            tracing::Level::INFO
        })
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    match cli.command {
        Commands::Import { path, version } => {
            tracing::info!("Importing library: {:?}", path);
            tracing::info!("Version hint: {:?}", version);

            // Open and parse PBD file
            let reader = PbdReader::open(&path)?;
            let header = reader.parse_header()
                .map_err(|e| anyhow::anyhow!("Failed to parse header: {}", e))?;

            println!("✓ Successfully parsed: {}", path.display());
            println!("  Format: {}", header.format);
            println!("  Version: {}", header.version);
            println!("  Entry count: {}", header.entry_count);

            // Extract objects
            let (objects, errors) = reader.extract_objects();
            println!("\n✓ Extracted {} objects", objects.len());

            if !errors.is_empty() {
                println!("  ⚠ {} extraction errors", errors.len());
                for error in errors.iter().take(3) {
                    println!("    - {}", error);
                }
            }

            // Show first few objects
            println!("\nFirst objects:");
            for (i, obj) in objects.iter().take(5).enumerate() {
                println!("  {}: {} - {} ({} bytes)",
                    i, obj.name, obj.object_type, obj.data.len());
            }
        }

        Commands::Decode { path, version, out } => {
            tracing::info!("Decoding P-code from: {:?}", path);

            // Open and parse PBD file
            let reader = PbdReader::open(&path)?;
            let header = reader.parse_header()
                .map_err(|e| anyhow::anyhow!("Failed to parse header: {}", e))?;

            println!("✓ Opened PBD file: {}", path.display());
            println!("  Format: {}", header.format);
            println!("  Version: {}", header.version);
            println!("  Entry count: {}", header.entry_count);

            // Extract objects
            let (objects, errors) = reader.extract_objects();
            println!("\n✓ Extracted {} objects", objects.len());

            if !errors.is_empty() {
                println!("  ⚠ {} extraction errors", errors.len());
                for error in errors.iter().take(3) {
                    println!("    - {}", error);
                }
            }

            // Determine PowerBuilder version
            use domain::decode::PBVersion;
            let pb_version = if let Some(ver_str) = version {
                // Parse version string (e.g., "12.5")
                match ver_str.as_str() {
                    "6" | "6.0" => PBVersion::PB6,
                    "7" | "7.0" => PBVersion::PB7,
                    "9" | "9.0" => PBVersion::PB9,
                    "10" | "10.0" => PBVersion::PB10,
                    "11" | "11.0" => PBVersion::PB11,
                    "12" | "12.0" => PBVersion::PB12,
                    "12.5" => PBVersion::PB12_5,
                    "2017" | "17" | "17.0" => PBVersion::PB2017,
                    "2019" | "19" | "19.0" => PBVersion::PB2019,
                    _ => {
                        println!("⚠ Unknown version '{}', using auto-detection", ver_str);
                        adapters::pb::detect_version(reader.bytes())
                            .unwrap_or(PBVersion::PB12)
                    }
                }
            } else {
                // Auto-detect version from first object's bytecode
                let detected = if !objects.is_empty() {
                    adapters::pb::detect_version(&objects[0].data)
                } else {
                    None
                };
                detected.unwrap_or(PBVersion::PB12)
            };

            println!("\n✓ Using PowerBuilder version: {}", pb_version);

            // Get decoder for version
            let decoder = adapters::pb::get_decoder(pb_version)
                .ok_or_else(|| anyhow::anyhow!("No decoder for version {}", pb_version))?;

            // Create output directory if specified
            if let Some(ref out_dir) = out {
                std::fs::create_dir_all(out_dir)?;
            }

            // Decode objects
            println!("\nDecoding {} objects...", objects.len());
            let mut decoded_count = 0;
            let mut error_count = 0;

            for (i, obj) in objects.iter().enumerate() {
                // Process all objects
                if i < 5 || i >= objects.len() - 2 || i % 50 == 0 {
                    // Show progress: first 5, last 2, and every 50th
                    print!("  [{}/{}] {} ({} bytes)... ", i + 1, objects.len(), obj.name, obj.data.len());
                } else if i == 5 {
                    println!("  ... processing remaining objects ...");
                }

                match decoder.disassemble(&obj.data) {
                    Ok(instrs) => {
                        match decoder.lift_to_pb_ir(&instrs) {
                            Ok(pb_unit) => {
                                if i < 5 || i >= objects.len() - 2 || i % 50 == 0 {
                                    println!("{} instructions, {} members ✓",
                                        instrs.len(), pb_unit.members.len());
                                }
                                decoded_count += 1;

                                // Save to output directory if specified
                                if let Some(ref out_dir) = out {
                                    // Sanitize filename: use index if name is too long or has invalid chars
                                    let filename = if obj.name.len() > 200 || obj.name.contains('/') {
                                        format!("object_{:04}.json", i)
                                    } else {
                                        format!("{}.json", obj.name)
                                    };
                                    let output_path = out_dir.join(filename);
                                    let json = serde_json::to_string_pretty(&pb_unit)?;
                                    std::fs::write(&output_path, json)?;
                                }
                            }
                            Err(e) => {
                                println!("✗ lift failed: {}", e);
                                error_count += 1;
                            }
                        }
                    }
                    Err(e) => {
                        println!("✗ disassembly failed: {}", e);
                        error_count += 1;
                    }
                }
            }

            println!("\n✓ Decode complete:");
            println!("  {} objects decoded successfully", decoded_count);
            println!("  {} objects failed", error_count);

            if let Some(out_dir) = out {
                println!("\n✓ Decompiled IR saved to: {}", out_dir.display());
            }
        }

        Commands::Emit { target, out } => {
            tracing::info!("Emitting target: {} to {:?}", target, out);

            // Create test module for demonstration
            let module = CoreModule {
                id: "demo_module".to_string(),
                items: vec![
                    CoreItem::Data {
                        def: DataDef {
                            name: "Entity".to_string(),
                            fields: vec![
                                ("id".to_string(), Ty::Int),
                                ("name".to_string(), Ty::String),
                            ],
                        },
                    },
                ],
            };

            // Select emitter based on target
            let result = match target.as_str() {
                "flutter" => {
                    println!("Generating Flutter application...");
                    let emitter = FlutterEmitter::new(FlutterGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "react" => {
                    println!("Generating React application...");
                    let emitter = ReactEmitter::new(ReactGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "vue" => {
                    println!("Generating Vue application...");
                    let emitter = VueEmitter::new(VueGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "svelte" => {
                    println!("Generating Svelte application...");
                    let emitter = SvelteEmitter::new(SvelteGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "python" => {
                    println!("Generating Python/Litestar application...");
                    let emitter = PythonEmitter::new(PythonGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "docs" => {
                    println!("Generating documentation...");
                    let emitter = DocsEmitter::new(DocsGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "rust" => {
                    println!("Generating Rust crate...");
                    let emitter = RustEmitter::new(RustGeneratorConfig::default());
                    emitter.emit_core(&module)?
                }
                "iced" => {
                    println!("Generating Iced GUI application...");
                    let emitter = IcedEmitter::new(IcedGeneratorConfig::default());
                    // Iced needs a UI tree
                    let ui_tree = domain::model::UiTree {
                        root: domain::model::UiNode::Window {
                            title: "Iced Application".to_string(),
                            children: vec![],
                        },
                    };
                    emitter.emit_ui(&ui_tree)?
                }
                _ => {
                    return Err(anyhow::anyhow!(
                        "Unknown target: {}. Available: flutter, react, vue, svelte, python, docs, rust, iced",
                        target
                    ));
                }
            };

            // Write files to output directory
            fs::create_dir_all(&out)?;
            for file in &result.files {
                let file_path = out.join(&file.path);
                fs::create_dir_all(file_path.parent().unwrap())?;
                fs::write(&file_path, &file.content)?;
                println!("  ✓ {}", file.path);
            }

            println!("\n✅ Generated {} files to {}", result.files.len(), out.display());
        }

        Commands::Validate { out } => {
            tracing::info!("Validating round-trip: {:?}", out);
            println!("Validate not yet implemented");
        }
    }

    Ok(())
}
