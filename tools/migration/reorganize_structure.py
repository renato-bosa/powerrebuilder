#!/usr/bin/env python3
"""
Comprehensive migration script to reorganize SIME Finch codebase structure.
This script automates the file movements while preserving git history.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import json
import re

class CodebaseReorganizer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.base_path = Path.cwd()
        self.movements = []
        self.deletions = []
        self.merges = []
        self.errors = []
        
    def log(self, message: str, level="INFO"):
        print(f"[{level}] {message}")
        
    def execute_command(self, cmd: List[str]) -> bool:
        """Execute a shell command."""
        try:
            if self.dry_run:
                self.log(f"DRY RUN: {' '.join(cmd)}")
                return True
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.errors.append(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")
                    return False
                return True
        except Exception as e:
            self.errors.append(f"Exception executing {cmd}: {str(e)}")
            return False
    
    def create_directory_structure(self):
        """Create the new directory structure."""
        directories = [
            # Main source directories
            "src/extract/pbd/structures",
            "src/extract/pbd/extractors", 
            "src/extract/pbd/recovery",
            "src/extract/utils",
            
            "src/parse/grammar/definitions",
            "src/parse/parser",
            "src/parse/transformer/visitors",
            "src/parse/preprocessor",
            "src/parse/error_recovery",
            
            "src/decompile/pcode/opcodes",
            "src/decompile/analysis",
            "src/decompile/reconstruction",
            "src/decompile/extractors",
            
            "src/model/ast/nodes",
            "src/model/ast/builders",
            "src/model/ast/visitors",
            "src/model/entities",
            "src/model/types",
            "src/model/symbols",
            "src/model/analysis",
            
            "src/generate/converters/flutter/ui",
            "src/generate/converters/flutter/state",
            "src/generate/converters/flutter/business",
            "src/generate/converters/flutter/services",
            "src/generate/templates/flutter",
            "src/generate/mappings",
            "src/generate/builders",
            
            "src/common/interfaces",
            "src/common/utils",
            "src/common/patterns",
            
            "src/pipeline/stages",
            "src/pipeline/execution",
            "src/pipeline/monitoring",
            
            # Test directories
            "tests/unit/extract",
            "tests/unit/parse",
            "tests/unit/decompile",
            "tests/unit/model",
            "tests/unit/generate",
            "tests/integration",
            "tests/fixtures",
            "tests/benchmarks",
            
            # Documentation
            "docs/architecture",
            "docs/api",
            "docs/guides",
            "docs/changelog",
            
            # Tools
            "tools/analysis",
            "tools/debug",
            "tools/maintenance",
            
            # Config
            "config",
            
            # Archive
            "archive/old_docs",
            "archive/old_tests",
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            if self.dry_run:
                self.log(f"Would create directory: {directory}")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Created directory: {directory}")
    
    def plan_extract_module_migration(self):
        """Plan migrations for the extract module."""
        migrations = [
            # Coordinators
            ("extract/extract_coordinator.py", "src/extract/coordinator.py"),
            
            # PBD Core
            ("extract/pbd/io/scanner.py", "src/extract/pbd/scanner.py"),
            ("extract/pbd/structures/header.py", "src/extract/pbd/structures/header.py"),
            ("extract/pbd/structures/entry.py", "src/extract/pbd/structures/entry.py"),
            ("extract/pbd/structures/data_block.py", "src/extract/pbd/structures/data_block.py"),
            ("extract/pbd/structures/pbd_object.py", "src/extract/pbd/structures/object.py"),
            
            # Extractors
            ("extract/pbd/extraction/extractor.py", "src/extract/pbd/extractors/base.py"),
            ("extract/pbd/extraction/unified_resource_extractor.py", "src/extract/pbd/extractors/resource.py"),
            
            # Recovery
            ("extract/pbd/recovery/enhanced_recovery.py", "src/extract/pbd/recovery/checkpoint.py"),
            ("extract/pbd/structures/data_corruption_fix.py", "src/extract/pbd/recovery/corruption.py"),
            
            # Utils
            ("extract/pbd/utils/binary_utils.py", "src/extract/utils/binary.py"),
            ("extract/pbd/utils/powerbuilder_decoder.py", "src/extract/utils/encoding.py"),
            ("extract/pbd/utils/version_detector.py", "src/extract/utils/version.py"),
            ("common/utils/validation.py", "src/extract/utils/validation.py"),
        ]
        
        # Files to merge
        self.merges.extend([
            {
                "sources": [
                    "extract/pbd/io/file_operations.py",
                    "extract/pbd/io/pe_scanner.py",
                    "extract/pbd/io/resource_utils.py"
                ],
                "target": "src/extract/pbd/reader.py",
                "description": "Merge file operations into unified reader"
            },
            {
                "sources": [
                    "extract/pbd/extraction/string_extractor.py",
                    "extract/pbd/extraction/enhanced_image_extractor.py",
                    "extract/pbd/extraction/resource_extraction_manager.py"
                ],
                "target": "src/extract/pbd/extractors/binary.py",
                "description": "Merge binary extractors"
            }
        ])
        
        # Files to delete
        self.deletions.extend([
            "extract/pbd/structures/enhanced_data_block.py",
            "extract/pbd/structures/enhanced_entry_parser.py",
            "extract/pbd/extraction/library.py",
            "extract/pbd/extraction/resource_catalog.py",
            "extract/pbd/formatters/",
            "extract/pbd/analysis/",
        ])
        
        self.movements.extend(migrations)
    
    def plan_parse_module_migration(self):
        """Plan migrations for the parse module."""
        migrations = [
            # Coordinators
            ("parse/parse_coordinator.py", "src/parse/coordinator.py"),
            
            # Grammar
            ("parse/grammar.py", "src/parse/grammar/loader.py"),
            
            # Parsers
            ("parse/parsers/base_parser.py", "src/parse/parser/base.py"),
            ("parse/parsers/specialized/sql_parser.py", "src/parse/parser/sql.py"),
            
            # Transformers
            ("parse/transformers/powerbuilder_transformer.py", "src/parse/transformer/ast_builder.py"),
            ("parse/type_resolution.py", "src/parse/transformer/type_resolver.py"),
            ("parse/visitors/abstract_visitor.py", "src/parse/transformer/visitors/node_visitor.py"),
            ("parse/visitors/position_tracker.py", "src/parse/transformer/visitors/position_tracker.py"),
            
            # Preprocessor
            ("parse/pb_preprocessor.py", "src/parse/preprocessor/pb_preprocessor.py"),
            ("parse/implicit_import_resolver.py", "src/parse/preprocessor/import_resolver.py"),
            
            # Error Recovery
            ("parse/error_recovery/error_recovery.py", "src/parse/error_recovery/strategy.py"),
        ]
        
        # Grammar files
        for grammar_file in ["powerbuilder.lark", "datawindow.lark", "sql.lark", 
                            "common_grammar.lark", "pseudocode.lark"]:
            migrations.append((f"parse/grammar/{grammar_file}", 
                             f"src/parse/grammar/definitions/{grammar_file}"))
        
        # Merges
        self.merges.extend([
            {
                "sources": [
                    "parse/parsers/parser.py",
                    "parse/parsers/enhanced_parser.py"
                ],
                "target": "src/parse/parser/powerbuilder.py",
                "description": "Merge parser implementations"
            }
        ])
        
        # Deletions
        self.deletions.extend([
            "parse/interactive.py",
            "parse/debug.py",
            "parse/library.py",
            "parse/ast_to_model.py",
        ])
        
        self.movements.extend(migrations)
    
    def plan_decompile_module_migration(self):
        """Plan migrations for the decompile module."""
        migrations = [
            # Coordinator
            ("decompile/decompile_coordinator.py", "src/decompile/coordinator.py"),
            
            # P-code Core
            ("decompile/core/pcode_decoder.py", "src/decompile/pcode/decoder.py"),
            ("decompile/analyzers/pcode_detector.py", "src/decompile/pcode/detector.py"),
            ("decompile/opcodes/opcodes.py", "src/decompile/pcode/opcodes/definitions.py"),
            ("decompile/opcodes/opcode_variants.py", "src/decompile/pcode/opcodes/variants.py"),
            
            # Analysis
            ("decompile/analyzers/control_flow_analyzer.py", "src/decompile/analysis/control_flow.py"),
            ("model/optimization/expression_optimizer.py", "src/decompile/analysis/data_flow.py"),
            
            # Reconstruction
            ("decompile/core/expression_reconstructor.py", "src/decompile/reconstruction/expression.py"),
            
            # Extractors
            ("decompile/extractors/datawindow.py", "src/decompile/extractors/datawindow.py"),
            ("decompile/extractors/schema.py", "src/decompile/extractors/schema.py"),
            ("decompile/analyzers/business_logic_mapper.py", "src/decompile/extractors/business_logic.py"),
        ]
        
        # Merges
        self.merges.extend([
            {
                "sources": [
                    "decompile/core/output_formatter.py",
                    "decompile/core/simple_formatter.py"
                ],
                "target": "src/decompile/reconstruction/formatter.py",
                "description": "Merge formatter implementations"
            }
        ])
        
        # Deletions
        self.deletions.extend([
            "decompile/pdw/",
            "decompile/core/advanced_expression_reconstructor.py",
            "decompile/core/special_opcode_formatter.py",
            "decompile/core/post_processor.py",
        ])
        
        self.movements.extend(migrations)
    
    def plan_model_module_migration(self):
        """Plan migrations for the model module."""
        migrations = [
            # Coordinator
            ("model/core/model_coordinator.py", "src/model/coordinator.py"),
            
            # AST
            ("model/ast/ast_nodes.py", "src/model/ast/nodes/base.py"),
            ("model/ast/types.py", "src/model/ast/nodes/declarations.py"),
            ("model/ast/sql.py", "src/model/ast/nodes/sql.py"),
            
            # Entities
            ("model/entities/pb_application.py", "src/model/entities/application.py"),
            ("model/entities/pb_event.py", "src/model/entities/event.py"),
            ("model/entities/function_entities.py", "src/model/entities/function.py"),
            ("model/core/library.py", "src/model/entities/library.py"),
            
            # Types
            ("model/utils/type_inference.py", "src/model/types/inference.py"),
            ("model/utils/validation.py", "src/model/types/validation.py"),
            
            # Symbols
            ("model/utils/symbol_table.py", "src/model/symbols/table.py"),
            ("model/utils/scope.py", "src/model/symbols/scope.py"),
            ("model/cross_module_resolver.py", "src/model/symbols/resolver.py"),
            
            # Analysis
            ("model/core/analysis.py", "src/model/analysis/cross_reference.py"),
            ("model/security_analyzer.py", "src/model/analysis/security.py"),
        ]
        
        self.movements.extend(migrations)
    
    def plan_generate_module_migration(self):
        """Plan migrations for the generate module."""
        migrations = [
            # Coordinator
            ("generate/generate_coordinator.py", "src/generate/coordinator.py"),
            
            # UI Converters
            ("generate/converters/ui/ui_converter.py", "src/generate/converters/flutter/ui/widget_converter.py"),
            ("generate/converters/ui/datawindow_converter.py", "src/generate/converters/flutter/ui/datawindow_converter.py"),
            ("generate/converters/ui/menu_converter.py", "src/generate/converters/flutter/ui/menu_converter.py"),
            ("generate/layout_converter.py", "src/generate/converters/flutter/ui/layout_converter.py"),
            ("generate/converters/ui/design_system_converter.py", "src/generate/converters/flutter/ui/theme_converter.py"),
            
            # State Converters
            ("generate/converters/logic/event_converter.py", "src/generate/converters/flutter/state/event_converter.py"),
            ("generate/converters/utils/type_converter.py", "src/generate/converters/flutter/state/model_converter.py"),
            
            # Business Logic
            ("generate/converters/logic/method_body_converter.py", "src/generate/converters/flutter/business/logic_converter.py"),
            ("generate/converters/data/database_operation_formatter.py", "src/generate/converters/flutter/services/api_service.py"),
            
            # Templates & Mappings
            ("generate/template_validator.py", "src/generate/templates/engine.py"),
            ("generate/flutter/powerbuilder_flutter_mapping.json", "src/generate/mappings/powerbuilder_flutter_mapping.json"),
        ]
        
        # Template files
        template_files = [
            "main.dart.jinja2", "widget.dart.jinja2", "screen.dart.jinja2",
            "model.dart.jinja2", "pubspec.yaml.jinja2", "datawindow_widget.dart.jinja2",
            "menu_widget.dart.jinja2", "design_system.dart.jinja2"
        ]
        
        for template in template_files:
            migrations.append((f"generate/templates/flutter/{template}", 
                             f"src/generate/templates/flutter/{template}"))
        
        # Deletions
        self.deletions.extend([
            "generate/python/",
            "generate/python_ui_generator.py",
            "generate/templates/python/",
            "generate/test_generator.py",
            "generate/documentation_generator.py",
        ])
        
        self.movements.extend(migrations)
    
    def plan_common_module_migration(self):
        """Plan migrations for the common module."""
        migrations = [
            # Core
            ("common/types.py", "src/common/types.py"),
            ("common/exceptions.py", "src/common/exceptions.py"),
            ("common/constants.py", "src/common/constants.py"),
            
            # Utils
            ("common/logging_config.py", "src/common/utils/logging.py"),
        ]
        
        # Move all utils
        for util_file in ["file_utils.py", "string_utils.py", "cache.py"]:
            if (self.base_path / f"common/utils/{util_file}").exists():
                migrations.append((f"common/utils/{util_file}", f"src/common/utils/{util_file}"))
        
        self.movements.extend(migrations)
    
    def plan_test_reorganization(self):
        """Plan test reorganization."""
        test_mappings = [
            # Unit tests
            ("tests/test_extract/", "tests/unit/extract/"),
            ("tests/test_parse/", "tests/unit/parse/"),
            ("tests/test_decompile/", "tests/unit/decompile/"),
            ("tests/test_model/", "tests/unit/model/"),
            ("tests/test_generate/", "tests/unit/generate/"),
            
            # Integration tests
            ("tests/test_integration_", "tests/integration/test_"),
            ("tests/test_end_to_end_", "tests/integration/test_e2e_"),
            ("tests/test_pipeline_", "tests/integration/test_pipeline_"),
            
            # Fixtures
            ("tests/fixtures/", "tests/fixtures/"),
        ]
        
        for source_pattern, target_pattern in test_mappings:
            source_path = self.base_path / source_pattern
            if source_path.exists() and source_path.is_dir():
                for file in source_path.rglob("*.py"):
                    relative = file.relative_to(source_path)
                    target = target_pattern + str(relative)
                    self.movements.append((str(file.relative_to(self.base_path)), target))
    
    def execute_movements(self):
        """Execute all planned file movements."""
        self.log(f"Executing {len(self.movements)} file movements...")
        
        for source, target in self.movements:
            source_path = self.base_path / source
            target_path = self.base_path / target
            
            if not source_path.exists():
                self.log(f"Source file not found: {source}", "WARNING")
                continue
            
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use git mv to preserve history
            if self.execute_command(["git", "mv", str(source), str(target)]):
                self.log(f"Moved: {source} → {target}")
            else:
                self.log(f"Failed to move: {source}", "ERROR")
    
    def create_merge_files(self):
        """Create placeholder files for merges with instructions."""
        for merge in self.merges:
            target_path = self.base_path / merge["target"]
            
            if self.dry_run:
                self.log(f"Would create merge file: {merge['target']}")
                self.log(f"  Sources: {', '.join(merge['sources'])}")
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                merge_content = f'''"""
{merge['description']}

