#!/bin/bash
# Astra Chatbot - Debian Package Builder

set -e

VERSION="1.0.0"
ARCH="all"
PACKAGE_NAME="astra-chatbot"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}_${ARCH}"

echo "📦 Building Debian Package for Astra Chatbot"
echo "=============================================="
echo "Version: $VERSION"
echo "Architecture: $ARCH"
echo ""

# Clean previous build
rm -rf build
mkdir -p "$BUILD_DIR"

# Create directory structure
echo "📁 Creating package structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/astra-chatbot"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/doc/astra-chatbot"

# Copy application files
echo "📋 Copying application files..."
cp astra_chatbot.py "$BUILD_DIR/opt/astra-chatbot/"
cp command_executor.py "$BUILD_DIR/opt/astra-chatbot/"
cp pdf_knowledge_base.py "$BUILD_DIR/opt/astra-chatbot/"
cp requirements.txt "$BUILD_DIR/opt/astra-chatbot/"

# Copy PDF if exists
if [ -f "ubuntu-linux-toolbox-1000-commands-for-ubuntu-and-debian-power-users-9780470082935-2007041567-076456997x.pdf" ]; then
    cp ubuntu-linux-toolbox-1000-commands-for-ubuntu-and-debian-power-users-9780470082935-2007041567-076456997x.pdf "$BUILD_DIR/opt/astra-chatbot/"
fi

# Copy icon
if [ -f "astra-chatbot-icon.png" ]; then
    cp astra-chatbot-icon.png "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/astra-chatbot.png"
fi

# Copy desktop file
cp astra-chatbot.desktop "$BUILD_DIR/usr/share/applications/"

# Copy documentation
cp README.md "$BUILD_DIR/usr/share/doc/astra-chatbot/" 2>/dev/null || echo "# Astra Chatbot" > "$BUILD_DIR/usr/share/doc/astra-chatbot/README.md"

# Create launcher script
cat > "$BUILD_DIR/usr/bin/astra-chatbot" << 'EOF'
#!/bin/bash
cd /opt/astra-chatbot
exec python3 astra_chatbot.py "$@"
EOF
chmod +x "$BUILD_DIR/usr/bin/astra-chatbot"

# Create control file
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.8), python3-pip
Recommends: ollama
Maintainer: Astra Team <astra@example.com>
Description: Intelligent Linux Assistant with AI
 Astra Chatbot is an intelligent Linux assistant that combines
 conversational AI with smart command execution. It uses the
 Ubuntu Linux Toolbox as a knowledge base to help users execute
 system commands through natural language.
 .
 Features:
  - Smart command execution with PDF knowledge base
  - Automatic retry with error analysis (up to 5 attempts)
  - Beautiful modern UI with dark/light themes
  - Session history and export functionality
  - Integration with Ollama for local LLM inference
Homepage: https://github.com/yourusername/astra-chatbot
EOF

# Create postinst script
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --break-system-packages httpx PySide6 PyYAML PyPDF2 2>/dev/null || \
pip3 install httpx PySide6 PyYAML PyPDF2

# Create sessions directory
mkdir -p /opt/astra-chatbot/sessions
chmod 777 /opt/astra-chatbot/sessions

# Update desktop database
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true

echo ""
echo "✅ Astra Chatbot installed successfully!"
echo ""
echo "📱 Launch from Applications menu or run: astra-chatbot"
echo ""
echo "⚠️  Requirements:"
echo "   - Ollama must be installed: curl -fsSL https://ollama.com/install.sh | sh"
echo "   - Pull a model: ollama pull qwen2.5:0.5b"
echo ""

exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/postinst"

# Create prerm script
cat > "$BUILD_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/prerm"

# Create postrm script
cat > "$BUILD_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true

exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/postrm"

# Set permissions
echo "🔐 Setting permissions..."
chmod -R 755 "$BUILD_DIR/opt/astra-chatbot"
chmod 755 "$BUILD_DIR/usr/bin/astra-chatbot"

# Build package
echo "🔨 Building package..."
dpkg-deb --build "$BUILD_DIR"

# Move to current directory
mv "build/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" .

echo ""
echo "✅ Package built successfully!"
echo ""
echo "📦 Package: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "  sudo apt-get install -f  # Fix dependencies if needed"
echo ""
