#!/usr/bin/env python3
"""Fix try/except block syntax correctly."""

import sys
from pathlib import Path


def fix_file_manually(file_path: Path, fixes: list[tuple[int, str]]) -> bool:
    """Apply specific fixes to a file at given line numbers.
    
    Args:
        file_path: Path to file
        fixes: List of (line_number, replacement_line) tuples
        
    Returns:
        True if successful
    """
    try:
        lines = file_path.read_text(encoding='utf-8').split('\n')
        
        # Apply fixes (in reverse order to preserve line numbers)
        for line_num, replacement in sorted(fixes, reverse=True):
            if 0 <= line_num < len(lines):
                lines[line_num] = replacement
        
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main() -> None:
    """Fix specific files with known issues."""
    root = Path(__file__).parent.parent
    
    fixes_map = {
        'scripts/fix_remaining_syntax_errors.py': [
            # Remove the duplicate try: on line 112
            (112, '            '),  # Remove duplicate try:
            (113, ''),  # Empty line
            # Line 114 already has except, just needs to be uncommented properly
        ],
        'scripts/fix_final_type_issues.py': [
            # Remove the duplicate try: on line 72
            (72, '            '),  # Remove duplicate try:
            (73, ''),  # Empty line
            # Line 74 already has except
        ],
        'scripts/fix_more_syntax_errors.py': [
            # Remove the duplicate try: on line 174
            (174, '            '),  # Remove duplicate try:
            (175, ''),  # Empty line  
            # Line 176 already has except
        ],
        'generate/template_schemas.py': [
            # Remove the orphaned try:
            (320, '        return _dataclass_to_dict(validated)'),
            (321, '    except Exception as e:'),
            (322, '        raise ValueError(f"Template context validation failed for {template_name}: {e}")'),
        ],
        'decompile/decompile_coordinator.py': [
            # Fix all the orphaned try: blocks
            (268, '                    output_path = self.output_dir / f"{object_name}{output_ext}"'),
            (290, ''),  # Remove orphaned try:
            (291, '        except Exception as e:'),
            (292, '            logger.error("Failed to decompile %s: %s", file_path, e, exc_info=True)'),
            (293, '            return False'),
            
            (382, '                    output_path = self.output_dir / f"{object_name}{output_ext}"'),
            (499, ''),  # Remove orphaned try:
            (500, '        except Exception as e:'),
            (501, '            logger.error("Failed to decompile %s: %s", pbd_path, e, exc_info=True)'),
            
            (586, ''),  # Remove orphaned try:
            (587, '        except Exception as e:'),
            (588, '            logger.exception("Failed to decompile %s: %s", entry.objectname, e)'),
            
            (674, ''),  # Remove orphaned try:
            (675, '        except Exception as e:'),
            (676, '            logger.exception("Failed to extract DataWindow %s: %s", entry.objectname, e)'),
            
            (763, '        '),
            (764, '    except Exception as e:'),
            (765, '        logger.error("Failed to extract database schema: %s", e, exc_info=True)'),
            
            (843, '                        failed_count += 1'),
            (844, '                except Exception as e:'),
            
            (863, '                    failed_count += 1'),
            (864, '            except Exception as e:'),
        ],
        'model/utils/type_checker.py': [
            # Already has proper try blocks, just needs except indentation
            # No changes needed - the existing except blocks are correct
        ]
    }
    
    updated_count = 0
    for file_path, fixes in fixes_map.items():
        full_path = root / file_path
        if full_path.exists() and fixes:
            print(f"Fixing {file_path}...")
            if fix_file_manually(full_path, fixes):
                print(f"✓ Fixed {file_path}")
                updated_count += 1
    
    print(f"\nCompleted! Fixed {updated_count} files.")
    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)