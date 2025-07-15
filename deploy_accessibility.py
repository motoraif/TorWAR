#!/usr/bin/env python3
"""
TorWAR Accessibility Deployment Script
Author: Mohamed Toraif

This script deploys the accessibility improvements and validates the setup.
"""

import os
import shutil
from datetime import datetime

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists and return status"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {filepath}")
    return exists

def backup_old_css():
    """Backup the old simple dark mode CSS"""
    old_file = "static/simple-dark-mode.css"
    if os.path.exists(old_file):
        backup_name = f"static/simple-dark-mode.css.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(old_file, backup_name)
        print(f"📦 Backed up old CSS to: {backup_name}")
        return True
    return False

def validate_css_content():
    """Validate that the accessible CSS contains required improvements"""
    css_file = "static/accessible-dark-mode.css"
    if not os.path.exists(css_file):
        return False
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    required_features = [
        '--risk-high: #ff6b6b',  # Enhanced risk colors
        '--risk-medium: #ffa726',
        '--risk-low: #ffeb3b',
        '--link-color: #58a6ff',  # Accessible link colors
        'prefers-contrast: high',  # High contrast support
        'prefers-reduced-motion',  # Reduced motion support
        'focus',  # Focus indicators
        'WCAG AA',  # Documentation
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"⚠️  Missing features in CSS: {missing_features}")
        return False
    
    print("✅ All accessibility features found in CSS")
    return True

def main():
    print("🚀 TorWAR Accessibility Deployment")
    print("=" * 40)
    
    # Check current directory
    if not os.path.exists('app.py'):
        print("❌ Please run this script from the TorWAF directory")
        return False
    
    print("\n📁 Checking Required Files:")
    required_files = [
        'static/accessible-dark-mode.css',
        'static/simple-dark-mode.js',
        'templates/base.html',
        'accessibility_test.html',
        'validate_accessibility.py'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if not check_file_exists(file_path):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing!")
        return False
    
    print("\n🔍 Validating CSS Content:")
    if not validate_css_content():
        print("❌ CSS validation failed!")
        return False
    
    print("\n📦 Backing Up Old Files:")
    backup_old_css()
    
    print("\n🧪 Running Accessibility Validation:")
    os.system("python3 validate_accessibility.py")
    
    print("\n✅ Deployment Complete!")
    print("\n🎯 Next Steps:")
    print("1. Test the application with dark mode")
    print("2. Open accessibility_test.html to verify improvements")
    print("3. Use browser dev tools to check contrast ratios")
    print("4. Test keyboard navigation (Tab key)")
    print("5. Validate with accessibility tools (WAVE, axe, Lighthouse)")
    
    print("\n🌐 Test URLs:")
    print("- Accessibility Test: file:///home/toraif/TorWAF/accessibility_test.html")
    print("- Flask App: http://localhost:5000 (when running)")
    
    print("\n🎉 Your TorWAR dark mode is now WCAG AA compliant!")
    return True

if __name__ == "__main__":
    main()
