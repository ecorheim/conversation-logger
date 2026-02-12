# PRD: Configurable Markdown Log Format (v0.2.0)

This PRD document is maintained in the conversation with the user.
See the plan mode transcript for the full PRD content.

## Summary

- Configurable log format: plain text (default) or Markdown
- Dual config path: global (`~/.claude/`) and project (`{project}/.claude/`)
- Priority: ENV > project > user > default
- Shared utility module (`scripts/utils.py`)
- Setup command (`/conversation-logger:setup`)
- Breaking changes: tool result/input truncation removed
- Dynamic backtick fencing for Markdown
