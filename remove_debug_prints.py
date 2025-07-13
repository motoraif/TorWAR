#!/usr/bin/env python3
"""
Script to remove DEBUG print statements from TorWAR
Author: Mohamed Toraif
"""

import re
import os
import shutil

def remove_debug_prints():
    """Remove or replace DEBUG print statements."""
    
    # Backup original file
    shutil.copy('app.py', 'app.py.backup')
    print("✅ Created backup: app.py.backup")
    
    # Read the file
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Count original DEBUG statements
    debug_count = len(re.findall(r'print\([^)]*DEBUG[^)]*\)', content))
    print(f"📊 Found {debug_count} DEBUG print statements")
    
    # Remove DEBUG print statements
    patterns_to_remove = [
        # Simple DEBUG prints
        r'\s*print\(f?"DEBUG: [^"]*"\)\n',
        r'\s*print\("DEBUG: [^"]*"\)\n',
        r'\s*print\(f"DEBUG: [^"]*"\)\n',
        
        # Multi-line DEBUG prints
        r'\s*# Debug[^#]*\n',
        r'\s*# DEBUG[^#]*\n',
        
        # Specific verbose DEBUG statements
        r'\s*print\(f"DEBUG: Question \{[^}]*\} - SelectedChoices type: [^"]*"\)\n',
        r'\s*print\(f"DEBUG: Question \{[^}]*\} marked as [^"]*"\)\n',
        r'\s*print\(f"DEBUG: Found [A-Z]+ risk for \{[^}]*\}"\)\n',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content)
    
    # Replace remaining important DEBUG statements with conditional logging
    important_replacements = [
        # Keep only essential logging
        ('print("DEBUG: Starting generate_report function")', 
         'if os.environ.get("DEBUG_REPORTS") == "true": logger.info("Starting report generation")'),
        
        ('print("DEBUG: Report generation completed successfully")', 
         'logger.info("Report generation completed")'),
        
        ('print(f"DEBUG: Processing workload_id: {workload_id}")', 
         'logger.info(f"Processing workload: {workload_id}")'),
        
        ('print("DEBUG: No AWS region in session")', 
         'logger.warning("No AWS region in session")'),
        
        ('print("DEBUG: No workload_id in session")', 
         'logger.warning("No workload_id in session")'),
        
        ('print("DEBUG: Failed to get Well-Architected client")', 
         'logger.error("Failed to get Well-Architected client")'),
    ]
    
    for old, new in important_replacements:
        content = content.replace(old, new)
    
    # Remove empty lines that might be left behind
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Write the cleaned content
    with open('app.py', 'w') as f:
        f.write(content)
    
    # Count remaining DEBUG statements
    remaining_count = len(re.findall(r'print\([^)]*DEBUG[^)]*\)', content))
    removed_count = debug_count - remaining_count
    
    print(f"✅ Removed {removed_count} DEBUG print statements")
    print(f"📝 {remaining_count} DEBUG statements remaining (if any)")
    print("🚀 Performance should be significantly improved!")

if __name__ == "__main__":
    if os.path.exists('app.py'):
        remove_debug_prints()
    else:
        print("❌ app.py not found in current directory")
