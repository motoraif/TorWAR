#!/bin/bash
# Cleanup old CSS files and organize static assets

echo "Cleaning up old CSS files..."

# Remove duplicate and old CSS files from static-backup
rm -f static-backup/*dark-mode*.css
rm -f static-backup/*fixes*.css
rm -f static-backup/*override*.css
rm -f static-backup/consolidated-*.css
rm -f static-backup/accessible-*.css
rm -f static-backup/bootstrap-*.css
rm -f static-backup/checkbox-*.css
rm -f static-backup/complete-*.css
rm -f static-backup/hints-*.css
rm -f static-backup/navbar-*.css
rm -f static-backup/navigation-*.css
rm -f static-backup/review-*.css
rm -f static-backup/select-*.css
rm -f static-backup/answer-*.css
rm -f static-backup/risk-*.css
rm -f static-backup/*.backup_*

# Keep only essential files
cp static-backup/style.css static/css/legacy.css 2>/dev/null || true
cp static-backup/app.js static/js/legacy.js 2>/dev/null || true

echo "Organizing static files..."

# Create proper directory structure
mkdir -p static/{css,js,img,fonts}

# Move files to proper locations
mv static/notification.css static/css/ 2>/dev/null || true
mv static/notification.js static/js/ 2>/dev/null || true

echo "Static files cleaned and organized!"
echo "Main files:"
echo "  - static/css/main.css (consolidated styles)"
echo "  - static/js/main.js (optimized JavaScript)"
echo "  - static/js/vue-app.js (Vue 3 SPA)"

# Set proper permissions
chmod -R 755 static/

echo "Cleanup complete!"
