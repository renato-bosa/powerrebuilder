#!/usr/bin/env python3
"""
More sophisticated syntax error fixer that handles specific patterns found in the codebase.
"""

import os
import ast
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

class AdvancedSyntaxFixer:
    def __init__(self, backup_dir: str = "syntax_backup_advanced"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.log_file = f"advanced_syntax_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.fixed_files = []
        self.failed_files = []
        
    def backup_file(self, filepath: Path) -> Path:
        """Create a backup of the file before modification."""
        backup_path = self.backup_dir / filepath.relative_to('src')
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        return backup_path
    
    def log(self, message: str):
        """Log messages to both console and file."""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {message}\n")
    
    def fix_detector_py(self, filepath: Path) -> bool:
        """Fix specific issues in detector.py"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Fix line 14: unmatched closing parenthesis
                if i == 13 and line.strip().startswith('confidence: float = 0.0)'):
                    # This looks like a method signature fragment
                    fixed_lines.append('class PCodeSection:\n')
                    fixed_lines.append('    """Information about a single P-code section."""\n')
                    fixed_lines.append('    \n')
                    fixed_lines.append('    def __init__(self, offset: int = 0, length: int = 0, ')
                    fixed_lines.append(line)
                    i += 1
                    continue
                
                # Fix line 19: incomplete return statement
                elif 'return f"PCodeSection(offset = 0x{' in line:
                    # Combine the multi-line f-string
                    combined = line.rstrip()
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().endswith(')"'):
                        combined += lines[j].strip()
                        j += 1
                    if j < len(lines):
                        combined += lines[j].strip()
                        j += 1
                    fixed_lines.append('    def __repr__(self):\n')
                    fixed_lines.append(f'        {combined}\n')
                    i = j
                    continue
                
                # Fix line 24: class definition without class keyword
                elif i == 23 and '"""Information about detected P-code."""' in line:
                    fixed_lines.append('\n')
                    fixed_lines.append('class PCodeInfo:\n')
                    fixed_lines.append(line)
                    i += 1
                    continue
                
                # Fix line 48: another class definition
                elif '"""Enhanced P-code detector for PowerBuilder objects."""' in line and not lines[i-1].strip().startswith('class'):
                    fixed_lines.append('\n')
                    fixed_lines.append('class PCodeDetector:\n')
                    fixed_lines.append(line)
                    i += 1
                    continue
                
                # Default: keep the line
                fixed_lines.append(line)
                i += 1
            
            # Write fixed content
            content = ''.join(fixed_lines)
            
            # Verify it's valid Python
            ast.parse(content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing {filepath}: {e}")
            return False
    
    def fix_parser_py(self, filepath: Path) -> bool:
        """Fix specific issues in parser.py"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for specific patterns and fix them
            lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(lines):
                # Fix unexpected indent issues
                if i > 0 and line.strip() and not lines[i-1].strip():
                    # Check if this line has unexpected indentation
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent > 0 and i > 1:
                        # Look for the previous non-empty line
                        prev_indent = 0
                        for j in range(i-1, -1, -1):
                            if lines[j].strip():
                                prev_indent = len(lines[j]) - len(lines[j].lstrip())
                                break
                        
                        # If indent jumped by more than 4, it might be an error
                        if current_indent - prev_indent > 4:
                            line = ' ' * (prev_indent + 4) + line.lstrip()
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Try to parse and fix any remaining issues
            try:
                ast.parse(content)
            except SyntaxError as e:
                # If there's still an error, try to fix it based on the error message
                if 'unexpected indent' in str(e):
                    # Remove all lines with unexpected indents
                    lines = content.split('\n')
                    fixed_lines = []
                    for line in lines:
                        if line.strip() or not line:  # Keep non-empty lines and truly empty lines
                            fixed_lines.append(line)
                    content = '\n'.join(fixed_lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing {filepath}: {e}")
            return False
    
    def fix_control_py(self, filepath: Path) -> bool:
        """Fix specific issues in control.py"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix common patterns in control flow analysis
            # Pattern 1: Fix incomplete class/function definitions
            content = re.sub(
                r'^\s*def\s+\w+\([^)]*$',
                lambda m: m.group(0) + '):', 
                content, 
                flags=re.MULTILINE
            )
            
            # Pattern 2: Fix missing colons
            content = re.sub(
                r'^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\s+[^:]+$',
                lambda m: m.group(0) + ':',
                content,
                flags=re.MULTILINE
            )
            
            # Pattern 3: Fix dangling else/elif
            lines = content.split('\n')
            fixed_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith(('else:', 'elif ')):
                    # Check if there's a matching if
                    found_if = False
                    indent = len(line) - len(line.lstrip())
                    for j in range(i-1, max(0, i-10), -1):
                        if lines[j].strip().startswith('if '):
                            prev_indent = len(lines[j]) - len(lines[j].lstrip())
                            if prev_indent == indent:
                                found_if = True
                                break
                    
                    if not found_if and line.strip().startswith('else:'):
                        # Add a dummy if
                        fixed_lines.append(' ' * indent + 'if True:')
                        fixed_lines.append(' ' * (indent + 4) + 'pass')
                    elif not found_if and line.strip().startswith('elif '):
                        # Convert elif to if
                        line = line.replace('elif ', 'if ', 1)
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Verify and write
            ast.parse(content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing {filepath}: {e}")
            return False
    
    def fix_file(self, filepath: Path) -> bool:
        """Fix syntax errors in a single file."""
        try:
            # Check if file has syntax errors
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            try:
                ast.parse(original_content)
                return True  # No syntax errors
            except SyntaxError as e:
                self.log(f"\nProcessing {filepath}")
                self.log(f"  Original error: {e}")
            
            # Create backup
            backup_path = self.backup_file(filepath)
            self.log(f"  Backup created: {backup_path}")
            
            # Apply specific fixes based on filename
            success = False
            if filepath.name == 'detector.py':
                success = self.fix_detector_py(filepath)
            elif filepath.name == 'parser.py':
                success = self.fix_parser_py(filepath)
            elif filepath.name == 'control.py':
                success = self.fix_control_py(filepath)
            else:
                # Try generic fixes
                success = self.apply_generic_fixes(filepath)
            
            if success:
                # Verify the fix
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                    self.log(f"  ✓ Successfully fixed!")
                    self.fixed_files.append(filepath)
                    return True
                except SyntaxError as e:
                    self.log(f"  Still has errors after fix: {e}")
                    # Restore from backup
                    shutil.copy2(backup_path, filepath)
                    self.failed_files.append((filepath, str(e)))
                    return False
            else:
                # Restore from backup
                shutil.copy2(backup_path, filepath)
                self.failed_files.append((filepath, "Could not apply fixes"))
                return False
                
        except Exception as e:
            self.log(f"  Error processing {filepath}: {e}")
            self.failed_files.append((filepath, str(e)))
            return False
    
    def apply_generic_fixes(self, filepath: Path) -> bool:
        """Apply generic fixes to a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix common patterns
            # 1. Add missing colons
            content = re.sub(
                r'^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\s+[^:]+$',
                lambda m: m.group(0) + ':',
                content,
                flags=re.MULTILINE
            )
            
            # 2. Fix incomplete function definitions
            content = re.sub(
                r'^\s*def\s+\w+\([^)]*$',
                lambda m: m.group(0) + '):', 
                content, 
                flags=re.MULTILINE
            )
            
            # 3. Remove extra closing parentheses
            lines = content.split('\n')
            fixed_lines = []
            paren_count = 0
            
            for line in lines:
                # Count parentheses
                for char in line:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                
                # If we have extra closing parentheses, remove them
                if paren_count < 0 and ')' in line:
                    line = line.replace(')', '', -paren_count)
                    paren_count = 0
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Write the fixed content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception:
            return False
    
    def run(self, specific_files: Optional[List[str]] = None):
        """Run the fixer on specific files or find all files with errors."""
        if specific_files:
            # Process specific files
            for file_path in specific_files:
                filepath = Path(file_path)
                if filepath.exists():
                    self.fix_file(filepath)
        else:
            # Find all files with syntax errors
            self.log("Scanning for files with syntax errors...")
            error_files = []
            
            for root, dirs, files in os.walk('src'):
                for file in files:
                    if file.endswith('.py'):
                        filepath = Path(root) / file
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                ast.parse(f.read())
                        except SyntaxError:
                            error_files.append(filepath)
                        except Exception:
                            pass
            
            self.log(f"Found {len(error_files)} files with syntax errors")
            
            # Process each file
            for filepath in error_files:
                self.fix_file(filepath)
        
        # Summary
        self.log("\n" + "="*60)
        self.log("SUMMARY")
        self.log("="*60)
        self.log(f"Files successfully fixed: {len(self.fixed_files)}")
        for f in self.fixed_files:
            self.log(f"  ✓ {f}")
        
        self.log(f"\nFiles that need manual fixing: {len(self.failed_files)}")
        for f, error in self.failed_files:
            self.log(f"  ✗ {f}: {error}")
        
        self.log(f"\nBackups saved to: {self.backup_dir}")
        self.log(f"Log saved to: {self.log_file}")


def main():
    """Main entry point."""
    import sys
    
    fixer = AdvancedSyntaxFixer()
    
    # Start with the most problematic files
    specific_files = [
        'src/decompile/pcode/detector.py',
        'src/decompile/analyzers/parser.py',
        'src/decompile/analysis/control.py',
        'src/decompile/reconstruction/expression.py',
        'src/decompile/pcode/recovery.py',
    ]
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        fixer.run()
    else:
        fixer.run(specific_files=specific_files)


if __name__ == '__main__':
    main()