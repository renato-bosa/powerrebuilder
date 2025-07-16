#!/bin/bash
# Cleanup outdated documentation files

cd /Users/michael/Projects/powerrebuilder/docs

# Delete all dated files (except VERSION_LOG.md)
find . -name "*2025-*-*.md" ! -name "VERSION_LOG.md" -delete
find . -name "*2025_*_*.md" -delete

# Delete analysis files
rm -f decompilation_analysis.md \
      import_analysis_report.md \
      datawindow_failure_analysis.md \
      pcode_format_analysis.md \
      pcode_extraction_debug_report.md \
      pipeline_architecture_analysis.md \
      event_return_type_handling.md \
      sql_transformer_todo.md \
      analysis_missing_sql_transformers.md \
      code_health_report.md \
      code_quality_report.md \
      pipeline_success_report.md \
      parser_to_ast_plan.md \
      business_logic_extraction_report.md \
      abstract_visitor_import_fixes.md \
      parse_module_cleanup.md \
      dead_code_report.txt

# Delete temporary and work files
rm -f TODO_2025-06-22.md \
      REDUNDANCY_CLEANUP_2025-06-28.md \
      todos_and_stubs.txt \
      PROJECT_TREE.md \
      extraction_analysis.json

# Delete old/redundant files
rm -f README_COMPREHENSIVE.md \
      REFERENCE.md \
      project_structure_guide.md \
      index.md \
      gen_ref_pages.py \
      PARSE_DECOMPILE_ANALYSIS.md \
      EXTRACTION_WARNINGS_AND_ERRORS.md \
      MODEL_MODULE_ANALYSIS.md \
      DATACLASS_INVENTORY.md \
      GENERATOR_UPDATE_SUMMARY.md \
      DECOMPILER_ENHANCEMENTS_SUMMARY.md \
      STUB_IMPLEMENTATION_SUMMARY.md \
      DECOMPILATION_ENHANCEMENTS.md \
      TEMPLATE_IMPROVEMENTS.md \
      PERFORMANCE_IMPROVEMENTS.md \
      IMPORT_FIXES_SUMMARY.md \
      PROJECT_HISTORY.md

# Delete build/reorganization files
rm -f BUILD_ARTIFACTS_CLEANUP.md \
      DATA_REORGANIZATION.md \
      DOCUMENTATION_CLEANUP.md \
      SPECIFIC_FILE_CONSOLIDATION.md \
      ROOT_REORGANIZATION_REPORT.md

# Delete sprint planning docs (keep only summary)
rm -rf sprint-planning/update-tracker.py

# Keep these essential files:
# - README.md
# - ARCHITECTURE.md  
# - API_REFERENCE.md
# - QUICK_REFERENCE.md
# - PIPELINE_ARCHITECTURE.md
# - POWERBUILDER_CONVERSION_GUIDE.md
# - STATUS.md
# - BUG_REFERENCE.md
# - ROADMAP.md
# - SCHEMAS.md
# - VERSION_LOG.md
# - CHANGELOG.md
# - DEPLOYMENT.md
# - SECURITY.md
# - PERFORMANCE.md
# - DATA_FLOW.md
# - API.md (needs update)
# - DEVELOPMENT.md (needs update)
# - CONFIG_FILES.md

echo "Documentation cleanup complete!"
echo "Remaining documentation files:"
find . -name "*.md" -type f | sort