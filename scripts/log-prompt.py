#!/usr/bin/env python
"""
Claude Code Hook: Unified Conversation Logging (Prompt)
Triggered on UserPromptSubmit events to save user input and record temporary session info.
"""
import json
import sys
import os
from datetime import datetime

# Ensure stdout/stderr can handle Unicode on Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def log_prompt():
    try:
        # Read JSON data from stdin
        input_data = json.load(sys.stdin)

        prompt = input_data.get("prompt", "")
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        # Set up log directory (project root/.claude/logs)
        log_dir = os.path.join(cwd, ".claude", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Log file (per date + session)
        date_prefix = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"{date_prefix}_{session_id}_conversation-log.txt")

        # Write prompt to log
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] Session: {session_id}\n")
            f.write(f"{'='*80}\n")
            f.write(f"👤 USER:\n{prompt}\n")
            f.write(f"{'-'*80}\n")

        # Save temporary session info (used by response hook)
        temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": session_id,
                "prompt_timestamp": datetime.now().isoformat(),
                "prompt": prompt
            }, f)

        print("Prompt logged", file=sys.stderr)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error logging prompt: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    log_prompt()
    sys.exit(0)