TODO: Merge the following files:
{chr(10).join(f"- {src}" for src in merge['sources'])}

This is a placeholder file created by the migration script.
"""

# Placeholder - merge implementations from source files
'''
                
                with open(target_path, 'w') as f:
                    f.write(merge_content)
                
                self.log(f"Created merge placeholder: {merge['target']}")
    
    def update_imports(self):
        """Update imports in all Python files."""
        self.log("Updating imports in all Python files...")
        
        # Build import mapping
        import_map = {}
        for old_path, new_path in self.movements:
            if old_path.endswith('.py') and new_path.endswith('.py'):
                old_import = old_path.replace('/', '.').replace('.py', '')
                new_import = new_path.replace('/', '.').replace('.py', '')
                import_map[old_import] = new_import
        
        # Update imports in all Python files
        for py_file in self.base_path.rglob("*.py"):
            if 'archive' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                updated = False
                for old_import, new_import in import_map.items():
                    # Handle various import patterns
                    patterns = [
                        (f'from {old_import}', f'from {new_import}'),
                        (f'import {old_import}', f'import {new_import}'),
                    ]
                    
                    for old_pattern, new_pattern in patterns:
                        if old_pattern in content:
                            content = content.replace(old_pattern, new_pattern)
                            updated = True
                
                if updated:
                    if not self.dry_run:
                        with open(py_file, 'w') as f:
                            f.write(content)
                    self.log(f"Updated imports in: {py_file.relative_to(self.base_path)}")
                    
            except Exception as e:
                self.log(f"Error updating imports in {py_file}: {str(e)}", "ERROR")
    
    def execute_deletions(self):
        """Execute planned deletions."""
        self.log(f"Executing {len(self.deletions)} deletions...")
        
        for path in self.deletions:
            full_path = self.base_path / path
            
            if not full_path.exists():
                continue
            
            if full_path.is_dir():
                if self.dry_run:
                    self.log(f"Would delete directory: {path}")
                else:
                    shutil.rmtree(full_path)
                    self.log(f"Deleted directory: {path}")
            else:
                if self.dry_run:
                    self.log(f"Would delete file: {path}")
                else:
                    full_path.unlink()
                    self.log(f"Deleted file: {path}")
    
    def create_init_files(self):
        """Create __init__.py files for all new directories."""
        self.log("Creating __init__.py files...")
        
        for directory in self.base_path.glob("src/**/*"):
            if directory.is_dir() and not (directory / "__init__.py").exists():
                init_file = directory / "__init__.py"
                if not self.dry_run:
                    init_file.write_text('"""Module initialization."""\n')
                self.log(f"Created: {init_file.relative_to(self.base_path)}")
    
    def generate_summary_report(self):
        """Generate a summary report of the migration."""
        report = f"""
