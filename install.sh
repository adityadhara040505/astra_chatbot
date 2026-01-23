#!/bin/bash
# Astra Chatbot - System Installation Script

set -e

echo "🚀 Astra Chatbot - Installation Script"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo "📦 Installing Astra Chatbot..."
echo "   User: $ACTUAL_USER"
echo "   Home: $ACTUAL_HOME"
echo ""

# 1. Create installation directory
echo "📁 Creating installation directory..."
INSTALL_DIR="/opt/astra-chatbot"
mkdir -p "$INSTALL_DIR"

# 2. Copy application files
echo "📋 Copying application files..."
cp astra_chatbot.py "$INSTALL_DIR/"
cp command_executor.py "$INSTALL_DIR/"
cp pdf_knowledge_base.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Copy PDF if exists
if [ -f "ubuntu-linux-toolbox-1000-commands-for-ubuntu-and-debian-power-users-9780470082935-2007041567-076456997x.pdf" ]; then
    echo "📖 Copying Ubuntu Linux Toolbox PDF..."
    cp ubuntu-linux-toolbox-1000-commands-for-ubuntu-and-debian-power-users-9780470082935-2007041567-076456997x.pdf "$INSTALL_DIR/"
fi

# Copy icon
if [ -f "astra-chatbot-icon.png" ]; then
    echo "🎨 Installing icon..."
    mkdir -p /usr/share/icons/hicolor/256x256/apps
    cp astra-chatbot-icon.png /usr/share/icons/hicolor/256x256/apps/astra-chatbot.png
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi

# 3. Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --break-system-packages -r "$INSTALL_DIR/requirements.txt" 2>/dev/null || \
pip3 install -r "$INSTALL_DIR/requirements.txt"

# 4. Create launcher script
echo "🔧 Creating launcher script..."
cat > /usr/bin/astra-chatbot << 'EOF'
#!/bin/bash
# Astra Chatbot Launcher

cd /opt/astra-chatbot
exec python3 astra_chatbot.py "$@"
EOF

chmod +x /usr/bin/astra-chatbot

# 5. Install desktop entry
echo "🖥️  Installing desktop entry..."
cp astra-chatbot.desktop /usr/share/applications/
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# 6. Create sessions directory for all users
echo "📂 Creating sessions directory..."
mkdir -p "$INSTALL_DIR/sessions"
chmod 777 "$INSTALL_DIR/sessions"

# 7. Set permissions
echo "🔐 Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 777 "$INSTALL_DIR/sessions"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📱 You can now:"
echo "   1. Launch from Applications menu (search 'Astra Chatbot')"
echo "   2. Run from terminal: astra-chatbot"
echo "   3. Find it in System → Utilities"
echo ""
echo "⚠️  Requirements:"
echo "   - Ollama must be installed and running"
echo "   - At least one LLM model (e.g., qwen2.5:0.5b)"
echo ""
echo "🔧 To install Ollama:"
echo "   curl -fsSL https://ollama.com/install.sh | sh"
echo "   ollama pull qwen2.5:0.5b"
echo ""
