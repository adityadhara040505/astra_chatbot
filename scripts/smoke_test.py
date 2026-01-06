import os
import sys
import httpx

OLLAMA_API = os.environ.get("OLLAMA_API", "http://localhost:11434")
MODEL = os.environ.get("ASTRA_CHATBOT_MODEL", "llama3.2:1b")

try:
    with httpx.Client(timeout=5.0) as client:
        # Simple non-stream generate for a quick sanity check
        r = client.post(
            f"{OLLAMA_API}/api/generate",
            json={"model": MODEL, "prompt": "Say hello briefly.", "stream": False},
        )
        r.raise_for_status()
        data = r.json()
        print("Model:", MODEL)
        print("Response:", data.get("response", "<no response>"))
except Exception as e:
    print("Smoke test failed:", e)
    sys.exit(1)
