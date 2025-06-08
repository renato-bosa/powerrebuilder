# Docs Folder Analysis Report

## Date: June 4, 2025

This document details the analysis of the `@docs/` folder, identifying redundant documentation and organizational issues.

## Major Overlapping Documents Found

### 1. Architecture Documentation (3 files)
- **architecture.md**: General architecture overview
- **architecture-mermaid.md**: Architecture with Mermaid diagrams
- **pipeline_architecture.md**: Detailed pipeline architecture

**Analysis**: These serve different purposes and complement each other:
- architecture.md is a text overview
- architecture-mermaid.md adds visual diagrams
- pipeline_architecture.md goes deeper into the pipeline specifics
**Recommendation**: Keep all three but add cross-references between them

### 2. Roadmap Documentation (2 files)
- **development_roadmap.md**: Quarterly milestones for v0.1.0 to v1.0
- **implementation_roadmap.md**: P-code implementation specific roadmap

**Analysis**: These serve different purposes:
- development_roadmap.md is high-level project planning
- implementation_roadmap.md is specific to decompiler implementation
**Recommendation**: Keep both but clarify their distinct purposes

### 3. Project Structure Documentation (2 files)
- **project_structure_map.md**: Detailed file-by-file description
- **project_structure_overview.md**: High-level directory overview

**Analysis**: Significant overlap - both describe the project structure
**Recommendation**: Merge into one comprehensive document

### 4. Changelog Files
- **changelog.md**: Current changelog
- **changelog old.md**: Old changelog (145KB!)

**Analysis**: "changelog old.md" appears to be a backup
**Recommendation**: Move to backup folder or archive

### 5. Session Notes (2 files)
- **session_notes_2024.md**: 2024 development notes
- **session_notes_2025_06_03.md**: Recent session notes

**Analysis**: Historical development records
**Recommendation**: Keep in an archive subfolder

### 6. Opcode Documentation (6 files)
- **OPCODE_DISCOVERY_TOOLS.md**: Tools for discovering opcodes
- **OPCODE_FIX_SUMMARY.md**: Summary of opcode fixes
- **opcode_discovery_automation.md**: Automation pipeline details
- **opcode_discovery_lessons.md**: Lessons learned
- **opcode_reference.md**: Opcode reference documentation
- **opcode_remediation_plan.md**: Plan for fixing opcodes

**Analysis**: Multiple overlapping documents about opcode discovery/fixing
**Recommendation**: Consolidate into 2-3 focused documents

### 7. Analysis Subfolder
Contains:
- opcode_analysis_report.md
- opcode_analysis_summary.md
- pcode_extraction_debug_report.md

**Analysis**: More opcode-related documentation scattered in subfolder
**Recommendation**: Consolidate with main opcode docs

## Other Documents (Well-Organized)
These documents serve clear, distinct purposes:
- README.md - Main documentation hub
- TODO_Phases.md - Phase-based task tracking
- comprehensive_project_review.md - Project review
- decompilation_progress.md - Decompilation status
- parsing_phase_plan.md - Parser planning
- powerbuilder_file_extensions.md - Reference info
- style_guide.txt - Coding standards
- technical_analysis.md - Technical details
- folder_reorganization_summary.md - Recent reorg summary
- implementation_comparison.md - Comparing implementations
- pipeline_diagram_simple.md - Simple pipeline diagram
- code_consolidation_summary.md - Recent consolidation work
- decompile_folder_analysis.md - Recent analysis

## Recommendations Summary

### 1. Create Archive Subfolder
Move historical/old documents:
- changelog old.md → docs/archive/
- session_notes_2024.md → docs/archive/
- session_notes_2025_06_03.md → docs/archive/

### 2. Consolidate Opcode Documentation
Merge the 9 opcode-related files into 3 focused documents:
- **opcode_reference.md**: Technical reference (keep as-is)
- **opcode_discovery_guide.md**: Merge tools, automation, lessons
- **opcode_fixes_summary.md**: Merge fix summary and remediation plan

### 3. Merge Project Structure Docs
Combine project_structure_map.md and project_structure_overview.md into:
- **project_structure.md**: Single comprehensive guide

### 4. Add Cross-References
Update architecture files to reference each other:
- Add links between architecture.md, architecture-mermaid.md, and pipeline_architecture.md

### 5. Create Index
Add an index.md or update README.md with a clear table of contents organizing all documentation by category.

## Summary

The docs folder contains 30+ files with significant overlap in several areas. By consolidating the opcode documentation (9→3 files), merging project structure docs (2→1), and archiving old files, we can reduce confusion and improve organization. The proposed changes would reduce the document count by approximately 10 files while maintaining all important information.