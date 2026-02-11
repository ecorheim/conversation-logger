#!/usr/bin/env python
"""
Claude Code Hook: Unified Conversation Logging (Prompt)
Triggered on UserPromptSubmit events to save user input and record temporary session info.
"""
import json
import sys
import os
from datetime import datetime

# Add scripts directory to path for utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import setup_encoding, get_log_dir, get_log_file_path, get_log_format, write_temp_session

# Ensure stdout/stderr can handle Unicode on Windows
setup_encoding()


def log_prompt():
    try:
        # Read JSON data from stdin
        input_data = json.load(sys.stdin)

        prompt = input_data.get("prompt", "")
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        # Set up log directory
        log_dir = get_log_dir(cwd)

        # Determine log format from config
        log_format = get_log_format(cwd)

        # Log file path
        log_file = get_log_file_path(log_dir, session_id, log_format)

        # Write prompt to log
        timestamp = datetime.now().strftime('%H:%M:%S')

        with open(log_file, 'a', encoding='utf-8') as f:
            if log_format == "markdown":
                _write_prompt_markdown(f, log_file, prompt, session_id, timestamp)
            else:
                _write_prompt_text(f, prompt, session_id, timestamp)

        # Save temporary session info (used by response hook)
        write_temp_session(log_dir, session_id, {
            "session_id": session_id,
            "prompt_timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "cwd": cwd,
            "log_format": log_format,
            "log_file_path": log_file
        })

        print("Prompt logged", file=sys.stderr)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error logging prompt: {e}", file=sys.stderr)
        sys.exit(1)


def _write_prompt_text(f, prompt, session_id, timestamp):
    """Write prompt in text format."""
    full_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(f"\n{'='*80}\n")
    f.write(f"[{full_timestamp}] Session: {session_id}\n")
    f.write(f"{'='*80}\n")
    f.write(f"\U0001f464 USER:\n{prompt}\n")
    f.write(f"{'-'*80}\n")


def _write_prompt_markdown(f, log_file, prompt, session_id, timestamp):
    """Write prompt in markdown format."""
    # Write document header if file is new/empty
    file_size = 0
    try:
        file_size = os.path.getsize(log_file)
    except OSError:
        pass

    if file_size == 0:
        date_str = datetime.now().strftime('%Y-%m-%d')
        f.write(f"# Conversation Log \u2014 {date_str}\n")

    f.write(f"\n---\n\n")
    f.write(f"## \U0001f464 User \u2014 {timestamp}\n")
    f.write(f"> Session: `{session_id}`\n\n")
    f.write(f"{prompt}\n")


if __name__ == "__main__":
    log_prompt()
    sys.exit(0)
