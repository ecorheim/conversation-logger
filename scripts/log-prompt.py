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
from utils import setup_encoding, get_log_dir, resolve_log_path, write_temp_session, ensure_markdown_header

# Ensure stdout/stderr can handle Unicode on Windows
setup_encoding()


def log_prompt():
    try:
        # Read JSON data from stdin
        input_data = json.load(sys.stdin)

        prompt = input_data.get("prompt", "")
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        # Resolve log path (reuses cached path from temp_session if available)
        log_file, log_format, log_dir = resolve_log_path(cwd, session_id)

        # Write prompt to log
        timestamp = datetime.now().strftime('%H:%M:%S')

        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            if log_format == "markdown":
                _write_prompt_markdown(f, log_file, prompt, timestamp)
            else:
                _write_prompt_text(f, prompt, timestamp)

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


def _write_prompt_text(f, prompt, timestamp):
    """Write prompt in text format."""
    f.write(f"\n{'='*80}\n")
    f.write(f"\U0001f464 USER ({timestamp}):\n{prompt}\n")
    f.write(f"{'-'*80}\n")


def _write_prompt_markdown(f, log_file, prompt, timestamp):
    """Write prompt in markdown format."""
    ensure_markdown_header(f, log_file)
    f.write(f"\n---\n\n")
    f.write(f"## \U0001f464 User \u2014 {timestamp}\n\n")
    f.write(f"{prompt}\n")


if __name__ == "__main__":
    log_prompt()
    sys.exit(0)