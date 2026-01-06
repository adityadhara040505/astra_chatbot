import os
import json
import time
from datetime import datetime
from pathlib import Path

import httpx

OLLAMA_API = os.environ.get("OLLAMA_API", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("ASTRA_CHATBOT_MODEL", "llama3.2:1b")
SYSTEM_PROMPT = os.environ.get("ASTRA_CHATBOT_SYSTEM")

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_api_available() -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{OLLAMA_API}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def save_turn(session_path: Path, role: str, content: str) -> None:
    payload = {"ts": time.time(), "role": role, "content": content}
    session_path.write_text(
        (session_path.read_text() if session_path.exists() else "") + json.dumps(payload) + "\n",
        encoding="utf-8",
    )


def pick_model(default_model: str = DEFAULT_MODEL) -> str:
    # If the default exists locally, use it; otherwise prompt to pick from tags
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{OLLAMA_API}/api/tags")
            r.raise_for_status()
            tags = r.json().get("models", [])
            names = [m.get("name") for m in tags if m.get("name")]
            if default_model in names:
                return default_model
            if names:
                print("Available models:")
                for i, n in enumerate(names, 1):
                    print(f"  {i}. {n}")
                choice = input(f"Pick model [default: {names[0]}]: ").strip()
                return choice or names[0]
            else:
                print("No local models found. Use 'ollama pull <model>' first.")
                return default_model
    except Exception:
        return default_model


def chat_loop(model: str, system_prompt: str | None = SYSTEM_PROMPT) -> None:
    session_name = datetime.now().strftime("session-%Y%m%d-%H%M%S.jsonl")
    session_path = SESSIONS_DIR / session_name

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        save_turn(session_path, "system", system_prompt)

    print(f"Model: {model}")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit", ":q"}:
            print("Goodbye.")
            break

        messages.append({"role": "user", "content": user})
        save_turn(session_path, "user", user)

        try:
            with httpx.Client(timeout=None) as client:
                with client.stream(
                    "POST",
                    f"{OLLAMA_API}/api/chat",
                    json={"model": model, "messages": messages, "stream": True},
                ) as r:
                    assistant_text = ""
                    print("Assistant: ", end="", flush=True)
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
                            print(chunk, end="", flush=True)
                        if data.get("done"):
                            print()
                            break
                    if assistant_text:
                        messages.append({"role": "assistant", "content": assistant_text})
                        save_turn(session_path, "assistant", assistant_text)
        except httpx.HTTPError as e:
            print(f"\n[error] HTTP issue: {e}")
        except Exception as e:
            print(f"\n[error] {e}")


def main() -> None:
    if not ensure_api_available():
        print("Ollama API is unreachable at", OLLAMA_API)
        print("Ensure the service is running: 'sudo systemctl enable --now ollama'")
        return
    model = pick_model()
    chat_loop(model)


if __name__ == "__main__":
    main()
