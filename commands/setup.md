---
description: Configure conversation-logger plugin settings (log format and context-keeper)
---

You are configuring the **conversation-logger** plugin.

## Steps

1. **Show current settings**: Check for existing config files and display current settings.
   - Check `~/.claude/conversation-logger-config.json` (global)
   - Check `{project}/.claude/conversation-logger-config.json` (project)
   - Check `CONVERSATION_LOG_FORMAT` environment variable
   - Priority: ENV > project > global > default ("text")
   - Show both log format and context-keeper status (enabled/scope)

2. **Ask scope**: Ask the user which scope to configure:
   - **global** — Applies to all projects (`~/.claude/conversation-logger-config.json`)
   - **project** — Applies to this project only (`{project}/.claude/conversation-logger-config.json`)

3. **Ask format**: Ask the user which log format to use:
   - **text** — Plain text format (`.txt` files, default)
   - **markdown** — Markdown format (`.md` files, with headings, code blocks, icons)

4. **Ask context-keeper enabled**: Ask whether to enable context-keeper (session memory continuity):
   - **enabled** — Automatically saves/restores work context across sessions (default)
   - **disabled** — Turn off context-keeper functionality

5. **Ask context-keeper scope** (only if enabled): Ask which memory scope to use:
   - **user** — Personal memory at `~/.claude/projects/<project>/memory/MEMORY.md` (default, private)
   - **project** — Shared team memory at `{project}/.context-keeper/memory/MEMORY.md` (committed to git)
   - **local** — Per-project personal memory at `{project}/.context-keeper/memory.local/MEMORY.md` (gitignored)

6. **Save config**: Use the Write tool to save the config JSON to the chosen path:
   ```json
   {
     "log_format": "text",
     "context_keeper": {
       "enabled": true,
       "scope": "user"
     }
   }
   ```

7. **Confirm**: Display a confirmation message showing:
   - The scope chosen
   - The log format chosen
   - The context-keeper enabled status and memory scope
   - The config file path written
   - A note that the setting takes effect on the next conversation
