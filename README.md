# Astra Chatbot - Intelligent Linux Assistant

An intelligent Linux assistant that combines LLM chat capabilities with smart command execution using the Ubuntu Linux Toolbox knowledge base.

## Features

✨ **Smart Command Execution**
- Understands natural language commands (e.g., "Install VS Code")
- Uses Ubuntu Linux Toolbox PDF as knowledge base
- Automatic retry with error analysis (up to 5 attempts)
- LLM-powered error diagnosis and fix suggestions

💬 **Chat Interface**
- Modern dark/light theme
- Chat history with sessions
- Export conversations to Markdown
- Streaming LLM responses

🎯 **Intelligent Features**
- Detects command vs. conversation intent
- Searches PDF for relevant commands
- Learns from errors and tries alternatives
- Provides detailed execution summaries

## Prerequisites

- Linux (Ubuntu/Debian recommended)
- Ollama installed and running
- At least one LLM model (e.g., `qwen2.5:0.5b`)

### Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
ollama pull qwen2.5:0.5b
```

## Quick Start

1. **Clone and setup:**
```bash
cd /home/astra/astra_chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python astra_chatbot.py
```

## Usage Examples

### Command Execution
Just type natural language commands:
- "Install VS Code"
- "Update all packages"
- "Install Docker"
- "Setup Python development environment"

The system will:
1. 🤖 Understand your request using LLM
2. 📖 Search Ubuntu Linux Toolbox for relevant commands
3. ⚡ Execute commands with automatic retry
4. 🔍 Analyze errors and try alternatives if needed
5. ✅ Report success or detailed error summary

### Regular Chat
Ask questions or have conversations:
- "How do I check disk space?"
- "What's the difference between apt and snap?"
- "Explain Linux file permissions"

## How It Works

### Intelligent Command Execution Flow

1. **Intent Detection**: LLM determines if input is a command or question
2. **Knowledge Search**: Searches Ubuntu Linux Toolbox PDF for relevant info
3. **Command Generation**: LLM generates appropriate shell commands
4. **Execution with Retry**: Runs commands with up to 5 retry attempts
5. **Error Analysis**: On failure, LLM analyzes error and suggests fixes
6. **Alternative Attempts**: Tries different approaches automatically
7. **Summary Report**: Provides detailed success/failure summary

### Example: "Install VS Code"

```
🤖 Understanding request: Install VS Code
📋 Identified 3 command(s) to execute

Command 1/3: wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
🔄 Attempt 1/5
✅ Command succeeded!

Command 2/3: sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
🔄 Attempt 1/5
✅ Command succeeded!

Command 3/3: sudo apt update && sudo apt install code
🔄 Attempt 1/5
✅ Command succeeded!

✅ Successfully executed all commands
```

## Configuration

### Environment Variables
```bash
export ASTRA_CHATBOT_MODEL="qwen2.5:0.5b"  # LLM model to use
export OLLAMA_API="http://localhost:11434"  # Ollama API endpoint
```

### Model Selection
- **qwen2.5:0.5b** (Default) - Fastest, good for most tasks
- **llama3.2:1b** - Balanced performance
- **phi3:latest** - Most accurate, slower

## Project Structure

```
astra_chatbot/
├── astra_chatbot.py           # Main GUI application
├── command_executor.py        # Intelligent command execution engine
├── pdf_knowledge_base.py      # PDF search and extraction
├── ubuntu-linux-toolbox...pdf # Knowledge base
├── requirements.txt           # Python dependencies
└── sessions/                  # Chat history
```

## Troubleshooting

### Ollama Not Running
```bash
sudo systemctl status ollama
sudo systemctl start ollama
```

### Qt/GUI Issues
```bash
# Install Qt dependencies
sudo apt install -y libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 \
                    libxcb-render-util0 libxkbcommon-x11-0

# Try different platform
QT_QPA_PLATFORM=xcb python astra_chatbot.py
```

### PDF Not Loading
The Ubuntu Linux Toolbox PDF should be in the same directory as the application.
On first run, it will extract and cache the content (may take a minute).

## Features in Detail

### Retry Logic
- Attempts each command up to 5 times
- Analyzes error messages using LLM
- Searches PDF for error-specific solutions
- Tries alternative commands automatically

### Error Analysis
When a command fails:
1. Captures error output
2. Sends to LLM with PDF context
3. Gets explanation and fix suggestions
4. Extracts alternative commands
5. Retries with new approach

### Knowledge Base
- Extracts all content from Ubuntu Linux Toolbox PDF
- Creates searchable cache for fast lookups
- Provides context-aware command suggestions
- Updates automatically if PDF changes

## License

MIT License - See project repository for details

## Credits

- Ubuntu Linux Toolbox reference material
- Ollama for local LLM inference
- PySide6 for GUI framework
