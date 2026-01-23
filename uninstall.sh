#!/bin/bash
# Astra Chatbot - Uninstallation Script

set -e

echo "🗑️  Astra Chatbot - Uninstallation Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "⚠️  This will remove Astra Chatbot from your system."
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing Astra Chatbot..."

# Remove installation directory
if [ -d "/opt/astra-chatbot" ]; then
    echo "📁 Removing /opt/astra-chatbot..."
    rm -rf /opt/astra-chatbot
fi

# Remove launcher
if [ -f "/usr/bin/astra-chatbot" ]; then
    echo "🔧 Removing launcher..."
    rm -f /usr/bin/astra-chatbot
fi

# Remove desktop entry
if [ -f "/usr/share/applications/astra-chatbot.desktop" ]; then
    echo "🖥️  Removing desktop entry..."
    rm -f /usr/share/applications/astra-chatbot.desktop
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

# Remove icon
if [ -f "/usr/share/icons/hicolor/256x256/apps/astra-chatbot.png" ]; then
    echo "🎨 Removing icon..."
    rm -f /usr/share/icons/hicolor/256x256/apps/astra-chatbot.png
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi

echo ""
echo "✅ Uninstallation complete!"
echo ""
echo "Note: User session data in ~/.local/share/astra-chatbot was preserved."
echo "      Python dependencies were not removed."
echo ""
