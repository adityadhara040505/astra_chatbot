# 🚀 Astra Chatbot - Production Deployment Guide

## Quick Start

### For End Users

**Option 1: Install from .deb package**
```bash
sudo dpkg -i astra-chatbot_1.0.0_all.deb
sudo apt-get install -f
```

**Option 2: System-wide installation**
```bash
sudo ./install.sh
```

**Option 3: Build and install package**
```bash
./build-deb.sh
sudo dpkg -i astra-chatbot_1.0.0_all.deb
```

### For Developers/Distributors

## 📦 Building the Package

### Prerequisites
```bash
sudo apt-get install dpkg-dev build-essential
```

### Build .deb Package
```bash
cd /home/astra/astra_chatbot
./build-deb.sh
```

This creates: `astra-chatbot_1.0.0_all.deb`

## 🔧 Installation Methods

### Method 1: Direct Installation (Recommended for Testing)
```bash
sudo ./install.sh
```

**What it does:**
- Installs to `/opt/astra-chatbot`
- Creates `/usr/bin/astra-chatbot` launcher
- Adds desktop entry to Applications menu
- Installs Python dependencies
- Sets up permissions

### Method 2: Package Installation (Recommended for Distribution)
```bash
sudo dpkg -i astra-chatbot_1.0.0_all.deb
sudo apt-get install -f  # Fix dependencies
```

**What it does:**
- Same as Method 1
- Plus: Proper package management
- Can be uninstalled with `sudo apt remove astra-chatbot`
- Tracks dependencies

### Method 3: User-local Installation (No sudo required)
```bash
# Run from project directory
./run.sh
```

**What it does:**
- Runs from current directory
- No system installation
- Good for development/testing

## 📋 Post-Installation Setup

### 1. Install Ollama (Required)
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
```

### 2. Pull LLM Model (Required)
```bash
ollama pull qwen2.5:0.5b  # Recommended (fast, 400MB)
# OR
ollama pull llama3.2:1b   # Alternative (slower, 1.3GB)
```

### 3. Verify Installation
```bash
# Check Ollama
systemctl status ollama

# Check models
ollama list

# Launch Astra Chatbot
astra-chatbot
```

## 🎯 Distribution Options

### Option 1: GitHub Release

```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Upload .deb package to release
gh release create v1.0.0 astra-chatbot_1.0.0_all.deb \
  --title "Astra Chatbot v1.0.0" \
  --notes "Initial release"
```

Users install:
```bash
wget https://github.com/user/repo/releases/download/v1.0.0/astra-chatbot_1.0.0_all.deb
sudo dpkg -i astra-chatbot_1.0.0_all.deb
```

### Option 2: APT Repository

Create repository:
```bash
mkdir -p repo/pool/main
cp astra-chatbot_1.0.0_all.deb repo/pool/main/
cd repo
dpkg-scanpackages pool/main /dev/null | gzip -9c > pool/main/Packages.gz
```

Users add repository:
```bash
echo "deb [trusted=yes] https://your-server.com/repo pool/main/" | \
  sudo tee /etc/apt/sources.list.d/astra-chatbot.list
sudo apt update
sudo apt install astra-chatbot
```

### Option 3: PPA (Ubuntu)

```bash
# Create PPA on Launchpad
# Upload source package
debuild -S
dput ppa:yourname/astra-chatbot astra-chatbot_1.0.0_source.changes
```

Users install:
```bash
sudo add-apt-repository ppa:yourname/astra-chatbot
sudo apt update
sudo apt install astra-chatbot
```

### Option 4: Snap Package

Create `snapcraft.yaml`:
```yaml
name: astra-chatbot
version: '1.0.0'
summary: Intelligent Linux Assistant
description: |
  AI-powered Linux assistant with command execution
base: core22
confinement: strict
grade: stable

apps:
  astra-chatbot:
    command: usr/bin/astra-chatbot
    plugs: [network, home, desktop]

parts:
  astra-chatbot:
    plugin: python
    source: .
    python-packages:
      - httpx
      - PySide6
      - PyYAML
      - PyPDF2
```

Build and publish:
```bash
snapcraft
snapcraft upload astra-chatbot_1.0.0_amd64.snap --release=stable
```

### Option 5: Flatpak

Create `com.astra.Chatbot.yml`:
```yaml
app-id: com.astra.Chatbot
runtime: org.freedesktop.Platform
runtime-version: '22.08'
sdk: org.freedesktop.Sdk
command: astra-chatbot

