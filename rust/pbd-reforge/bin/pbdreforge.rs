//! PBD Reforge - PowerBuilder Reverse Engineering
//!
//! Composition root that wires together all layers:
//! - Domain (pure business logic)
//! - Application (use cases and services)
//! - Adapters (infrastructure and I/O)

use clap::{Parser, Subcommand};
use serde_json::json;
use std::path::Path;
use std::path::PathBuf;
use std::fs;
use adapters::pb::pbd_reader::{ExtractionError, PbdReader, PBLHeader, PBLEntry};
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

    /// Extract raw PBD entries and a reproducible manifest
    Extract {
        /// Path to PBL/PBD file
        path: PathBuf,

        /// Empty output directory for raw objects and manifest.json
        #[arg(short, long)]
        out: PathBuf,
    },

    /// Inspect extracted object signatures and candidate internal sections
    Inspect {
        /// Path to PBL/PBD file
        path: PathBuf,

        /// New JSON report file (must not already exist)
        #[arg(short, long)]
        out: PathBuf,
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

        /// Research-only: treat each complete object payload as raw P-code
        #[arg(long)]
        unsafe_raw_object: bool,
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
            println!("  PBL format version: {:04X}", header.version);
            if let Some(runtime_version) = &header.runtime_version {
                println!("  PowerBuilder runtime: {}", runtime_version);
            }
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

        Commands::Extract { path, out } => {
            tracing::info!("Extracting raw PBD entries from: {:?}", path);

            prepare_empty_output_directory(&out)?;

            let reader = PbdReader::open(&path)?;
            let header = reader.parse_header()
                .map_err(|e| anyhow::anyhow!("Failed to parse header: {}", e))?;
            let (objects, errors) = reader.extract_objects();
            let objects_dir = out.join("objects");
            std::fs::create_dir(&objects_dir)?;

            let mut manifest_entries = Vec::with_capacity(objects.len());
            for (index, object) in objects.iter().enumerate() {
                let filename = raw_object_filename(index, &object.name);
                std::fs::write(objects_dir.join(&filename), &object.data)?;

                let blocks: Vec<_> = object.data_blocks.iter().map(|block| json!({
                    "offset": block.offset,
                    "next_offset": block.next_offset,
                    "payload_offset": block.payload_offset,
                    "payload_length": block.payload_length,
                })).collect();

                manifest_entries.push(json!({
                    "index": index,
                    "name": object.name,
                    "object_type": object.object_type,
                    "size": object.size,
                    "first_data_block_offset": object.offset,
                    "data_block_count": object.data_blocks.len(),
                    "data_blocks": blocks,
                    "blake3": blake3::hash(&object.data).to_hex().to_string(),
                    "file": format!("objects/{filename}"),
                }));
            }

            let source_path = path.canonicalize().unwrap_or_else(|_| path.clone());
            let extraction_errors: Vec<String> = errors.iter().map(ToString::to_string).collect();
            let manifest = json!({
                "manifest_version": 1,
                "hash_algorithm": "BLAKE3",
                "source": {
                    "path": source_path,
                    "size": reader.bytes().len(),
                    "blake3": blake3::hash(reader.bytes()).to_hex().to_string(),
                    "format": header.format,
                    "pbl_format_version": format!("{:04X}", header.version),
                    "powerbuilder_runtime": header.runtime_version,
                    "declared_entry_count": header.entry_count,
                },
                "extracted_entry_count": objects.len(),
                "extraction_errors": extraction_errors,
                "entries": manifest_entries,
            });
            std::fs::write(
                out.join("manifest.json"),
                serde_json::to_vec_pretty(&manifest)?,
            )?;

            println!("Extracted {} raw objects to {}", objects.len(), objects_dir.display());
            println!("Manifest: {}", out.join("manifest.json").display());

            if !errors.is_empty() {
                anyhow::bail!(
                    "extraction completed with {} error(s); inspect manifest.json",
                    errors.len()
                );
            }
        }

        Commands::Inspect { path, out } => {
            tracing::info!("Inspecting compiled PBD objects from: {:?}", path);
            prepare_new_output_file(&out)?;

            let reader = PbdReader::open(&path)?;
            let header = reader.parse_header()
                .map_err(|e| anyhow::anyhow!("Failed to parse header: {}", e))?;
            let (objects, errors) = reader.extract_objects();
            let entries: Vec<_> = objects.iter().enumerate().map(|(index, object)| {
                json!({
                    "index": index,
                    "name": object.name,
                    "object_type": object.object_type,
                    "size": object.size,
                    "inspection": adapters::pb::object_inspector::inspect_object(&object.data),
                })
            }).collect();
            let validated_regions: usize = entries
                .iter()
                .filter_map(|entry| entry.get("inspection"))
                .filter_map(|inspection| inspection.get("validated_pcode_regions"))
                .filter_map(serde_json::Value::as_array)
                .map(Vec::len)
                .sum();
            let extraction_errors: Vec<String> = errors.iter().map(ToString::to_string).collect();
            let report = json!({
                "report_version": 1,
                "source": {
                    "path": path.canonicalize().unwrap_or_else(|_| path.clone()),
                    "format": header.format,
                    "pbl_format_version": format!("{:04X}", header.version),
                    "powerbuilder_runtime": header.runtime_version,
                    "entry_count": header.entry_count,
                },
                "important_caveat": "P-code boundaries are structurally validated for parsed compiled objects; PB 2022 opcode compatibility and instruction semantics remain provisional",
                "extraction_errors": extraction_errors,
                "entries": entries,
            });
            std::fs::write(&out, serde_json::to_vec_pretty(&report)?)?;

            println!("Inspected {} objects", objects.len());
            println!("Report: {}", out.display());
            println!("Validated P-code regions: {}", validated_regions);

            if !errors.is_empty() {
                anyhow::bail!(
                    "inspection completed with {} extraction error(s); inspect the report",
                    errors.len()
                );
            }
        }

        Commands::Decode { path, version, out, unsafe_raw_object } => {
            tracing::info!("Decoding P-code from: {:?}", path);

            // Open and parse PBD file
            let reader = PbdReader::open(&path)?;
            let header = reader.parse_header()
                .map_err(|e| anyhow::anyhow!("Failed to parse header: {}", e))?;

            println!("✓ Opened PBD file: {}", path.display());
            println!("  Format: {}", header.format);
            println!("  PBL format version: {:04X}", header.version);
            if let Some(runtime_version) = &header.runtime_version {
                println!("  PowerBuilder runtime: {}", runtime_version);
            }
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

            let selected_pb_version = select_pb_version(
                version.as_deref(),
                header.runtime_version.as_deref(),
                objects.first().map(|object| object.data.as_slice()),
            )?;

            if !unsafe_raw_object {
                return decode_validated_regions(
                    &path,
                    &header,
                    &objects,
                    &errors,
                    selected_pb_version,
                    out.as_deref(),
                );
            }

            println!(
                "\nWARNING: --unsafe-raw-object bypasses section validation; successful counts do not mean successful decompilation"
            );

            let pb_version = selected_pb_version;
            println!("\nUsing PowerBuilder version: {}", pb_version);

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

fn prepare_empty_output_directory(path: &Path) -> anyhow::Result<()> {
    if path.exists() {
        if !path.is_dir() {
            anyhow::bail!("output path is not a directory: {}", path.display());
        }
        if std::fs::read_dir(path)?.next().transpose()?.is_some() {
            anyhow::bail!(
                "output directory must be empty to avoid stale or overwritten evidence: {}",
                path.display()
            );
        }
    } else {
        std::fs::create_dir_all(path)?;
    }
    Ok(())
}

fn select_pb_version(
    explicit: Option<&str>,
    runtime_version: Option<&str>,
    fallback_bytes: Option<&[u8]>,
) -> anyhow::Result<domain::decode::PBVersion> {
    use domain::decode::PBVersion;

    if let Some(version) = explicit {
        return match version {
            "6" | "6.0" => Ok(PBVersion::PB6),
            "7" | "7.0" => Ok(PBVersion::PB7),
            "9" | "9.0" => Ok(PBVersion::PB9),
            "10" | "10.0" => Ok(PBVersion::PB10),
            "11" | "11.0" => Ok(PBVersion::PB11),
            "12" | "12.0" => Ok(PBVersion::PB12),
            "12.5" => Ok(PBVersion::PB12_5),
            "2017" | "17" | "17.0" => Ok(PBVersion::PB2017),
            "2019" | "19" | "19.0" => Ok(PBVersion::PB2019),
            "2022" | "22" | "22.0" | "22.1" => Ok(PBVersion::PB2022),
            _ => anyhow::bail!(
                "unsupported PowerBuilder version '{version}'; supported values include 6, 7, 9, 10, 11, 12, 12.5, 2017, 2019, and 2022"
            ),
        };
    }

    if let Some(runtime) = runtime_version {
        let mut components = runtime.split('.');
        if let Some(major) = components.next().and_then(|part| part.parse::<u16>().ok()) {
            let minor = components
                .next()
                .and_then(|part| part.parse::<u16>().ok())
                .unwrap_or(0);
            let detected = match (major, minor) {
                (22.., _) => Some(PBVersion::PB2022),
                (19..=21, _) => Some(PBVersion::PB2019),
                (17..=18, _) => Some(PBVersion::PB2017),
                (12, 5..) => Some(PBVersion::PB12_5),
                (12, _) => Some(PBVersion::PB12),
                (11, _) => Some(PBVersion::PB11),
                (10, _) => Some(PBVersion::PB10),
                (9, _) => Some(PBVersion::PB9),
                (7, _) => Some(PBVersion::PB7),
                (6, _) => Some(PBVersion::PB6),
                _ => None,
            };
            if let Some(version) = detected {
                return Ok(version);
            }
        }
    }

    Ok(fallback_bytes
        .and_then(adapters::pb::detect_version)
        .unwrap_or(PBVersion::PB12))
}

fn decode_validated_regions(
    path: &Path,
    header: &PBLHeader,
    objects: &[PBLEntry],
    extraction_errors: &[ExtractionError],
    version: domain::decode::PBVersion,
    out: Option<&Path>,
) -> anyhow::Result<()> {
    use adapters::pb::object_inspector::{inspect_object, ObjectBinaryFormat};
    use adapters::pb::pcode_scanner::scan_pcode_strict;

    let mut compiled_objects = 0;
    let mut datawindows = 0;
    let mut validated_regions = 0;
    let mut validated_region_bytes = 0;
    let mut complete_regions = 0;
    let mut parsed_instructions = 0;
    let mut consumed_bytes = 0;
    let mut entry_reports = Vec::with_capacity(objects.len());

    for (index, object) in objects.iter().enumerate() {
        let inspection = inspect_object(&object.data);
        match &inspection.format {
            ObjectBinaryFormat::CompiledObject { .. } => compiled_objects += 1,
            ObjectBinaryFormat::DataWindow { .. } => datawindows += 1,
            ObjectBinaryFormat::Unknown { .. } => {}
        }

        let mut region_reports = Vec::with_capacity(inspection.validated_pcode_regions.len());
        for region in &inspection.validated_pcode_regions {
            validated_regions += 1;
            validated_region_bytes += region.length;
            let end = region.offset.checked_add(region.length);
            let scan_report = match end.and_then(|end| object.data.get(region.offset..end)) {
                Some(bytes) => {
                    let scan = scan_pcode_strict(bytes, version);
                    complete_regions += usize::from(scan.complete);
                    parsed_instructions += scan.instruction_count;
                    consumed_bytes += scan.consumed_bytes;
                    json!(scan)
                }
                None => json!({
                    "boundary_error": "validated region falls outside its owning object"
                }),
            };
            region_reports.push(json!({
                "owner": region.owner,
                "offset": region.offset,
                "length": region.length,
                "scan": scan_report,
            }));
        }

        entry_reports.push(json!({
            "index": index,
            "name": object.name,
            "object_type": object.object_type,
            "size": object.size,
            "format": inspection.format,
            "structural_status": inspection.decode_status,
            "pcode_regions": region_reports,
        }));
    }

    let error_strings: Vec<String> = extraction_errors.iter().map(ToString::to_string).collect();
    let report = json!({
        "report_version": 1,
        "report_kind": "strict_pcode_diagnostic",
        "source": {
            "path": path.canonicalize().unwrap_or_else(|_| path.to_path_buf()),
            "format": header.format,
            "pbl_format_version": format!("{:04X}", header.version),
            "powerbuilder_runtime": header.runtime_version,
            "entry_count": header.entry_count,
        },
        "decoder": {
            "selected_version": version.to_string(),
            "opcode_names": "existing PB 6-2019 community reference",
            "operand_width_profile": "Hucxy/PbdViewer PCodeParser110 (PB 11-era)",
            "pb2022_compatibility": "provisional; scanning stops before the first unknown opcode",
            "operand_unit": "16-bit words",
        },
        "summary": {
            "object_containers": objects.len(),
            "compiled_object_envelopes": compiled_objects,
            "datawindow_envelopes": datawindows,
            "validated_pcode_regions": validated_regions,
            "validated_pcode_bytes": validated_region_bytes,
            "regions_scanned_to_end": complete_regions,
            "regions_stopped": validated_regions - complete_regions,
            "known_instructions_before_stop": parsed_instructions,
            "bytes_consumed_without_guessing": consumed_bytes,
        },
        "important_caveat": "This is an instruction-boundary diagnostic, not recovered PowerBuilder source or semantically validated decompilation.",
        "extraction_errors": error_strings,
        "entries": entry_reports,
    });

    println!("\nStrict P-code diagnostic (PowerBuilder {}):", version);
    println!("  {} object containers inspected", objects.len());
    println!("  {} compiled-object envelopes", compiled_objects);
    println!("  {} DataWindow envelopes (P-code layout pending)", datawindows);
    println!("  {} structurally validated P-code regions", validated_regions);
    println!("  {} regions scanned to their exact end", complete_regions);
    println!("  {} regions stopped without guessing", validated_regions - complete_regions);
    println!("  {} known instructions before stop", parsed_instructions);
    println!("  {}/{} bytes consumed without guessing", consumed_bytes, validated_region_bytes);

    if let Some(out_dir) = out {
        prepare_empty_output_directory(out_dir)?;
        let report_path = out_dir.join("decode-report.json");
        std::fs::write(&report_path, serde_json::to_vec_pretty(&report)?)?;
        println!("  Diagnostic report: {}", report_path.display());
    } else {
        println!("  Pass --out <empty-directory> to save the per-region report");
    }

    if !extraction_errors.is_empty() {
        anyhow::bail!(
            "strict diagnostic completed with {} extraction error(s)",
            extraction_errors.len()
        );
    }

    Ok(())
}

fn prepare_new_output_file(path: &Path) -> anyhow::Result<()> {
    if path.exists() {
        anyhow::bail!("refusing to overwrite existing report: {}", path.display());
    }
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    Ok(())
}

fn raw_object_filename(index: usize, object_name: &str) -> String {
    let sanitized: String = object_name
        .chars()
        .map(|character| {
            if character.is_control()
                || matches!(character, '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*')
            {
                '_'
            } else {
                character
            }
        })
        .take(160)
        .collect();
    let sanitized = sanitized.trim_end_matches([' ', '.']);
    let basename = if sanitized.is_empty() { "object" } else { sanitized };
    format!("{index:04}_{basename}.bin")
}

#[cfg(test)]
mod tests {
    use super::{raw_object_filename, select_pb_version};
    use domain::decode::PBVersion;

    #[test]
    fn raw_object_filename_is_ordered_and_windows_safe() {
        assert_eq!(
            raw_object_filename(7, "folder/bad:name.win."),
            "0007_folder_bad_name.win.bin"
        );
    }

    #[test]
    fn selects_pb2022_from_runtime_header() {
        assert_eq!(
            select_pb_version(None, Some("22.1.0.2819"), None).unwrap(),
            PBVersion::PB2022
        );
    }

    #[test]
    fn explicit_version_overrides_runtime_header() {
        assert_eq!(
            select_pb_version(Some("2019"), Some("22.1.0.2819"), None).unwrap(),
            PBVersion::PB2019
        );
    }

    #[test]
    fn rejects_unknown_explicit_version() {
        assert!(select_pb_version(Some("2025"), None, None).is_err());
    }
}
