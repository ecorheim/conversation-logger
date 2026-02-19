#!/usr/bin/env python
"""
Shared utilities for conversation-logger plugin.
Common logic used by both log-prompt.py and log-response.py.
"""
import json
import sys
import os
import glob
import tempfile
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


def resolve_log_path(cwd, session_id):
    """Resolve log file path: try temp_session first, fall back to config chain."""
    log_dir = get_log_dir(cwd)
    temp_data = read_temp_session(log_dir, session_id)
    if temp_data and temp_data.get("log_file_path"):
        return temp_data["log_file_path"], temp_data.get("log_format", "text"), log_dir
    log_format = get_log_format(cwd)
    log_file = get_log_file_path(log_dir, session_id, log_format)
    return log_file, log_format, log_dir


def ensure_markdown_header(f, log_file):
    """Write markdown document header if file is new/empty. Receives open file handle."""
    try:
        if os.path.getsize(log_file) == 0:
            date_str = datetime.now().strftime('%Y-%m-%d')
            f.write(f"# Conversation Log \u2014 {date_str}\n")
    except OSError:
        date_str = datetime.now().strftime('%Y-%m-%d')
        f.write(f"# Conversation Log \u2014 {date_str}\n")


# ---------------------------------------------------------------------------
# Context Keeper utilities
# ---------------------------------------------------------------------------

def get_context_keeper_config(cwd):
    """Get context-keeper config from conversation-logger config files.
    Returns: {"enabled": bool, "scope": str}
    Default: {"enabled": True, "scope": "user"}
    ENV (CONVERSATION_LOG_FORMAT) does not affect context_keeper settings.
    """
    for path in [
        os.path.join(cwd, ".claude", "conversation-logger-config.json"),
        os.path.join(os.path.expanduser("~"), ".claude", "conversation-logger-config.json"),
    ]:
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if "context_keeper" not in config:
                continue
            ck = config["context_keeper"]
            scope = ck.get("scope", "user")
            if scope not in ("user", "project", "local"):
                print(f"Warning: invalid context_keeper scope '{scope}', using 'user'", file=sys.stderr)
                scope = "user"
            return {"enabled": ck.get("enabled", True), "scope": scope}
        except (json.JSONDecodeError, IOError):
            continue
    return {"enabled": True, "scope": "user"}


def get_memory_path(cwd, scope="user"):
    """Get MEMORY.md path based on scope.
    - user:    ~/.claude/projects/<sanitized>/memory/MEMORY.md
    - project: <cwd>/.context-keeper/memory/MEMORY.md
    - local:   <cwd>/.context-keeper/memory.local/MEMORY.md
    """
    if scope == "project":
        return os.path.join(cwd, ".context-keeper", "memory", "MEMORY.md")
    elif scope == "local":
        return os.path.join(cwd, ".context-keeper", "memory.local", "MEMORY.md")
    else:  # user (default)
        if os.name == 'nt':
            sanitized = cwd.replace(':', '').replace('\\', '-').lstrip('-')
        else:
            sanitized = cwd.lstrip('/').replace('/', '-')
        return os.path.join(
            os.path.expanduser("~"), ".claude", "projects", sanitized, "memory", "MEMORY.md"
        )


def read_active_work(memory_file):
    """Extract ## Active Work section content from MEMORY.md.
    Returns section content as str, or empty string if not found or file missing.
    """
    if not os.path.isfile(memory_file):
        return ""
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        in_section = False
        result = []
        for line in lines:
            if not in_section:
                if line.startswith("## Active Work"):
                    in_section = True
            else:
                if line.startswith("## "):
                    break
                result.append(line)
        return "".join(result).strip()
    except (IOError, OSError) as e:
        print(f"Warning: failed to read {memory_file}: {e}", file=sys.stderr)
        return ""


def write_compaction_marker(memory_file, trigger, modified_files):
    """Insert compaction marker into ## Active Work section of MEMORY.md.
    Creates the section if it doesn't exist. Uses atomic write (temp + os.replace).
    """
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.splitlines(keepends=True)
    except (IOError, OSError) as e:
        print(f"Warning: failed to read {memory_file}: {e}", file=sys.stderr)
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    marker = f"<!-- compaction: {trigger} at {timestamp} -->"

    new_lines = []
    if any(line.startswith("## Active Work") for line in lines):
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.startswith("## Active Work"):
                new_lines.append(marker + "\n")
                if modified_files:
                    new_lines.append("- [Compaction occurred] Files modified in previous context:\n")
                    for fp in modified_files:
                        new_lines.append(f"  - {fp}\n")
                inserted = True
    else:
        new_lines = list(lines)
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append('\n')
        new_lines.append("## Active Work\n")
        new_lines.append(marker + "\n")
        if modified_files:
            new_lines.append("- [Compaction occurred] Files modified in previous context:\n")
            for fp in modified_files:
                new_lines.append(f"  - {fp}\n")

    try:
        dir_name = os.path.dirname(os.path.abspath(memory_file))
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=dir_name,
                                         delete=False, suffix='.tmp') as tmp:
            tmp.writelines(new_lines)
            tmp_path = tmp.name
        os.replace(tmp_path, memory_file)
    except (IOError, OSError) as e:
        print(f"Warning: failed to write compaction marker to {memory_file}: {e}", file=sys.stderr)


def extract_modified_files(transcript_path, max_lines=100, max_files=20):
    """Extract file paths from Edit/Write tool uses in transcript JSONL.
    Reads last max_lines lines, deduplicates, returns list of paths.
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        recent = lines[-max_lines:] if len(lines) > max_lines else lines
        seen = set()
        files = []
        for line in recent:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if entry.get("type") != "tool_use":
                continue
            if entry.get("tool_name") not in ("Edit", "Write"):
                continue
            fp = entry.get("tool_input", {}).get("file_path", "")
            if fp and fp not in seen:
                seen.add(fp)
                files.append(fp)
                if len(files) >= max_files:
                    break
        return files
    except (IOError, OSError) as e:
        print(f"Warning: failed to read transcript {transcript_path}: {e}", file=sys.stderr)
        return []


def build_restore_context(memory_file, source):
    """Build additionalContext string for SessionStart hook.
    Returns context string, or None if nothing to restore.
    """
    if not os.path.isfile(memory_file):
        return None
    active_work = read_active_work(memory_file)
    if active_work:
        return (
            f"[Context Keeper] Session source: {source}. "
            f"Active work detected from previous session:\n{active_work}\n"
            f"Read the full MEMORY.md and referenced topic files for complete context before continuing."
        )
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        if line_count > 5:
            return (
                f"[Context Keeper] Session source: {source}. "
                f"MEMORY.md exists ({line_count} lines) but no Active Work section found. "
                f"Read MEMORY.md if you need project context."
            )
    except (IOError, OSError):
        pass
    return None
