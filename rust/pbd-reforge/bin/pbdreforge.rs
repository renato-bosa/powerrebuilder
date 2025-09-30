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

    /// Decode artifacts from imported library
    Decode {
        /// Library ID (from import command)
        library: String,
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

        Commands::Decode { library } => {
            tracing::info!("Decoding library: {}", library);
            println!("Decode not yet implemented - use Import command to parse PBD files");
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
                _ => {
                    return Err(anyhow::anyhow!(
                        "Unknown target: {}. Available: flutter, react, vue, svelte, python, docs",
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
