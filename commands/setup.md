---
description: Configure conversation-logger plugin settings (log format)
---

You are configuring the **conversation-logger** plugin.

## Steps

1. **Show current format**: Check for existing config files and display the current log format setting.
   - Check `~/.claude/conversation-logger-config.json` (global)
   - Check `{project}/.claude/conversation-logger-config.json` (project)
   - Check `CONVERSATION_LOG_FORMAT` environment variable
   - Priority: ENV > project > global > default ("text")

2. **Ask scope**: Ask the user which scope to configure:
   - **global** — Applies to all projects (`~/.claude/conversation-logger-config.json`)
   - **project** — Applies to this project only (`{project}/.claude/conversation-logger-config.json`)

3. **Ask format**: Ask the user which log format to use:
   - **text** — Plain text format (`.txt` files, default)
   - **markdown** — Markdown format (`.md` files, with headings, code blocks, icons)

4. **Save config**: Use the Write tool to save the config JSON to the chosen path:
   ```json
   {
     "log_format": "markdown"
   }
   ```

5. **Confirm**: Display a confirmation message showing:
   - The scope chosen
   - The format chosen
   - The config file path written
   - A note that the setting takes effect on the next conversation
