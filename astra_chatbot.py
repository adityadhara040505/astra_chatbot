import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import threading

"""Ensure a suitable Qt platform plugin is set before importing Qt widgets."""
_session = os.environ.get("XDG_SESSION_TYPE", "").lower()
if "QT_QPA_PLATFORM" not in os.environ:
    if _session == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "wayland"
    elif _session == "x11":
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

import httpx
from PySide6.QtCore import QThread, Signal, Qt, QObject
from PySide6.QtGui import QTextCursor, QFont, QScreen, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QFrame,
)

from command_executor import CommandExecutor

OLLAMA_API = os.environ.get("OLLAMA_API", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("ASTRA_CHATBOT_MODEL", "qwen2.5:0.5b")
SYSTEM_PROMPT = os.environ.get("ASTRA_CHATBOT_SYSTEM")

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize command executor with PDF
PDF_PATH = Path(__file__).parent / "ubuntu-linux-toolbox-1000-commands-for-ubuntu-and-debian-power-users-9780470082935-2007041567-076456997x.pdf"
COMMAND_EXECUTOR = None

def init_command_executor():
    """Initialize command executor in background"""
    global COMMAND_EXECUTOR
    if PDF_PATH.exists():
        print("🔧 Initializing command executor with Ubuntu Linux Toolbox...")
        COMMAND_EXECUTOR = CommandExecutor(str(PDF_PATH))
        print("✅ Command executor ready!")
    else:
        print(f"⚠️  PDF not found at {PDF_PATH}")

def ensure_api_available() -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{OLLAMA_API}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{OLLAMA_API}/api/tags")
            r.raise_for_status()
            tags = r.json().get("models", [])
            return [m.get("name") for m in tags if m.get("name")]
    except Exception:
        return []


def save_turn(session_path: Path, role: str, content: str) -> None:
    payload = {"ts": time.time(), "role": role, "content": content}
    session_path.write_text(
        (session_path.read_text() if session_path.exists() else "") + json.dumps(payload) + "\n",
        encoding="utf-8",
    )


def is_command(text: str) -> bool:
    """Check if text looks like a command request"""
    text_lower = text.lower().strip()
    
    # Command indicators - actions that should execute commands
    command_keywords = [
        # Installation/removal
        "install", "uninstall", "remove", "purge", "add",
        # Updates
        "update", "upgrade", "patch",
        # Application control
        "open", "close", "launch", "start", "run", "execute",
        # Configuration
        "setup", "configure", "enable", "disable", "set",
        # File operations
        "create", "delete", "make", "build", "copy", "move",
        # Network operations
        "download", "get", "fetch", "pull", "clone",
        # System control
        "restart", "stop", "kill", "shutdown", "reboot",
        # Information gathering (should execute commands to get real data)
        "check", "show", "list", "display", "find", "search",
        "view", "see", "get", "print", "monitor", "watch"
    ]
    
    # Check if starts with command keyword
    for keyword in command_keywords:
        if text_lower.startswith(keyword + " ") or text_lower == keyword:
            return True
    
    return False


class CommandWorker(QThread):
    """Worker thread for executing commands"""
    progress = Signal(str)
    done = Signal(dict)
    
    def __init__(self, request: str):
        super().__init__()
        self.request = request
    
    def run(self):
        try:
            if COMMAND_EXECUTOR is None:
                self.progress.emit("❌ Command executor not initialized")
                self.done.emit({"final_status": "failed", "summary": "Command executor not available"})
                return
            
            self.progress.emit(f"🤖 Processing: {self.request}")
            report = COMMAND_EXECUTOR.execute_with_retry(self.request)
            
            # Send progress updates
            for attempt in report.get("attempts", []):
                status = "✅" if attempt["success"] else "❌"
                self.progress.emit(f"{status} Attempt {attempt['attempt']}: {attempt['command'][:50]}")
            
            self.done.emit(report)
        
        except Exception as e:
            self.progress.emit(f"❌ Error: {str(e)}")
            self.done.emit({"final_status": "failed", "summary": str(e)})


class ChatWorker(QThread):
    chunk = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, model: str, messages: list[dict[str, str]]):
        super().__init__()
        self.model = model
        self.messages = messages

    def run(self) -> None:
        try:
            assistant_text = ""
            with httpx.Client(timeout=None) as client:
                with client.stream(
                    "POST",
                    f"{OLLAMA_API}/api/chat",
                    json={"model": self.model, "messages": self.messages, "stream": True},
                ) as r:
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except Exception:
                            continue
                        msg = data.get("message") or {}
                        chunk = msg.get("content", "")
                        if chunk:
                            assistant_text += chunk
                            self.chunk.emit(chunk)
                        if data.get("done"):
                            break
            self.done.emit(assistant_text)
        except Exception as e:
            self.error.emit(str(e))


