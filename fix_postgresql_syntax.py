#!/usr/bin/env python3
"""
Fix PostgreSQL Syntax in All Agents
Converts SQLite ? parameters to PostgreSQL %s parameters
"""
import os
import re
from pathlib import Path

def fix_file_postgresql_syntax(file_path):
    """Fix PostgreSQL syntax issues in a single file"""
    print(f"🔧 Fixing {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Fix 1: Replace ? with %s in SQL queries (but not in regex patterns)
        # This is a more careful replacement that looks for SQL context
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip lines that are clearly regex patterns or comments
            if 're.search(' in line or 're.match(' in line or line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
                
            # Look for SQL query patterns with ? parameters
            if ('execute(' in line or 'executemany(' in line) and '?' in line:
                # Replace ? with %s in SQL queries
                # Count the number of ? to ensure we're in SQL context
                question_marks = line.count('?')
                if question_marks > 0 and ('SELECT' in line.upper() or 'INSERT' in line.upper() or 
                                          'UPDATE' in line.upper() or 'WHERE' in line.upper()):
                    line = line.replace('?', '%s')
                    changes_made += 1
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Remove any remaining PRAGMA statements (they should be handled by db_config)
        if 'PRAGMA foreign_keys' in content:
            content = re.sub(r'c\.execute\("PRAGMA foreign_keys = ON;"\)\s*\n', '', content)
            changes_made += 1
        
        # Fix 3: Fix any double quotes in SQL string literals to single quotes
        content = re.sub(r"= \"([^\"]+)\"", r"= '\1'", content)
        
        if changes_made > 0:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Made {changes_made} changes")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix PostgreSQL syntax in all agent files"""
    print("🔧 Fixing PostgreSQL Syntax in All Agents")
    print("=" * 60)
    
    agent_dir = Path("agents/team_strength")
    
    if not agent_dir.exists():
        print(f"❌ Agent directory not found: {agent_dir}")
        return
    
    files_fixed = 0
    files_processed = 0
    
    # Process all Python files in the agent directory
    for agent_file in agent_dir.glob("*.py"):
        files_processed += 1
        if fix_file_postgresql_syntax(agent_file):
            files_fixed += 1
    
    # Also fix shared utilities
    shared_dir = Path("agents/shared")
    if shared_dir.exists():
        for shared_file in shared_dir.glob("*.py"):
            files_processed += 1
            if fix_file_postgresql_syntax(shared_file):
                files_fixed += 1
    
    print(f"\n📊 Summary:")
    print(f"Files processed: {files_processed}")
    print(f"Files fixed: {files_fixed}")
    
    if files_fixed > 0:
        print(f"\n✅ PostgreSQL syntax fixes complete!")
        print(f"Now test agents individually.")
    else:
        print(f"\nℹ️  No syntax issues found.")

if __name__ == "__main__":
    main()