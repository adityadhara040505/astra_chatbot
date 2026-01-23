#!/bin/bash
# Astra Chatbot Launcher

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Run the application
python astra_chatbot.py "$@"
