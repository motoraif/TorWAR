#!/usr/bin/env python3
"""
Clear any cached Flask sessions and Python cache
"""

import os
import shutil
import glob

def clear_caches():
    """Clear Python and Flask caches"""
    print("Clearing caches...")
    
    # Clear Python bytecode cache
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                print(f"Removed: {os.path.join(root, file)}")
        
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            print(f"Removed directory: {pycache_path}")
    
    # Clear any Flask session files (if using filesystem sessions)
    session_files = glob.glob('flask_session_*')
    for session_file in session_files:
        os.remove(session_file)
        print(f"Removed session file: {session_file}")
    
    print("✅ Cache clearing completed!")

if __name__ == "__main__":
    print("=" * 50)
    print("Clearing TorWAR Caches")
    print("=" * 50)
    
    clear_caches()
    
    print("\n" + "=" * 50)
    print("🎉 Ready to restart TorWAR application!")
    print("The application should now use account 445567094096")
    print("=" * 50)
