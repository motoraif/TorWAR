#!/usr/bin/env python3
"""
Script to replace DEBUG print statements with proper logging
Author: Mohamed Toraif
"""

import re
import os

def fix_debug_logging():
    """Replace DEBUG print statements with proper logging calls."""
    
    # Read the current app.py file
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Add logging import at the top
    if 'from logging_config import' not in content:
        # Find the import section and add our logging import
        import_pattern = r'(from report_manager import ReportManager\n)'
        replacement = r'\1from logging_config import get_logger, time_operation, log_performance\n'
        content = re.sub(import_pattern, replacement, content)
    
    # Add logger initialization after app creation
    if 'logger = get_logger("report_generation")' not in content:
        app_pattern = r'(app = Flask\(__name__\)\n)'
        replacement = r'\1\n# Initialize logger\nlogger = get_logger("report_generation")\nperf_logger = get_logger("performance")\n'
        content = re.sub(app_pattern, replacement, content)
    
    # Replace DEBUG print statements with logger calls
    debug_patterns = [
        # Simple DEBUG prints
        (r'print\(f?"DEBUG: ([^"]+)"\)', r'logger.debug("\1")'),
        (r'print\("DEBUG: ([^"]+)"\)', r'logger.debug("\1")'),
        
        # DEBUG prints with variables
        (r'print\(f"DEBUG: ([^"]+)"\)', r'logger.debug(f"\1")'),
        
        # Exception DEBUG prints
        (r'print\(f"DEBUG: Exception in ([^:]+): \{str\(e\)\}"\)', r'logger.error(f"Exception in \1: {str(e)}")'),
        (r'print\(f"DEBUG: Exception type: \{type\(e\)\.__name__\}"\)', r'logger.error(f"Exception type: {type(e).__name__}")'),
        (r'print\(f"DEBUG: Traceback: \{traceback\.format_exc\(\)\}"\)', r'logger.error(f"Traceback: {traceback.format_exc()}")'),
    ]
    
    for pattern, replacement in debug_patterns:
        content = re.sub(pattern, replacement, content)
    
    # Replace specific function print statements
    specific_replacements = [
        # Function start/end logging
        ('print("DEBUG: Starting generate_report function")', 'logger.info("Starting report generation")'),
        ('print("DEBUG: Report generation completed successfully")', 'logger.info("Report generation completed successfully")'),
        
        # AWS connection logging
        ('print("DEBUG: No AWS region in session")', 'logger.warning("No AWS region in session")'),
        ('print("DEBUG: No workload_id in session")', 'logger.warning("No workload_id in session")'),
        ('print("DEBUG: Failed to get Well-Architected client")', 'logger.error("Failed to get Well-Architected client")'),
        ('print("DEBUG: Got Well-Architected client successfully")', 'logger.debug("Got Well-Architected client successfully")'),
        
        # Workload processing
        ('print("DEBUG: Getting workload details...")', 'logger.debug("Getting workload details")'),
        
        # Save report logging
        ('print("DEBUG: Regenerating report data for saving...")', 'logger.info("Regenerating report data for saving")'),
    ]
    
    for old, new in specific_replacements:
        content = content.replace(old, new)
    
    # Write the updated content back
    with open('app.py.new', 'w') as f:
        f.write(content)
    
    print("✅ Created app.py.new with improved logging")
    print("📝 Review the changes and rename to app.py when ready")

if __name__ == "__main__":
    fix_debug_logging()
