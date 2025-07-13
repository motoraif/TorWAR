#!/usr/bin/env python3
"""
Targeted DEBUG statement removal for TorWAR
Author: Mohamed Toraif
"""

import re

def targeted_debug_fix():
    """Remove only the most problematic DEBUG statements."""
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Only remove the most verbose DEBUG statements that impact performance
    verbose_patterns = [
        # Question-level debugging (most verbose)
        r'\s*print\(f"DEBUG: Question \{question_id\}"\)\n',
        r'\s*print\(f"  - Selected Choices: \{selected_choices\}"\)\n',
        r'\s*print\(f"  - Available Choices: \{len\(choices\)\}"\)\n',
        r'\s*print\(f"DEBUG: Question \{question_id\} - Risk: \{risk\}, Choices: \{len\(selected_choices\)\}"\)\n',
        r'\s*print\(f"DEBUG: Question \{question_id\} marked as [^"]*"\)\n',
        r'\s*print\(f"DEBUG: Question \{question_id\} - SelectedChoices type: [^"]*"\)\n',
        r'\s*print\(f"DEBUG: Found [A-Z]+ risk for \{question_id\}"\)\n',
        r'\s*print\(f"DEBUG: Question \{question_id\} has no risk assessment \(unanswered\)"\)\n',
        
        # Pillar-level verbose debugging
        r'\s*print\(f"DEBUG: SECURITY PILLAR DETAILED ANALYSIS:"\)\n',
        r'\s*print\(f"  Questions processed: \{len\(detailed_answers\)\}"\)\n',
        r'\s*print\(f"  ⚠️ MISMATCH DETECTED! Manual: \{answered_count\}, Stats: \{pillar_stats\[\'answered_questions\'\]\}"\)\n',
        
        # Comment-based debug sections
        r'\s*# Debug logging\n',
        r'\s*# Debug: Check individual pillar question counts\n',
        r'\s*# Special debugging for Security pillar\n',
        r'\s*# Add debugging for all pillars to catch the issue\n',
    ]
    
    original_lines = content.count('\n')
    
    for pattern in verbose_patterns:
        content = re.sub(pattern, '', content)
    
    # Replace only the most critical DEBUG statements with simple logging
    critical_replacements = [
        ('print("DEBUG: Starting generate_report function")', 
         'logger.info("Starting report generation")'),
        ('print("DEBUG: Report generation completed successfully")', 
         'logger.info("Report generation completed")'),
        ('print("DEBUG: No AWS region in session")', 
         'logger.warning("No AWS region in session")'),
        ('print("DEBUG: No workload_id in session")', 
         'logger.warning("No workload_id in session")'),
    ]
    
    for old, new in critical_replacements:
        content = content.replace(old, new)
    
    # Clean up multiple empty lines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    with open('app.py', 'w') as f:
        f.write(content)
    
    new_lines = content.count('\n')
    removed_lines = original_lines - new_lines
    
    print(f"✅ Removed {removed_lines} lines of verbose DEBUG output")
    print("🚀 Performance should be improved for report generation")

if __name__ == "__main__":
    targeted_debug_fix()
