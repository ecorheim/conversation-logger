# conversation-logger

A Claude Code plugin that automatically logs conversations. Records prompts and responses chronologically in a single file, including tool usage tracking.

## Features

- Prompts and responses recorded sequentially in a single file
- Log files separated by date and session ID
- Speaker identification with emoji markers (👤 USER, 🤖 CLAUDE)
- Tool usage and result tracking
- Follow-up interaction support (user answers, plan approval/rejection, interrupt)
- Duplicate logging prevention

## How It Works

This plugin uses two Claude Code hooks that work together:

1. **UserPromptSubmit** hook triggers `log-prompt.py` to record the user's input immediately
2. **Stop** hook triggers `log-response.py` to parse the session transcript and record Claude's response, including all tool usage

Both outputs are appended to a single chronological log file per session.

## Installation

### Via Marketplace

```bash
# 1. Add marketplace
/plugin marketplace add ecorheim/conversation-logger

# 2. Install plugin
/plugin install conversation-logger@ecorheim-plugins
```

### Local Installation (Development/Testing)

```bash
claude --plugin-dir ./conversation-logger
```

### Requirements

- Claude Code v1.0.33 or later
- Python 3.6 or later (`python` must be available in PATH)
  - Windows: Ensure "Add Python to PATH" is checked during installation

## Log Format

Filename: `{project}/.claude/logs/YYYY-MM-DD_{session_id}_conversation-log.txt`

```
================================================================================
[YYYY-MM-DD HH:MM:SS] Session: abc123def456
================================================================================
👤 USER:
Write a hello world program in Python
--------------------------------------------------------------------------------
🤖 CLAUDE [YYYY-MM-DD HH:MM:SS]:
● Here's a simple Hello World program in Python.

● Write(file_path=hello.py)
  ⎿  print('Hello, World!')
================================================================================
```

### Follow-up Interactions

```
👤 USER (answer):
I'll use React
--------------------------------------------------------------------------------
🤖 CLAUDE [YYYY-MM-DD HH:MM:SS]:
● I'll implement it with React.
================================================================================
```

## Plugin Structure

```
conversation-logger/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # Marketplace catalog
├── hooks/
│   └── hooks.json           # Hook config (UserPromptSubmit, Stop)
├── scripts/
│   ├── log-prompt.py        # Prompt logging script
│   └── log-response.py      # Response logging script
├── CONTRIBUTING.md
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Viewing Logs

```bash
# View today's logs
cat .claude/logs/$(date +%Y-%m-%d)_*_conversation-log.txt

# Real-time monitoring
tail -f .claude/logs/*_conversation-log.txt
```

## Security Notice

Log files contain all conversation content. Be cautious when entering sensitive information such as API keys or passwords.

```bash
# Set log file permissions
chmod 600 .claude/logs/*.txt
chmod 700 .claude/logs
```

## License

MIT