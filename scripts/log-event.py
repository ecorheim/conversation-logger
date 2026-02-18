#!/usr/bin/env python
"""
Claude Code Hook: Session Event Logging
Handles SessionStart, SessionEnd, SubagentStart, SubagentStop,
PreCompact, and PostToolUseFailure events.
"""
import json
import sys
import os
from datetime import datetime

# Add scripts directory to path for utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    setup_encoding, get_log_dir, get_log_format, get_log_file_path,
    write_temp_session, read_temp_session, cleanup_stale_temp_files,
    resolve_log_path, ensure_markdown_header
)

# Ensure stdout/stderr can handle Unicode on Windows
setup_encoding()


def _ts():
    return datetime.now().strftime('%H:%M:%S')


def handle_session_start(input_data, log_file, log_format, log_dir, session_id, cwd):
    source = input_data.get("source", "unknown")
    model = input_data.get("model", "")
    ts = _ts()

    # Create temp_session so subsequent hooks can find the log path.
    # log-prompt.py will overwrite this with prompt data later.
    if not read_temp_session(log_dir, session_id):
        write_temp_session(log_dir, session_id, {
            "session_id": session_id,
            "cwd": cwd,
            "log_format": log_format,
            "log_file_path": log_file
        })

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            ensure_markdown_header(f, log_file)
            model_part = f" | model: `{model}`" if model else ""
            f.write(f"> **Session Start** -- {ts} | `{source}`{model_part}\n")
        else:
            model_part = f" | model={model}" if model else ""
            f.write(f"~ SESSION START ({ts}) | source={source}{model_part}\n")


def handle_session_end(input_data, log_file, log_format, log_dir, session_id, cwd):
    reason = input_data.get("reason", "unknown")
    ts = _ts()

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            f.write(f"> **Session End** -- {ts} | reason: `{reason}`\n")
        else:
            f.write(f"~ SESSION END ({ts}) | reason={reason}\n")

    # Clean up temp_session if still present (Stop hook may have already deleted it)
    temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
    if os.path.exists(temp_file):
        os.remove(temp_file)

    cleanup_stale_temp_files(log_dir)


def handle_subagent_start(input_data, log_file, log_format, log_dir, session_id, cwd):
    agent_type = input_data.get("subagent_type", "unknown")
    agent_id = input_data.get("subagent_id", "")
    ts = _ts()

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            id_part = f" | id: `{agent_id}`" if agent_id else ""
            f.write(f"> **Subagent Start** -- {ts} | type: `{agent_type}`{id_part}\n")
        else:
            id_part = f" | id={agent_id}" if agent_id else ""
            f.write(f"~ SUBAGENT START ({ts}) | type={agent_type}{id_part}\n")


def handle_subagent_stop(input_data, log_file, log_format, log_dir, session_id, cwd):
    agent_type = input_data.get("subagent_type", "unknown")
    agent_id = input_data.get("subagent_id", "")
    ts = _ts()

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            id_part = f" | id: `{agent_id}`" if agent_id else ""
            f.write(f"> **Subagent Stop** -- {ts} | type: `{agent_type}`{id_part}\n")
        else:
            id_part = f" | id={agent_id}" if agent_id else ""
            f.write(f"~ SUBAGENT STOP ({ts}) | type={agent_type}{id_part}\n")


def handle_pre_compact(input_data, log_file, log_format, log_dir, session_id, cwd):
    trigger = input_data.get("trigger", "unknown")
    ts = _ts()

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            f.write(f"> **Context Compacted** -- {ts} | trigger: `{trigger}`\n")
        else:
            f.write(f"~ COMPACT ({ts}) | trigger={trigger}\n")


def handle_tool_failure(input_data, log_file, log_format, log_dir, session_id, cwd):
    tool_name = input_data.get("tool_name", "unknown")
    error = input_data.get("error", "unknown")
    error_short = error.split('\n')[0][:200]
    ts = _ts()

    with open(log_file, 'a', encoding='utf-8') as f:
        if log_format == "markdown":
            f.write(f"> **Tool Failed** -- {ts} | tool: `{tool_name}` | error: {error_short}\n")
        else:
            f.write(f"~ TOOL FAILED ({ts}) | tool={tool_name} | error={error_short}\n")


HANDLERS = {
    "SessionStart": handle_session_start,
    "SessionEnd": handle_session_end,
    "SubagentStart": handle_subagent_start,
    "SubagentStop": handle_subagent_stop,
    "PreCompact": handle_pre_compact,
    "PostToolUseFailure": handle_tool_failure,
}


def log_event():
    try:
        input_data = json.load(sys.stdin)

        event_name = input_data.get("hook_event_name", "")
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        if event_name not in HANDLERS:
            sys.exit(0)

        log_file, log_format, log_dir = resolve_log_path(cwd, session_id)

        HANDLERS[event_name](input_data, log_file, log_format, log_dir, session_id, cwd)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error logging event: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    log_event()
    sys.exit(0)