class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astra Chatbot")
        
        # Set window icon
        icon_path = Path(__file__).parent / "astra-chatbot-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Get screen geometry and set initial size to 85% of screen
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.85)
        height = int(screen.height() * 0.85)
        self.resize(width, height)
        
        # Center the window on screen
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)
        
        # Set minimum size but allow resizing
        self.setMinimumSize(800, 500)

        self.session_path = SESSIONS_DIR / datetime.now().strftime("session-%Y%m%d-%H%M%S.jsonl")
        self.messages: list[dict[str, str]] = []
        self.assistant_streaming_started: bool = False
        self.sessions_list: list[dict] = []
        self.dark_mode_enabled = True
        self.command_worker = None

        # Main layout with sidebar
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(280)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)

        # New chat button
        self.new_btn = QPushButton("+ New chat")
        self.new_btn.setObjectName("newChatBtn")
        self.new_btn.setMinimumHeight(44)
        sidebar_layout.addWidget(self.new_btn)

        # Chat history list
        history_label = QLabel("RECENT")
        history_label.setObjectName("sidebarLabel")
        sidebar_layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        sidebar_layout.addWidget(self.history_list)

        # Settings at bottom
        settings_label = QLabel("SETTINGS")
        settings_label.setObjectName("sidebarLabel")
        sidebar_layout.addWidget(settings_label)

        self.model_combo = QComboBox()
        self.model_combo.setObjectName("sidebarCombo")
        sidebar_layout.addWidget(self.model_combo)

        self.dark_mode = QCheckBox("Dark theme")
        self.dark_mode.setChecked(True)
        sidebar_layout.addWidget(self.dark_mode)

        sidebar.setLayout(sidebar_layout)

        # --- Main content area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar with model and actions
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 12, 20, 12)
        top_bar.addStretch(1)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("topBtn")
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("topBtn")
        top_bar.addWidget(self.export_btn)
        top_bar.addWidget(self.refresh_btn)
        content_layout.addLayout(top_bar)

        # Welcome message (shown when no messages)
        self.welcome_widget = QWidget()
        self.welcome_widget.setObjectName("welcomeWidget")
        welcome_layout = QVBoxLayout()
        welcome_layout.setAlignment(Qt.AlignCenter)
        
        welcome_title = QLabel("What can I help with?")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_title)
        self.welcome_widget.setLayout(welcome_layout)
        content_layout.addWidget(self.welcome_widget)

        # Transcript area (hidden initially)
        self.transcript = QTextEdit()
        self.transcript.setObjectName("transcript")
        self.transcript.setReadOnly(True)
        self.transcript.hide()
        content_layout.addWidget(self.transcript)

        # Input area at bottom
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(20, 12, 20, 20)
        
        input_bar = QHBoxLayout()
        input_bar.setSpacing(8)
        self.input = QLineEdit()
        self.input.setObjectName("mainInput")
        self.input.setPlaceholderText("Ask anything...")
        self.input.setMinimumHeight(50)
        self.send_btn = QPushButton("↑")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setMinimumSize(50, 50)
        self.send_btn.setMaximumSize(50, 50)
        input_bar.addWidget(self.input)
        input_bar.addWidget(self.send_btn)
        
        input_layout.addLayout(input_bar)
        input_container.setLayout(input_layout)
        content_layout.addWidget(input_container)

        content_widget.setLayout(content_layout)

        # Add sidebar and content to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_widget, 1)
        self.setLayout(main_layout)

        # Signals
        self.refresh_btn.clicked.connect(self.populate_models)
        self.send_btn.clicked.connect(self.on_send)
        self.input.returnPressed.connect(self.on_send)
        self.new_btn.clicked.connect(self.on_new_chat)
        self.export_btn.clicked.connect(self.on_export)
        self.dark_mode.toggled.connect(self.on_toggle_theme)
        self.history_list.itemClicked.connect(self.on_history_click)

        # Init models and load history
        self.populate_models()
        self.load_history()
        self.apply_system_prompt()

    def apply_system_prompt(self):
        prompt = SYSTEM_PROMPT
        if not prompt:
            return
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": prompt})
            save_turn(self.session_path, "system", prompt)

    def load_history(self):
        self.history_list.clear()
        if not SESSIONS_DIR.exists():
            return
        sessions = sorted(SESSIONS_DIR.glob("session-*.jsonl"), reverse=True)[:20]
        for s in sessions:
            # Read first user message as title
            try:
                lines = s.read_text(encoding="utf-8").strip().split("\n")
                title = "New chat"
                for line in lines:
                    data = json.loads(line)
                    if data.get("role") == "user":
                        title = data.get("content", "")[:40]
                        if len(data.get("content", "")) > 40:
                            title += "..."
                        break
                item = QListWidgetItem(title)
                item.setData(Qt.UserRole, str(s))
                self.history_list.addItem(item)
            except Exception:
                pass

    def on_history_click(self, item: QListWidgetItem):
        path = Path(item.data(Qt.UserRole))
        if not path.exists():
            return
        self.messages = []
        self.transcript.clear()
        self.session_path = path
        # Load messages from file
        try:
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if not line:
                    continue
                data = json.loads(line)
                role = data.get("role")
                content = data.get("content", "")
                self.messages.append({"role": role, "content": content})
                if role == "system":
                    self.transcript.append(f"<b>System:</b> {content}")
                elif role == "user":
                    self.transcript.append(f"<b>You:</b> {content}")
                elif role == "assistant":
                    self.transcript.append(f"<b>Assistant:</b> {content}")
            if self.messages:
                self.welcome_widget.hide()
                self.transcript.show()
        except Exception as e:
            self.transcript.append(f"[error] Could not load session: {e}")

    def populate_models(self):
        self.model_combo.clear()
        if not ensure_api_available():
            self.model_combo.addItem(DEFAULT_MODEL)
            self.transcript.append(f"[error] Ollama API unreachable at {OLLAMA_API}")
            return
        models = list_models()
        if models:
            for m in models:
                self.model_combo.addItem(m)
            # Select default if present
            idx = self.model_combo.findText(DEFAULT_MODEL)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.addItem(DEFAULT_MODEL)
            self.transcript.append("[warn] No local models found. Use 'ollama pull <model>'.")

    def on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        
        # Show transcript, hide welcome
        self.welcome_widget.hide()
        self.transcript.show()
        
        self.messages.append({"role": "user", "content": text})
        save_turn(self.session_path, "user", text)
        self.transcript.append(f"<b>You:</b> {text}")
        self.input.clear()
        
        # Check if this is a command request
        if is_command(text):
            self.execute_command(text)
        else:
            self.chat_with_llm(text)
    
    def execute_command(self, request: str):
        """Execute command using intelligent executor"""
        self.send_btn.setEnabled(False)
        self.input.setEnabled(False)
        
        self.transcript.append(f"<b>System:</b> 🔧 Executing command...")
        
        self.command_worker = CommandWorker(request)
        self.command_worker.progress.connect(self.on_command_progress)
        self.command_worker.done.connect(self.on_command_done)
        self.command_worker.start()
    
    def on_command_progress(self, message: str):
        """Handle command execution progress"""
        self.transcript.append(f"<i>{message}</i>")
        QApplication.processEvents()
    
    def on_command_done(self, report: dict):
        """Handle command execution completion"""
        summary = COMMAND_EXECUTOR.get_summary(report) if COMMAND_EXECUTOR else str(report)
        
        self.transcript.append(f"\n<b>Assistant:</b>\n{summary}")
        
        # Save to history
        save_turn(self.session_path, "assistant", summary)
        self.messages.append({"role": "assistant", "content": summary})
        
        self.send_btn.setEnabled(True)
        self.input.setEnabled(True)
        self.input.setFocus()
        self.load_history()
    
    def chat_with_llm(self, text: str):
        """Regular chat with LLM"""
        model = self.model_combo.currentText() or DEFAULT_MODEL
        self.send_btn.setEnabled(False)
        self.input.setEnabled(False)
        self.assistant_streaming_started = False

        self.worker = ChatWorker(model=model, messages=self.messages)
        self.worker.chunk.connect(self.on_chunk)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_chunk(self, chunk: str):
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.transcript.setTextCursor(cursor)
        # If starting assistant output, add a label line
        if not self.assistant_streaming_started:
            self.transcript.append("<b>Assistant:</b> ")
            self.assistant_streaming_started = True
        # Append without extra newline so it feels streaming
        self.transcript.insertPlainText(chunk)
        QApplication.processEvents()

    def on_done(self, full_text: str):
        self.transcript.append("")
        save_turn(self.session_path, "assistant", full_text)
        self.messages.append({"role": "assistant", "content": full_text})
        self.send_btn.setEnabled(True)
        self.input.setEnabled(True)
        self.input.setFocus()
        self.assistant_streaming_started = False
        self.load_history()

    def on_error(self, msg: str):
        self.transcript.append(f"\n[error] {msg}")
        self.send_btn.setEnabled(True)
        self.input.setEnabled(True)
        self.input.setFocus()

    def on_new_chat(self):
        self.messages = []
        self.session_path = SESSIONS_DIR / datetime.now().strftime("session-%Y%m%d-%H%M%S.jsonl")
        self.transcript.clear()
        self.transcript.hide()
        self.welcome_widget.show()
        self.apply_system_prompt()

    def on_export(self):
        # Export the current session to Markdown in sessions/
        md_lines = ["# Astra Chatbot Session\n"]
        for m in self.messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "system":
                md_lines.append(f"**System:** {content}\n")
            elif role == "user":
                md_lines.append(f"**You:** {content}\n")
            elif role == "assistant":
                md_lines.append(f"**Assistant:** {content}\n")
        out = "\n".join(md_lines)
        out_path = self.session_path.with_suffix(".md")
        out_path.write_text(out, encoding="utf-8")
        self.transcript.append(f"[saved] Exported Markdown to {out_path}")

    def on_toggle_theme(self, checked: bool):
        app = QApplication.instance()
        if not app:
            return
        self.dark_mode_enabled = checked
        app.setStyleSheet(get_styles(dark=checked))


