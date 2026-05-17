#!/usr/bin/env bash
set -euo pipefail

SESSION_NAME="${1:-saved}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Session '$SESSION_NAME' already exists. Attaching..."
  tmux attach-session -t "$SESSION_NAME"
  exit 0
fi

# --- Window 1: Main (Hermes Gateway + AI dev) ---
tmux new-session -d -s "$SESSION_NAME" -n main

tmux send-keys -t "$SESSION_NAME" "hermes gateway run" Enter

tmux split-window -h -t "$SESSION_NAME"

tmux send-keys -t "$SESSION_NAME:.1" "hermes --tui" Enter

tmux split-window -v -t "$SESSION_NAME:.0"

# Clear the bottom-left pane of inherited TUI display junk
sleep 0.3
tmux send-keys -t "$SESSION_NAME:.1" "clear" Enter

tmux send-keys -t "$SESSION_NAME:.1" "opencode" Enter

# --- Window 2: Expo Go (app dev server + backend + shell) ---
tmux new-window -t "$SESSION_NAME" -n expo

# Pane 0 (top, full width): Expo dev server — shows QR code for Expo Go
tmux send-keys -t "$SESSION_NAME:expo" "cd rowapp/mobile && npx expo start" Enter

# Split vertically: Pane 1 (bottom) for backend API
tmux split-window -v -t "$SESSION_NAME:expo"

# Pane 1 (bottom-left): FastAPI backend
tmux send-keys -t "$SESSION_NAME:expo.1" "cd rowapp/backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" Enter

# Split horizontally: Pane 2 (bottom-right) for utility shell
sleep 0.3
tmux split-window -h -t "$SESSION_NAME:expo.1"

# Pane 2 (bottom-right): shell / utility — ready for git, npm, etc.
tmux send-keys -t "$SESSION_NAME:expo.2" "cd rowapp/mobile" Enter

tmux attach-session -t "$SESSION_NAME"
