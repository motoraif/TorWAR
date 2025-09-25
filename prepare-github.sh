#!/bin/bash

echo "🧹 Preparing TorWAR for GitHub"
echo "=============================="

# Remove sensitive files
echo "🔐 Removing sensitive files..."
rm -f .env .env.local .env.production
rm -f cookies*.txt *.log torwar.log app.log
rm -f q-dev-chat-*.md

# Remove SSL certificates (will be regenerated)
echo "🔑 Removing SSL certificates..."
rm -rf ssl/

# Remove data directories
echo "📁 Removing data directories..."
rm -rf data/ logs/ instance/ __pycache__/

# Remove backup and test files
echo "🗑️  Removing backup and test files..."
rm -rf *_backup_* testing/ test-files/
rm -f *_SUMMARY.md *_GUIDE.md *_FIXES.md *_SETUP.md
rm -f ENHANCEMENT_*.md DEBUG_*.md TRUSTED_ADVISOR_*.md
rm -f BEDROCK_*.md CACHING_*.md PERFORMANCE_*.md

# Create necessary directories with .gitkeep
echo "📂 Creating directory structure..."
mkdir -p data/reports logs instance
touch data/.gitkeep logs/.gitkeep instance/.gitkeep

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "🔧 Initializing git repository..."
    git init
fi

# Add files to git
echo "📝 Adding files to git..."
git add .
git status

echo ""
echo "✅ TorWAR prepared for GitHub!"
echo "📋 Next steps:"
echo "   1. Review git status above"
echo "   2. git commit -m 'Initial containerized TorWAR release'"
echo "   3. git remote add origin <your-github-repo-url>"
echo "   4. git push -u origin main"
