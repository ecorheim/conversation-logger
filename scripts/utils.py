#!/usr/bin/env python
"""
Shared utilities for conversation-logger plugin.
Common logic used by both log-prompt.py and log-response.py.
"""
import json
import sys
import os
import glob
from datetime import datetime

DEBUG = False  # Debug mode


def setup_encoding():
    """Wrap stdin/stdout/stderr with UTF-8 on Windows."""
    if sys.platform == "win32":
        import io
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_log_dir(cwd):
    """Get log directory path and ensure it exists."""
    log_dir = os.path.join(cwd, ".claude", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_log_file_path(log_dir, session_id, log_format):
    """Generate log file path with appropriate extension."""
    date_prefix = datetime.now().strftime('%Y-%m-%d')
    ext = ".md" if log_format == "markdown" else ".txt"
    return os.path.join(log_dir, f"{date_prefix}_{session_id}_conversation-log{ext}")


def _try_load_json(path):
    """Try to load JSON file. Returns dict or None. Warns on parse error."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            fmt = config.get("log_format", "").lower()
            if fmt in ("text", "markdown"):
                return config
            else:
                print(f"Warning: invalid log_format '{fmt}' in {path}, using default", file=sys.stderr)
                return None
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: failed to read config {path}: {e}, using default", file=sys.stderr)
        return None


def load_config(cwd):
    """Load config with priority: ENV > project > user > default."""
    # 1. Environment variable
    env_fmt = os.environ.get("CONVERSATION_LOG_FORMAT", "").lower()
    if env_fmt in ("text", "markdown"):
        return {"log_format": env_fmt}

    # 2. Project scope config
    project_config = os.path.join(cwd, ".claude", "conversation-logger-config.json")
    config = _try_load_json(project_config)
    if config:
        return config

    # 3. User scope config
    user_config = os.path.join(os.path.expanduser("~"), ".claude", "conversation-logger-config.json")
    config = _try_load_json(user_config)
    if config:
        return config

    # 4. Default
    return {"log_format": "text"}


def get_log_format(cwd):
    """Get log format from config. Returns 'text' or 'markdown'."""
    return load_config(cwd).get("log_format", "text")


def read_temp_session(log_dir, session_id):
    """Read temp session JSON file. Returns dict or None."""
    temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
    if not os.path.exists(temp_file):
        return None
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def write_temp_session(log_dir, session_id, data):
    """Write temp session JSON file."""
    temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def cleanup_stale_temp_files(log_dir, max_age_seconds=3600):
    """Remove temp session files older than max_age_seconds (default 1 hour)."""
    temp_pattern = os.path.join(log_dir, ".temp_session_*.json")
    for temp_f in glob.glob(temp_pattern):
        try:
            if os.path.getmtime(temp_f) < (datetime.now().timestamp() - max_age_seconds):
                os.remove(temp_f)
        except:
            pass


def debug_log(log_dir, message):
    """Write debug log entry."""
    if not DEBUG:
        return
    try:
        debug_file = os.path.join(log_dir, "debug-response.log")
        with open(debug_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


def calculate_fence(content):
    """Calculate minimum backtick fence that doesn't collide with content."""
    max_consecutive = 0
    current = 0
    for char in content:
        if char == '`':
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    return '`' * max(max_consecutive + 1, 3)  # minimum 3
