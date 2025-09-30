//! PBD Reforge - PowerBuilder Reverse Engineering
//!
//! Composition root that wires together all layers:
//! - Domain (pure business logic)
//! - Application (use cases and services)
//! - Adapters (infrastructure and I/O)

use clap::{Parser, Subcommand};
use std::path::PathBuf;

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
            // TODO: Wire up import_library use case
            println!("Import not yet implemented");
        }

        Commands::Decode { library } => {
            tracing::info!("Decoding library: {}", library);
            // TODO: Wire up decode_objects use case
            println!("Decode not yet implemented");
        }

        Commands::Emit { target, out } => {
            tracing::info!("Emitting target: {} to {:?}", target, out);
            // TODO: Wire up generate_target use case
            println!("Emit not yet implemented");
        }

        Commands::Validate { out } => {
            tracing::info!("Validating round-trip: {:?}", out);
            // TODO: Wire up validate_roundtrip use case
            println!("Validate not yet implemented");
        }
    }

    Ok(())
}
