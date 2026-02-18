# Architecture

## How It Works

This plugin uses eight Claude Code hooks that work together:

1. **SessionStart** hook triggers `log-event.py` to record a session start marker and create session metadata
2. **UserPromptSubmit** hook triggers `log-prompt.py` to record the user's input immediately
3. **SubagentStart** / **SubagentStop** hooks trigger `log-event.py` to record subagent lifecycle events
4. **PostToolUseFailure** hook triggers `log-event.py` to record tool execution failures
5. **PreCompact** hook triggers `log-event.py` to record context compaction events
6. **Stop** hook triggers `log-response.py` to parse the session transcript and record Claude's response, including all tool usage
7. **SessionEnd** hook triggers `log-event.py` to record a session end marker and clean up session metadata

All outputs are appended to a single chronological log file per session.

## Architecture Overview

```mermaid
sequenceDiagram
    participant User
    participant Claude
    participant Prompt as log-prompt.py
    participant Temp as temp_session
    participant Response as log-response.py
    participant Log as conversation-log

    User->>Claude: Submit prompt
    Note over Claude,Prompt: UserPromptSubmit Hook (10s timeout)

    Claude->>Prompt: Trigger hook with JSON
    Prompt->>Prompt: Load config (utils.py)
    Prompt->>Temp: Save cwd/format/path
    Prompt->>Log: Append user prompt

    Claude->>Claude: Process & respond
    Note over Claude,Response: Stop Hook (30s timeout)

    Claude->>Response: Trigger hook
    Response->>Temp: Read session metadata
    Response->>Response: Parse transcript (JSONL)
    Response->>Response: Format output (text/md)
    Response->>Log: Append Claude response

    Note over Log: Single chronological file per session
```

## Data Flow

```mermaid
graph LR
    subgraph "Input"
        A[User Prompt<br/>stdin JSON]
    end

    subgraph "Prompt Hook"
        B[log-prompt.py]
        C[Config Loader<br/>utils.py]
    end

    subgraph "Session State"
        D[temp_session file<br/>cwd/format/path]
    end

    subgraph "Response Hook"
        E[log-response.py]
        F[Transcript Parser<br/>JSONL]
        G[Format Engine<br/>text/markdown]
    end

    subgraph "Output"
        H[.claude/logs/<br/>YYYY-MM-DD_session_conversation-log]
    end

    A --> B
    C --> B
    B --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

## Configuration Priority

```mermaid
graph TD
    A[Environment Variable<br/>CONVERSATION_LOG_FORMAT] -->|Highest| Z{Final Config}
    B[Project Config<br/>.claude/conversation-logger-config.json] -->|High| Z
    C[User Config<br/>~/.claude/conversation-logger-config.json] -->|Medium| Z
    D[Default<br/>text] -->|Lowest| Z

    Z --> E[Log Format Applied]
```

Configuration is loaded in priority order:
1. **Environment Variable** (`CONVERSATION_LOG_FORMAT`) — Highest priority
2. **Project Config** (`.claude/conversation-logger-config.json`) — Overrides user config
3. **User Config** (`~/.claude/conversation-logger-config.json`) — Global default
4. **Default** (`"text"`) — Fallback if no config exists

## Hook Execution Flow

### UserPromptSubmit Hook (`log-prompt.py`)

1. Receives user input via stdin (JSON format)
2. Loads configuration priority chain
3. Saves session metadata to temp file:
   - Working directory (cwd)
   - Log format (text/markdown)
   - Log file path
4. Appends formatted prompt to log file

**Timeout**: 10 seconds

### Stop Hook (`log-response.py`)

1. Reads session metadata from temp file
2. Parses session transcript (JSONL format)
3. Extracts Claude's response and tool usage:
   - Text output
   - Tool calls (name, parameters)
   - Tool results (full output, no truncation)
4. Formats output according to configured format
5. Appends to the same log file

**Timeout**: 30 seconds

## Session State Management

Session metadata is stored in a temporary file to bridge the two hooks:

**Location**: `/tmp/claude_session_{session_id}`

**Contents**:
```json
{
  "cwd": "/path/to/project",
  "format": "markdown",
  "log_file": "/path/to/project/.claude/logs/2026-02-13_abc123_conversation-log.md"
}
```

This approach ensures:
- No dependency between hook executions
- Consistent configuration across both hooks
- Resilience to hook failures (each hook is independent)

## File Organization

```
{project}/
└── .claude/
    └── logs/
        ├── 2026-02-13_abc123_conversation-log.txt
        ├── 2026-02-13_def456_conversation-log.md
        └── 2026-02-14_ghi789_conversation-log.txt
```

Each session creates a new log file with:
- Date prefix (`YYYY-MM-DD`)
- Session ID (8-character hex)
- Format-specific extension (`.txt` or `.md`)

## Error Handling

All scripts follow a consistent error handling pattern:

```python
try:
    # Main logic
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

Hook failures are logged but do not interrupt Claude's operation. Users can check `.claude/logs/` for error messages.