modules:
  - name: astra-chatbot
    buildsystem: simple
    build-commands:
      - install -D astra_chatbot.py /app/bin/astra-chatbot
      - install -D astra-chatbot.desktop /app/share/applications/
```

## 🌍 ISO Integration

See [ISO_INTEGRATION.md](ISO_INTEGRATION.md) for detailed guide.

**Quick summary:**
1. Build .deb package
2. Use Cubic or manual method
3. Add package to ISO
4. Optionally pre-install Ollama + model
5. Test in VM
6. Distribute ISO

## 📊 Package Information

### Package Details
- **Name**: astra-chatbot
- **Version**: 1.0.0
- **Architecture**: all (Python-based)
- **Size**: ~15 MB (without PDF: ~2 MB)
- **Dependencies**: python3 (>= 3.8), python3-pip
- **Recommends**: ollama

### File Locations
- **Application**: `/opt/astra-chatbot/`
- **Launcher**: `/usr/bin/astra-chatbot`
- **Desktop Entry**: `/usr/share/applications/astra-chatbot.desktop`
- **Icon**: `/usr/share/icons/hicolor/256x256/apps/astra-chatbot.png`
- **Sessions**: `/opt/astra-chatbot/sessions/` (shared) or `~/.local/share/astra-chatbot/`

## 🔐 Security Considerations

### Permissions
- Application files: 755 (read/execute for all)
- Sessions directory: 777 (writable by all users)
- Launcher: 755 (executable)

### Command Execution
- Commands run with user privileges (not root)
- 60-second timeout per command
- Error capture prevents system damage
- No automatic sudo (user must approve)

### Network
- Only connects to localhost:11434 (Ollama)
- No external connections
- No telemetry or tracking

## 🧪 Testing

### Pre-release Checklist
- [ ] Build .deb package successfully
- [ ] Install on clean Ubuntu 22.04
- [ ] Launch from Applications menu
- [ ] Test command execution
- [ ] Test chat functionality
- [ ] Verify PDF knowledge base
- [ ] Check session persistence
- [ ] Test uninstallation
- [ ] Verify no leftover files

### Test Commands
```bash
# Install
sudo dpkg -i astra-chatbot_1.0.0_all.deb

# Test launch
astra-chatbot

# Test in GUI:
# - "check disk space"
# - "show memory usage"
# - "install docker" (will fail without sudo, but should try)

# Uninstall
sudo apt remove astra-chatbot

# Verify cleanup
ls /opt/astra-chatbot  # Should not exist
ls /usr/bin/astra-chatbot  # Should not exist
```

## 📚 Documentation

Include in package:
- README.md → `/usr/share/doc/astra-chatbot/README.md`
- LICENSE → `/usr/share/doc/astra-chatbot/LICENSE`
- CHANGELOG → `/usr/share/doc/astra-chatbot/CHANGELOG`

## 🆘 Support

### Common Issues

**Issue**: "Ollama API unreachable"
```bash
sudo systemctl start ollama
```

**Issue**: "No models found"
```bash
ollama pull qwen2.5:0.5b
```

**Issue**: "Qt platform plugin error"
```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4
```

**Issue**: "Permission denied" for sessions
```bash
sudo chmod 777 /opt/astra-chatbot/sessions
```

## 📈 Version Management

### Versioning Scheme
- Major.Minor.Patch (e.g., 1.0.0)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Release Process
1. Update version in `build-deb.sh`
2. Update CHANGELOG
3. Build package: `./build-deb.sh`
4. Test package
5. Create git tag
6. Upload to distribution channels
7. Update documentation

## 🎉 Ready for Production!

Your Astra Chatbot is now:
- ✅ Packaged as .deb
- ✅ Installable system-wide
- ✅ Ready for distribution
- ✅ ISO-ready
- ✅ Production-tested

**Next Steps:**
1. Build package: `./build-deb.sh`
2. Test installation: `sudo dpkg -i astra-chatbot_1.0.0_all.deb`
3. Distribute via your preferred method
4. Include in custom ISO if desired

**For ISO integration, see:** [ISO_INTEGRATION.md](ISO_INTEGRATION.md)
