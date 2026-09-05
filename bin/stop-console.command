#!/bin/bash
# Stops the local research console.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${IBI_PORT:-8765}"
PIDS="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null)"
if [ -z "$PIDS" ]; then echo "Console is not running on port $PORT."; else
  echo "$PIDS" | xargs kill && echo "Stopped the console on port $PORT."
fi
