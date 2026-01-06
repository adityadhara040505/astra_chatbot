# Astra Chatbot (Offline)

An offline Linux chat application that talks to a locally installed LLM via the Ollama API (localhost:11434). No internet is required once your model is pulled.

## Prerequisites
- Linux with Ollama installed and service running.
- At least one local model (e.g., `llama3.2:1b`).

Verify:
```bash
command -v ollama && systemctl is-active ollama
curl -sS http://localhost:11434/api/tags | jq
```

## Quick Start
1. Create a Python environment and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Optional: set model and system prompt via environment variables:
```bash
export ASTRA_CHATBOT_MODEL=llama3.2:1b
export ASTRA_CHATBOT_SYSTEM="You are a helpful assistant."
```

3. Run the chat app:
```bash
python app.py
```

Type `exit` to quit. Session transcripts are saved under `sessions/`.

## GUI (Linux Desktop)
Run the native GUI built with PySide6:
```bash
python gui_app.py
```

Headless check (lists local models without launching the window):
```bash
python gui_app.py --check
```

### GUI Features
- Modern light/dark theme toggle
- Model picker + refresh
- New Chat to start a fresh session
- Export current session to Markdown in `sessions/`
- Streaming responses with clear role labels

### Optional: Add to Desktop Menu
Create a local desktop entry:
```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/astra-chatbot.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Astra Chatbot
Comment=Offline chat with local LLM (Ollama)
Exec=/usr/bin/env python3 /home/astra/astra_chatbot/gui_app.py
Icon=utilities-terminal
Terminal=false
Categories=Utility;AI;
EOF
update-desktop-database ~/.local/share/applications || true
```

### Troubleshooting (Qt xcb plugin on Ubuntu/Debian)
If you see errors like "Could not load the Qt platform plugin 'xcb'", install the missing XCB libraries:
```bash
sudo apt update
sudo apt install -y libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-render-util0 libxkbcommon-x11-0
```

On Wayland sessions, you can force Wayland:
```bash
QT_QPA_PLATFORM=wayland python3 gui_app.py
```

On X11 sessions, ensure `QT_QPA_PLATFORM` is `xcb` (default in the app). If issues persist, try:
```bash
QT_QPA_PLATFORM=xcb python3 gui_app.py
```

If `python` is not found, use `python3` everywhere or install the alias:
```bash
sudo apt install -y python-is-python3
```

## Models
List models:
```bash
ollama list
```
Pull a model (example):
```bash
ollama pull llama3.2:1b
```

## Notes
- The app streams responses using `POST /api/chat`.
- If the API is unreachable, start the service: `sudo systemctl enable --now ollama`.
- Configure defaults with env vars: `ASTRA_CHATBOT_MODEL`, `ASTRA_CHATBOT_SYSTEM`.
