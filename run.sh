#!/bin/bash

# Activate the virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Git Bash on Windows
    source venv/Scripts/activate
    open_browser() {
        start http://127.0.0.1:5000
    }
elif [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # Linux or macOS
    source venv/bin/activate
    open_browser() {
        xdg-open http://127.0.0.1:5000 2>/dev/null || open http://127.0.0.1:5000
    }
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Open browser in background
( sleep 1 && open_browser ) &

# Trap Ctrl+C to deactivate
trap "echo 'Stopping Flask...'; deactivate; exit" INT

# Run Flask app
python app.py

# Just in case trap fails
deactivate
