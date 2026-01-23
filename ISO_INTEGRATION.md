# Astra Chatbot - ISO Integration Guide

## Overview

This guide explains how to integrate Astra Chatbot into a custom Ubuntu/Debian-based ISO for distribution.

## Prerequisites

- Ubuntu/Debian base ISO
- Cubic (Custom Ubuntu ISO Creator) or similar tool
- Astra Chatbot .deb package

## Method 1: Using Cubic (Recommended)

### Step 1: Install Cubic
```bash
sudo apt-add-repository universe
sudo apt-add-repository ppa:cubic-wizard/release
sudo apt update
sudo apt install --no-install-recommends cubic
```

### Step 2: Start Cubic and Load ISO
1. Launch Cubic
2. Select your base ISO (e.g., Ubuntu 22.04)
3. Choose output directory
4. Click "Next" to extract ISO

### Step 3: Add Astra Chatbot

In the Cubic terminal:

```bash
# Copy the .deb package to the chroot environment
# (Do this from your host, not in Cubic terminal)
# The package will be in: ~/cubic/custom-disk/

# In Cubic terminal:
cd /tmp
# The .deb file should be copied here by Cubic

# Install the package
dpkg -i astra-chatbot_1.0.0_all.deb
apt-get install -f  # Fix any dependencies

# Install Ollama (optional, can be done post-install)
curl -fsSL https://ollama.com/install.sh | sh

# Pull default model (optional)
ollama pull qwen2.5:0.5b

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
```

### Step 4: Customize Desktop
```bash
# Add to default applications
mkdir -p /etc/skel/.config/autostart

# Optional: Auto-start on login
cp /usr/share/applications/astra-chatbot.desktop /etc/skel/.config/autostart/
```

### Step 5: Generate ISO
1. Click "Next" in Cubic
2. Customize boot options if needed
3. Generate the ISO
4. Test in VM

## Method 2: Manual ISO Customization

### Step 1: Extract ISO
```bash
mkdir -p ~/iso-custom/{extract,squashfs,new}
sudo mount -o loop ubuntu-22.04.iso ~/iso-custom/extract
sudo unsquashfs -d ~/iso-custom/squashfs ~/iso-custom/extract/casper/filesystem.squashfs
```

### Step 2: Chroot into System
```bash
sudo mount --bind /dev ~/iso-custom/squashfs/dev
sudo mount --bind /run ~/iso-custom/squashfs/run
sudo chroot ~/iso-custom/squashfs
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devpts none /dev/pts
```

### Step 3: Install Astra Chatbot
```bash
# Copy .deb to chroot first (from host)
# sudo cp astra-chatbot_1.0.0_all.deb ~/iso-custom/squashfs/tmp/

# Inside chroot:
cd /tmp
dpkg -i astra-chatbot_1.0.0_all.deb
apt-get install -f

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable ollama

# Pull model
ollama pull qwen2.5:0.5b

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
rm /tmp/astra-chatbot_1.0.0_all.deb
```

### Step 4: Exit and Rebuild
```bash
# Exit chroot
umount /proc /sys /dev/pts
exit

# Unmount
sudo umount ~/iso-custom/squashfs/dev
sudo umount ~/iso-custom/squashfs/run

# Rebuild squashfs
sudo mksquashfs ~/iso-custom/squashfs ~/iso-custom/new/casper/filesystem.squashfs -comp xz

# Copy other files
sudo cp -r ~/iso-custom/extract/* ~/iso-custom/new/
sudo cp ~/iso-custom/new/casper/filesystem.squashfs ~/iso-custom/new/casper/

# Generate ISO
sudo genisoimage -r -V "Custom Ubuntu" -cache-inodes -J -l \
  -b isolinux/isolinux.bin -c isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  -o ~/custom-ubuntu.iso ~/iso-custom/new
```

## Method 3: Preseed/Kickstart Integration

### Create preseed file: `astra-chatbot.seed`

```bash
# Download and install Astra Chatbot
d-i preseed/late_command string \
  in-target wget -O /tmp/astra-chatbot.deb https://your-server.com/astra-chatbot_1.0.0_all.deb; \
  in-target dpkg -i /tmp/astra-chatbot.deb; \
  in-target apt-get install -f -y; \
  in-target curl -fsSL https://ollama.com/install.sh | sh; \
  in-target systemctl enable ollama; \
  in-target rm /tmp/astra-chatbot.deb
```

## Post-Installation Setup Script

Create `/usr/local/bin/astra-setup.sh`:

```bash
#!/bin/bash
# Astra Chatbot Post-Install Setup

echo "🚀 Setting up Astra Chatbot..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    systemctl enable --now ollama
fi

# Pull default model
echo "📦 Pulling default LLM model..."
ollama pull qwen2.5:0.5b

# Create user sessions directory
mkdir -p ~/.local/share/astra-chatbot/sessions

echo "✅ Setup complete!"
echo "Launch Astra Chatbot from Applications menu"
```

## ISO Distribution Checklist

- [ ] Astra Chatbot .deb package included
- [ ] Ollama pre-installed (optional)
- [ ] Default LLM model included (optional, saves ~400MB)
- [ ] Desktop entry visible in menu
- [ ] Icon properly displayed
- [ ] PDF knowledge base included
- [ ] Post-install setup script (if needed)
- [ ] Documentation included
- [ ] Tested in VM

## Size Considerations

- Astra Chatbot: ~15 MB
- Ubuntu Linux Toolbox PDF: ~13 MB
- Ollama: ~50 MB
- qwen2.5:0.5b model: ~400 MB
- **Total**: ~480 MB

To reduce size:
- Don't include LLM model (download post-install)
- Don't include Ollama (download post-install)
- **Minimal size**: ~30 MB

## Testing

1. Boot ISO in VM (VirtualBox, VMware, QEMU)
2. Complete installation
3. Launch Astra Chatbot from menu
4. Test command execution
5. Verify PDF knowledge base works
6. Check session persistence

## Distribution

### Option 1: GitHub Release
```bash
# Create release with .deb package
gh release create v1.0.0 astra-chatbot_1.0.0_all.deb
```

### Option 2: APT Repository
```bash
# Create repository structure
mkdir -p repo/pool/main
cp astra-chatbot_1.0.0_all.deb repo/pool/main/

# Generate Packages file
cd repo
dpkg-scanpackages pool/main /dev/null | gzip -9c > pool/main/Packages.gz

# Users can add:
# deb [trusted=yes] https://your-server.com/repo pool/main/
```

### Option 3: Direct Download
Host the .deb file and provide install command:
```bash
wget https://your-server.com/astra-chatbot_1.0.0_all.deb
sudo dpkg -i astra-chatbot_1.0.0_all.deb
sudo apt-get install -f
```

## Customization for ISO

### Custom Branding
Edit `astra-chatbot.desktop`:
```ini
Name=Your Custom Name
Icon=/usr/share/pixmaps/your-icon.png
```

### Pre-configured Settings
Create `/opt/astra-chatbot/config.json`:
```json
{
  "default_model": "qwen2.5:0.5b",
  "theme": "dark",
  "auto_update": false
}
```

### System Integration
Add to `/etc/xdg/autostart/` for auto-launch on login.

## Support

For issues or questions:
- GitHub: https://github.com/yourusername/astra-chatbot
- Email: support@example.com
- Documentation: /usr/share/doc/astra-chatbot/

## License

Include appropriate license file in package.
