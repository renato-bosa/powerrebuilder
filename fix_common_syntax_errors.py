#!/usr/bin/env python3
"""
Automated script to fix common syntax errors in Python files.
Backs up files before modification and logs all changes.
"""

import os
import ast
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict

class SyntaxErrorFixer:
    def __init__(self, backup_dir: str = "syntax_backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.log_file = f"syntax_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.fixed_files = []
        self.failed_files = []
        self.patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for common syntax errors."""
        return {
            # Pattern 1: else without if (preceded by return/pass/continue/break)
            'dangling_else': re.compile(
                r'^(\s*)(return\s+.*?|pass|continue|break)\s*\n(\s*)else\s*:',
                re.MULTILINE
            ),
            
            # Pattern 2: elif without if
            'dangling_elif': re.compile(
                r'^(\s*)(return\s+.*?|pass|continue|break)\s*\n(\s*)elif\s+(.+?)\s*:',
                re.MULTILINE
            ),
            
            # Pattern 3: Unmatched closing parenthesis in imports
            'import_paren': re.compile(
                r'from\s+[\w.]+\s+import\s*\([^)]+\n[^)]+\n\s*\)',
                re.MULTILINE | re.DOTALL
            ),
            
            # Pattern 4: Missing colon after control statement
            'missing_colon': re.compile(
                r'^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\s+[^:]+$',
                re.MULTILINE
            ),
            
            # Pattern 5: Code after return statement at same indentation
            'code_after_return': re.compile(
                r'^(\s*)return\s+.*?\n(\1)(?![\s\n]).*$',
                re.MULTILINE
            ),
            
            # Pattern 6: Incorrect indentation after control statement
            'bad_indent': re.compile(
                r'^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with).*:\s*\n(\s*)(?=\S)',
                re.MULTILINE
            ),
            
            # Pattern 7: Missing comma in multi-line structures
            'missing_comma': re.compile(
                r'(\w+|"[^"]+"|\'[^\']+\')\s*\n\s*(\w+|"[^"]+"|\'[^\']+\')\s*[,\]\)]',
                re.MULTILINE
            ),
            
            # Pattern 8: Extra closing parenthesis
            'extra_paren': re.compile(
                r'^\s*\)\s*$',
                re.MULTILINE
            ),
        }
    
    def backup_file(self, filepath: Path) -> Path:
        """Create a backup of the file before modification."""
        backup_path = self.backup_dir / filepath.name
        if backup_path.exists():
            # Add timestamp if backup already exists
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"
        shutil.copy2(filepath, backup_path)
        return backup_path
    
    def log(self, message: str):
        """Log messages to both console and file."""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {message}\n")
    
    def fix_dangling_else(self, content: str) -> Tuple[str, List[str]]:
        """Fix else statements without matching if."""
        changes = []
        
        def replace_dangling_else(match):
            indent1, statement, indent2 = match.groups()[:3]
            changes.append(f"Added 'if True:' before dangling else at line")
            return f"{indent1}{statement}\n{indent2}if True:\n{indent2}    pass\n{indent2}else:"
        
        fixed = self.patterns['dangling_else'].sub(replace_dangling_else, content)
        return fixed, changes
    
    def fix_dangling_elif(self, content: str) -> Tuple[str, List[str]]:
        """Fix elif statements without matching if."""
        changes = []
        
        def replace_dangling_elif(match):
            indent1, statement, indent2, condition = match.groups()
            changes.append(f"Converted dangling elif to if at line")
            return f"{indent1}{statement}\n{indent2}if {condition}:"
        
        fixed = self.patterns['dangling_elif'].sub(replace_dangling_elif, content)
        return fixed, changes
    
    def fix_import_parentheses(self, content: str) -> Tuple[str, List[str]]:
        """Fix unmatched parentheses in import statements."""
        changes = []
        lines = content.split('\n')
        fixed_lines = []
        in_import = False
        paren_count = 0
        import_start = -1
        
        for i, line in enumerate(lines):
            if 'from' in line and 'import' in line and '(' in line:
                in_import = True
                import_start = i
                paren_count = line.count('(') - line.count(')')
            elif in_import:
                paren_count += line.count('(') - line.count(')')
                if paren_count < 0:
                    # Extra closing parenthesis
                    line = line.replace(')', '', 1)
                    changes.append(f"Removed extra closing parenthesis at line {i+1}")
                    paren_count = 0
                    in_import = False
                elif paren_count == 0:
                    in_import = False
            
            fixed_lines.append(line)
        
        # Check for unclosed imports
        if in_import and paren_count > 0:
            fixed_lines[import_start] += ')' * paren_count
            changes.append(f"Added {paren_count} closing parenthesis to import at line {import_start+1}")
        
        return '\n'.join(fixed_lines), changes
    
    def fix_missing_colons(self, content: str) -> Tuple[str, List[str]]:
        """Add missing colons after control statements."""
        changes = []
        
        def add_colon(match):
            full_match = match.group(0)
            if not full_match.rstrip().endswith(':'):
                changes.append(f"Added missing colon after control statement")
                return full_match.rstrip() + ':'
            return full_match
        
        fixed = self.patterns['missing_colon'].sub(add_colon, content)
        return fixed, changes
    
    def fix_code_after_return(self, content: str) -> Tuple[str, List[str]]:
        """Fix code after return statements."""
        changes = []
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            if i < len(lines) - 1:
                current_indent = len(line) - len(line.lstrip())
                if line.strip().startswith('return'):
                    next_line = lines[i + 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent == current_indent and next_line.strip():
                        # Code at same indentation after return
                        changes.append(f"Indented code after return statement at line {i+2}")
                        lines[i + 1] = '    ' + next_line
        
        return '\n'.join(fixed_lines), changes
    
    def fix_indentation(self, content: str) -> Tuple[str, List[str]]:
        """Fix common indentation errors."""
        changes = []
        lines = content.split('\n')
        fixed_lines = []
        expected_indent = 0
        indent_stack = [0]
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            current_indent = len(line) - len(stripped)
            
            # Check if this line should be dedented
            if stripped.startswith(('else:', 'elif ', 'except:', 'finally:')):
                if indent_stack and current_indent > indent_stack[-1]:
                    new_indent = indent_stack[-1] if indent_stack else 0
                    line = ' ' * new_indent + stripped
                    changes.append(f"Fixed indentation for {stripped.split()[0]} at line {i+1}")
            
            # Update expected indentation
            if stripped.endswith(':') and not stripped.startswith('#'):
                indent_stack.append(current_indent)
                expected_indent = current_indent + 4
            elif current_indent < indent_stack[-1]:
                # Dedent
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), changes
    
    def fix_file(self, filepath: Path) -> bool:
        """Fix syntax errors in a single file."""
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Check if file has syntax errors
            try:
                ast.parse(original_content)
                return True  # No syntax errors
            except SyntaxError:
                pass  # Continue with fixes
            
            # Create backup
            backup_path = self.backup_file(filepath)
            self.log(f"\nProcessing {filepath}")
            self.log(f"  Backup created: {backup_path}")
            
            # Apply fixes
            content = original_content
            all_changes = []
            
            # Apply each fix type
            for fix_name, fix_func in [
                ('dangling else', self.fix_dangling_else),
                ('dangling elif', self.fix_dangling_elif),
                ('import parentheses', self.fix_import_parentheses),
                ('missing colons', self.fix_missing_colons),
                ('code after return', self.fix_code_after_return),
                ('indentation', self.fix_indentation),
            ]:
                content, changes = fix_func(content)
                if changes:
                    all_changes.extend([f"{fix_name}: {change}" for change in changes])
            
            # Verify fixes
            try:
                ast.parse(content)
                # Write fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"  Successfully fixed {len(all_changes)} issues:")
                for change in all_changes:
                    self.log(f"    - {change}")
                self.fixed_files.append(filepath)
                return True
            except SyntaxError as e:
                self.log(f"  Failed to fix completely: {e}")
                # Restore from backup
                shutil.copy2(backup_path, filepath)
                self.failed_files.append((filepath, str(e)))
                return False
                
        except Exception as e:
            self.log(f"  Error processing {filepath}: {e}")
            self.failed_files.append((filepath, str(e)))
            return False
    
    def find_files_with_errors(self, directory: str = 'src') -> List[Path]:
        """Find all Python files with syntax errors."""
        error_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        ast.parse(content)
                    except SyntaxError:
                        error_files.append(filepath)
                    except Exception:
                        pass  # Skip files we can't read
        
        return error_files
    
    def run(self, directory: str = 'src', test_mode: bool = False):
        """Run the syntax error fixer on all Python files in directory."""
        self.log(f"Starting syntax error scan in '{directory}'...")
        
        # Find files with errors
        error_files = self.find_files_with_errors(directory)
        self.log(f"Found {len(error_files)} files with syntax errors")
        
        if test_mode and len(error_files) > 5:
            error_files = error_files[:5]
            self.log("Test mode: Processing only first 5 files")
        
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
        
        self.log(f"\nFiles that couldn't be fixed automatically: {len(self.failed_files)}")
        for f, error in self.failed_files:
            self.log(f"  ✗ {f}: {error}")
        
        self.log(f"\nBackups saved to: {self.backup_dir}")
        self.log(f"Log saved to: {self.log_file}")
        
        return len(self.fixed_files), len(self.failed_files)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix common Python syntax errors')
    parser.add_argument('--directory', '-d', default='src', help='Directory to scan (default: src)')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode: process only 5 files')
    parser.add_argument('--backup-dir', '-b', default='syntax_backup', help='Backup directory')
    
    args = parser.parse_args()
    
    fixer = SyntaxErrorFixer(backup_dir=args.backup_dir)
    fixed, failed = fixer.run(directory=args.directory, test_mode=args.test)
    
    # Exit with error code if some files couldn't be fixed
    sys.exit(1 if failed > 0 else 0)


if __name__ == '__main__':
    main()