# Migration Summary Report

## Statistics
- File movements: {len(self.movements)}
- File merges: {len(self.merges)}
- File deletions: {len(self.deletions)}
- Errors encountered: {len(self.errors)}

## Movements
{chr(10).join(f"- {src} → {tgt}" for src, tgt in self.movements[:10])}
... and {len(self.movements) - 10} more

## Merges Required
{chr(10).join(f"- {m['target']}: merge {len(m['sources'])} files" for m in self.merges)}

## Deletions
{chr(10).join(f"- {d}" for d in self.deletions[:10])}
... and {len(self.deletions) - 10} more

## Errors
{chr(10).join(self.errors)}

## Next Steps
1. Review and complete file merges
2. Run tests to ensure nothing is broken
3. Update documentation
4. Clean up any remaining empty directories
"""
        
        if not self.dry_run:
            with open("MIGRATION_REPORT.md", "w") as f:
                f.write(report)
        
        self.log(report)
    
    def run(self):
        """Execute the complete migration."""
        self.log("Starting codebase reorganization...")
        
        # Plan all migrations
        self.plan_extract_module_migration()
        self.plan_parse_module_migration()
        self.plan_decompile_module_migration()
        self.plan_model_module_migration()
        self.plan_generate_module_migration()
        self.plan_common_module_migration()
        self.plan_test_reorganization()
        
        # Execute steps
        self.create_directory_structure()
        self.execute_movements()
        self.create_merge_files()
        self.update_imports()
        self.execute_deletions()
        self.create_init_files()
        
        # Generate report
        self.generate_summary_report()
        
        self.log("Migration complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reorganize SIME Finch codebase structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup (not recommended)")
    
    args = parser.parse_args()
    
    if not args.no_backup and not args.dry_run:
        print("Creating backup...")
        backup_path = Path.cwd().parent / f"sime-finch-backup-{Path.cwd().stat().st_mtime}"
        shutil.copytree(Path.cwd(), backup_path, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        print(f"Backup created at: {backup_path}")
    
    reorganizer = CodebaseReorganizer(dry_run=args.dry_run)
    reorganizer.run()