def run_check() -> int:
    if not ensure_api_available():
        print("API unreachable at", OLLAMA_API)
        return 1
    models = list_models()
    print("Models:", ", ".join(models) or "<none>")
    return 0


# ----- Styles -----
def get_styles(dark: bool = True) -> str:
    if dark:
        return """
        QWidget { 
            font-family: 'Segoe UI', 'Ubuntu', sans-serif; 
            font-size: 14px; 
            color: #ececec; 
            background: #212121;
        }
        QFrame#sidebar { 
            background: #171717; 
            border-right: 1px solid #2d2d2d;
        }
        QLabel#sidebarLabel {
            color: #8e8ea0;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 8px 4px;
        }
        QPushButton#newChatBtn {
            background: #212121;
            border: 1px solid #4d4d4d;
            border-radius: 8px;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            color: #ececec;
        }
        QPushButton#newChatBtn:hover {
            background: #2a2a2a;
        }
        QListWidget#historyList {
            background: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }
        QListWidget#historyList::item {
            background: transparent;
            border-radius: 6px;
            padding: 10px;
            margin: 2px 0;
            color: #c5c5d2;
        }
        QListWidget#historyList::item:hover {
            background: #2a2a2a;
        }
        QListWidget#historyList::item:selected {
            background: #2f2f2f;
        }
        QComboBox#sidebarCombo {
            background: #2a2a2a;
            border: 1px solid #4d4d4d;
            border-radius: 6px;
            padding: 8px;
            color: #ececec;
        }
        QCheckBox {
            color: #c5c5d2;
            spacing: 8px;
        }
        QTextEdit#transcript {
            background: #212121;
            border: none;
            padding: 20px;
            color: #ececec;
            font-size: 15px;
            line-height: 1.6;
        }
        QWidget#welcomeWidget {
            background: #212121;
        }
        QLabel#welcomeTitle {
            font-size: 32px;
            font-weight: 300;
            color: #ececec;
            padding: 40px;
        }
        QWidget#inputContainer {
            background: #212121;
            border-top: 1px solid #2d2d2d;
        }
        QLineEdit#mainInput {
            background: #2f2f2f;
            border: 1px solid #4d4d4d;
            border-radius: 24px;
            padding: 12px 20px;
            color: #ececec;
            font-size: 15px;
        }
        QLineEdit#mainInput:focus {
            border: 1px solid #565869;
        }
        QPushButton#sendBtn {
            background: #676767;
            border: none;
            border-radius: 25px;
            color: #000;
            font-size: 20px;
            font-weight: bold;
        }
        QPushButton#sendBtn:hover {
            background: #8e8ea0;
        }
        QPushButton#topBtn {
            background: transparent;
            border: 1px solid #4d4d4d;
            border-radius: 6px;
            padding: 6px 14px;
            color: #c5c5d2;
            font-size: 13px;
        }
        QPushButton#topBtn:hover {
            background: #2a2a2a;
        }
        """
    else:
        return """
        QWidget { 
            font-family: 'Segoe UI', 'Ubuntu', sans-serif; 
            font-size: 14px; 
            color: #2d2d2d; 
            background: #ffffff;
        }
        QFrame#sidebar { 
            background: #f9f9f9; 
            border-right: 1px solid #e5e5e5;
        }
        QLabel#sidebarLabel {
            color: #6e6e80;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 8px 4px;
        }
        QPushButton#newChatBtn {
            background: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            color: #2d2d2d;
        }
        QPushButton#newChatBtn:hover {
            background: #f5f5f5;
        }
        QListWidget#historyList {
            background: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }
        QListWidget#historyList::item {
            background: transparent;
            border-radius: 6px;
            padding: 10px;
            margin: 2px 0;
            color: #4d4d4d;
        }
        QListWidget#historyList::item:hover {
            background: #f0f0f0;
        }
        QListWidget#historyList::item:selected {
            background: #e8e8e8;
        }
        QComboBox#sidebarCombo {
            background: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 8px;
            color: #2d2d2d;
        }
        QCheckBox {
            color: #4d4d4d;
            spacing: 8px;
        }
        QTextEdit#transcript {
            background: #ffffff;
            border: none;
            padding: 20px;
            color: #2d2d2d;
            font-size: 15px;
        }
        QWidget#welcomeWidget {
            background: #ffffff;
        }
        QLabel#welcomeTitle {
            font-size: 32px;
            font-weight: 300;
            color: #2d2d2d;
            padding: 40px;
        }
        QWidget#inputContainer {
            background: #ffffff;
            border-top: 1px solid #e5e5e5;
        }
        QLineEdit#mainInput {
            background: #f5f5f5;
            border: 1px solid #d0d0d0;
            border-radius: 24px;
            padding: 12px 20px;
            color: #2d2d2d;
            font-size: 15px;
        }
        QLineEdit#mainInput:focus {
            border: 1px solid #a0a0a0;
        }
        QPushButton#sendBtn {
            background: #2d2d2d;
            border: none;
            border-radius: 25px;
            color: #fff;
            font-size: 20px;
            font-weight: bold;
        }
        QPushButton#sendBtn:hover {
            background: #1a1a1a;
        }
        QPushButton#topBtn {
            background: transparent;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 6px 14px;
            color: #4d4d4d;
            font-size: 13px;
        }
        QPushButton#topBtn:hover {
            background: #f5f5f5;
        }
        """


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return run_check()
    
    # Initialize command executor in background
    init_thread = threading.Thread(target=init_command_executor, daemon=True)
    init_thread.start()
    
    app = QApplication(sys.argv)
    # Apply initial style (dark by default, like ChatGPT)
    app.setStyleSheet(get_styles(dark=True))
    w = ChatWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
