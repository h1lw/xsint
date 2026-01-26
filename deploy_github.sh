#!/bin/bash

# KISS GitHub Deployment Script
# This script helps deploy KISS to GitHub

echo "🚀 KISS GitHub Deployment Script"
echo "================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found"
    echo ""
    echo "Install GitHub CLI first:"
    echo "  brew install gh  # macOS"
    echo "  sudo apt install gh  # Ubuntu/Debian"
    echo "  winget install GitHub.cli  # Windows"
    echo ""
    echo "Then authenticate with: gh auth login"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Please run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI configured"
echo ""

# Repository information
REPO_NAME="kiss"
REPO_DESCRIPTION="KISS - Keep It Simple, Stupid: A modern OSINT toolkit for comprehensive intelligence gathering with structured query support"
HOMEPAGE_URL="https://github.com/yourusername/kiss"
TOPICS="osint, cybersecurity, async, python, intelligence"

echo "📝 Repository Configuration:"
echo "  Name: $REPO_NAME"
echo "  Description: $REPO_DESCRIPTION"
echo "  Homepage: $HOMEPAGE_URL"
echo "  Topics: $TOPICS"
echo ""

# Create repository
echo "🏗️  Creating GitHub repository..."
gh repo create $REPO_NAME \
  --public \
  --description "$REPO_DESCRIPTION" \
  --homepage "$HOMEPAGE_URL" \
  --topics "$TOPICS"

if [ $? -eq 0 ]; then
    echo "✅ Repository created successfully!"
else
    echo "⚠️  Repository might already exist or error occurred"
    echo "Continuing with existing repository..."
fi

# Add remote
echo "🔗 Adding remote origin..."
git remote add origin https://github.com/yourusername/$REPO_NAME.git 2>/dev/null || true

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin master

# Create initial release
echo "🏷️  Creating initial release..."
gh release create v2.0.0 \
  --title "KISS v2.0.0 - Modern OSINT Toolkit" \
  --notes "$(cat <<'EOF'
# KISS v2.0.0

Major release with modern async architecture and professional features.

## 🚀 Key Features

### Async Architecture
- High-performance async plugin system
- Non-blocking HTTP requests with aiohttp
- Connection pooling and resource management
- Backward compatibility with sync plugins

### Strict Query System  
- Field:"value" syntax with validation
- Support for email, phone, ip, username, address, hash
- Fail-fast validation with helpful error messages

### Professional Repository
- Complete GitHub templates and workflows
- Comprehensive documentation and guides
- Plugin development templates and examples
- MIT License for open source contribution

### Modern Development
- CI/CD pipeline with automated testing
- Async plugin templates for easy development
- Professional code standards and documentation
- Enhanced error handling and user experience

## 📦 Installation

\`\`\`bash
git clone https://github.com/yourusername/kiss.git
cd kiss
pip install -r requirements.txt
python -m kiss user@example.com
\`\`\`

## 🧩 Plugin Development

New plugin architecture makes development easier than ever:

\`\`\`python
from kiss.plugins.async_base import AsyncBasePlugin

class MyPlugin(AsyncBasePlugin):
    async def scan_async(self, target, scan_type, progress_callback):
        # Your async implementation
        return [self._create_result("Result", "value")]
\`\`\`

## 🔮 Roadmap

This release establishes the foundation for future enhancements:
- Name-based searches (name:"John Doe" location:"New York")
- SSID/BSSID lookup capabilities  
- Advanced phone number parsing
- Batch processing and export features
- REST API and web interface

## 🙏 Acknowledgments

Thanks to the OSINT community and contributors who helped make this release possible.

---
Built with ❤️ for the OSINT community
EOF
)"

echo ""
echo "✅ Repository deployment complete!"
echo ""
echo "🔗 Your repository is available at:"
echo "https://github.com/yourusername/kiss"
echo ""
echo "📋 Next steps:"
echo "1. Visit your repository"
echo "2. Update repository description with your GitHub username"
echo "3. Enable GitHub Pages for documentation"
echo "4. Test the installation from git clone"
echo ""
echo "🎉 Happy OSINT hunting!"