#!/usr/bin/env python
"""Fix all remaining G004 and G201 logging issues."""

import subprocess
import re
from pathlib import Path

def get_logging_issues() -> list:


    

    """Get all G004 and G201 issues from ruff."""
    result = subprocess.run(
        ["ruff", "check", ".", "--select", "G004,G201", "--no-cache"],
        capture_output=True,
        text=True
    )
    
    issues = []
    for line in result.stderr.strip().split('\n'):
        if ':' in line and ('.py:' in line):
            # Parse the file:line:col: error format
            match = re.match(r'(.+\.py):(\d+):(\d+): (G\d+)', line)
            if match:
                issues.append({
                    'file': match.group(1),
                    'line': int(match.group(2)),
                    'col': int(match.group(3)),
                    'code': match.group(4)
                })
    
    return issues

def fix_g004_issue(file_path, line_num) -> None:


    

    """Fix a G004 issue at a specific line."""
    lines = Path(file_path).read_text().splitlines()
    
    # Find the logger statement starting from line_num - 1
    start_line = line_num - 1
    
    # Find the complete logger statement (may span multiple lines)
    end_line = start_line
    paren_count = 0
    in_statement = False
    
    for i in range(start_line, len(lines)):
        line = lines[i]
        if 'logger' in line or 'logging' in line or in_statement:
            in_statement = True
            paren_count += line.count('(') - line.count(')')
            if paren_count == 0 and in_statement:
                end_line = i
                break
    
    # Extract the complete statement
    statement_lines = lines[start_line:end_line + 1]
    statement = '\n'.join(statement_lines)
    
    # Fix f-string formatting
    if 'f"' in statement or "f'" in statement:
        # Extract the logging method and f-string content
        pattern = r'(logger\.\w+|logging\.\w+)\s*\(\s*(f["\'].*?["\'])\s*\)'
        
        # Handle multi-line f-strings
        f_string_content = []
        params = []
        
        for line in statement_lines:
            if 'f"' in line or "f'" in line:
                # Extract expressions from f-string
                expr_pattern = r'\{([^}:]+)(?::[^}]+)?\}'
                
                # Find all expressions
                for match in re.finditer(expr_pattern, line):
                    expr = match.group(1)
                    params.append(expr)
                
                # Replace expressions with format specifiers
                new_line = line
                
                # Replace formatted expressions like {expr:.2f} with %.2f
                new_line = re.sub(r'\{[^}:]+:\.(\d+)f\}', r'%.\\1f', new_line)
                new_line = re.sub(r'\{[^}:]+:(\d+)d\}', r'%\\1d', new_line)
                new_line = re.sub(r'\{[^}:]+:0(\d+)[xX]\}', r'%0\\1X', new_line)
                new_line = re.sub(r'\{[^}:]+:[xX]\}', r'%x', new_line)
                
                # Replace simple expressions with %s
                new_line = re.sub(r'\{[^}]+\}', '%s', new_line)
                
                # Remove f prefix
                new_line = new_line.replace('f"', '"').replace("f'", "'")
                
                f_string_content.append(new_line)
            else:
                f_string_content.append(line)
        
        # Reconstruct the statement
        if params:
            # Add parameters after the string
            if len(f_string_content) == 1:
                # Single line
                new_statement = f_string_content[0].rstrip(')')
                new_statement += ', ' + ', '.join(params) + ')'
                lines[start_line] = new_statement
                for i in range(start_line + 1, end_line + 1):
                    lines[i] = ''
            else:
                # Multi-line - add params to last line
                last_line_idx = end_line
                lines[last_line_idx] = lines[last_line_idx].rstrip(')') + ',\n' + ' ' * 8 + ',\n'.join(' ' * 8 + p for p in params) + '\n' + ' ' * 4 + ')'
                
                # Fix the f-string lines
                for i, new_line in enumerate(f_string_content[:
                    -1]):
                    if i + start_line < len(lines):
                        lines[i + start_line] = new_line
        
        # Write back
        Path(file_path).write_text('\n'.join(lines) + '\n')
        return True
    
    return False

def fix_g201_issue(file_path, line_num) -> bool:


    

    """Fix a G201 issue (use .exception instead of .error(..., exc_info=True))."""
    lines = Path(file_path).read_text().splitlines()
    
    if line_num - 1 < len(lines):
        line = lines[line_num - 1]
        if '.error(' in line and 'exc_info=True' in line:
            # Replace .error with .exception and remove exc_info=True
            new_line = line.replace('.error(', '.exception(')
            new_line = re.sub(r',\s*exc_info=True', '', new_line)
            lines[line_num - 1] = new_line
            
            Path(file_path).write_text('\n'.join(lines) + '\n')
            return True
    
    return False

def main() -> None:


    

    """Fix all logging issues."""
    issues = get_logging_issues()
    
    print(f"Found {len(issues)} logging issues to fix")
    
    # Group by file
    files_to_fix = {}
    for issue in issues:
        if issue['file'] not in files_to_fix:
            files_to_fix[issue['file']] = []
        files_to_fix[issue['file']].append(issue)
    
    # Fix issues file by file
    for file_path, file_issues in files_to_fix.items():
        print(f"\nFixing {file_path}...")
        
        # Sort by line number in reverse order to avoid line number shifts
        file_issues.sort(key=lambda x: x['line'], reverse=True)
        
        for issue in file_issues:
            if issue['code'] == 'G004':
                if fix_g004_issue(file_path, issue['line']):
                    print(f"  Fixed G004 at line {issue['line']}")
            elif issue['code'] == 'G201':
                if fix_g201_issue(file_path, issue['line']):
                    print(f"  Fixed G201 at line {issue['line']}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()