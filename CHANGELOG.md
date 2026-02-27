# Changelog

## [0.5.2] - 2026-02-27

### Fixed
- Fix empty tool results silently dropped from both text and markdown logs
  - When a tool produces no output, text logs now show `(no output)` and markdown logs show `> *(no output)*`
  - Previously, empty tool results were filtered out during content extraction and never reached the formatter
- Fix 5 tool input parameters missing from text format logs (`old_string`, `new_string`, `content`, `url`, `prompt`)
  - Text and markdown logs now display the same set of tool parameters for Edit, Write, and WebFetch tools
- Fix markdown response and follow-up timestamps missing the date component
  - Markdown logs now record full `YYYY-MM-DD HH:MM:SS` timestamps (matching text format), enabling reliable identification of sessions that span midnight

## [0.5.1] - 2026-02-26

### Fixed
- Fix log file split across multiple files when a session turn lasts over 1 hour
  - The Stop hook now refreshes the temp session cache timestamp before running stale cleanup, preventing the active session from being evicted by the 1-hour threshold
  - Previously, long turns (>1 hour) caused the temp session file to appear stale, leading to its deletion and a new log file being created on the next turn

## [0.5.0] - 2026-02-24

### Changed
- Enrich MEMORY.md maintenance instructions for better session recovery
  - Active Work entries now support multi-line format (goal, status, context, decisions, modified files, blockers, next step)
  - Decisions & Conventions and Resolved Issues entries now include the why, not just the what
  - MEMORY.md line budget increased from 200 to 600 to accommodate richer entries
  - Quality Gate reworded: "structured and concise" instead of "semantically compressed"

## [0.4.9] - 2026-02-23

### Fixed
- Fix new log files created when temp session is lost during a long session
  - When the temp session cache is missing (e.g., cleaned up after 1 hour of inactivity, or lost due to a race condition), the existing log file for the session is now located by searching the log directory for a matching session ID
  - If found, the existing file is reused and the temp session cache is restored to avoid repeated searches
  - Previously, any temp session loss caused a new log file to be created, splitting a single session across multiple files

## [0.4.8] - 2026-02-20

### Changed
- Replace mechanical prompt extraction with Claude-driven Active Work maintenance
  - SessionStart now injects Active Work maintenance directive into every session, including the MEMORY.md path so Claude knows exactly where to write
  - PreCompact hook simplified to timestamp marker plus modified files only
  - Stale compaction markers are removed on each compaction to prevent accumulation
  - Remove `extract_recent_prompts()` — replaced by Claude's own summaries in Active Work

## [0.4.7] - 2026-02-20

### Changed
- PreCompact hook now auto-saves recent user prompts to MEMORY.md Active Work section
  - Extracts last 3 user prompts from conversation log file before compaction
  - Post-compaction SessionStart automatically restores this context via additionalContext
  - Workaround for Claude Code bug #13668 (empty transcript_path in PreCompact)

## [0.4.6] - 2026-02-20

### Fixed
- Fix duplicate log files created when working directory changes during a session
  - Temp session files moved from `{cwd}/.claude/logs/` to `~/.claude/tmp/` so they are found regardless of cwd changes
  - When cwd changed mid-session, the original temp session was no longer found, causing a new log file with a different format to be created
  - `utils.py`: added `get_temp_session_dir()`, `delete_temp_session()`; updated `read_temp_session`, `write_temp_session`, `cleanup_stale_temp_files` signatures to use fixed path by default

## [0.4.5] - 2026-02-20

### Changed
- context-keeper default memory scope changed from `user` to `project`
  - Shared team memory (`.context-keeper/memory/MEMORY.md`) is now the default when no explicit scope is configured
  - Affects `scripts/utils.py` fallback, `CLAUDE.md`, `skills/context-keeper/SKILL.md`, and `commands/setup.md`

## [0.4.4] - 2026-02-20

### Fixed
- Log file and directory are automatically recreated if deleted during an active session
  - `log-response.py`: ensures the log directory exists before writing and writes the markdown header when starting a new file mid-session
  - `log-prompt.py`: ensures the log directory exists before writing

## [0.4.3] - 2026-02-20

### Fixed
- Fix new log file created on every prompt after session creation time was added to filenames
  - `log-prompt.py` now uses `resolve_log_path()` to reuse the cached log path from temp_session instead of generating a new timestamp on each call
  - `log-response.py` no longer deletes the temp_session file after the Stop hook; cleanup is handled by the SessionEnd handler

## [0.4.2] - 2026-02-19

### Changed
- Log filenames now include session creation time for easier ordering of same-day sessions
  - New format: `YYYY-MM-DD_HH-MM-SS_{session_id}_conversation-log.{txt|md}`
- Default memory scope in auto-generated config changed from `user` to `project`

### Fixed
- `MEMORY.md` is now auto-created on first context compaction when context-keeper is enabled but no memory file exists
  - Previously, context-keeper silently skipped saving state if `MEMORY.md` had never been initialized, causing session memory to never be written

## [0.4.1] - 2026-02-19

### Added
- Auto-create `conversation-logger-config.json` with default values at session start if no config file exists in the project or user scope

## [0.4.0] - 2026-02-19

### Added
- Context-keeper: automatic session memory continuity built into the plugin
  - `SessionStart` hook reads `MEMORY.md` and injects Active Work context into Claude's session prompt via `additionalContext`
  - `PreCompact` hook writes a compaction marker (trigger, timestamp, modified files) into the `## Active Work` section of `MEMORY.md` so the next session can recover in-progress work
  - Three memory scopes: `user` (personal, `~/.claude/projects/<project>/memory/MEMORY.md`), `project` (shared, `<cwd>/.context-keeper/memory/MEMORY.md`), `local` (per-project personal, gitignored)
  - Enabled by default (`enabled: true`, `scope: "user"`); configure via `context_keeper` key in the conversation-logger config file
  - Extracts recently modified files from the session transcript (Edit/Write tool uses) and lists them in the compaction marker for handoff context
- `/conversation-logger:context-keeper` skill for reviewing and managing MEMORY.md
  - Reports memory status, identifies stale Active Work entries, verifies Topic File Index sync
- Setup command (`/conversation-logger:setup`) now includes context-keeper configuration
  - Enables/disables context-keeper and selects memory scope (user/project/local)

### Changed
- `SessionStart` and `PreCompact` hook timeouts increased from 5s to 10s to accommodate MEMORY.md I/O

## [0.3.0] - 2026-02-18

### Added
- Log session lifecycle events: session start/end, subagent activity, context compaction, and tool failures
  - New `log-event.py` script handles six new hook events via a single entry point
  - `SessionStart`: records a session marker (source, model) at the top of each log file; creates session metadata so subsequent hooks can locate the log file before the first user prompt
  - `SessionEnd`: records session close reason; cleans up session metadata
  - `SubagentStart` / `SubagentStop`: records when Task-tool subagents are spawned and complete (type, ID)
  - `PreCompact`: records when context is compacted (auto or manual trigger)
  - `PostToolUseFailure`: records tool execution failures with tool name and first-line error summary (max 200 chars)
  - Text format: `~`-prefixed single-line entries for easy grep
  - Markdown format: `>` blockquote entries visually distinct from conversation headings

### Changed
- Markdown log header is now guaranteed even when `SessionStart` fires before the first user prompt
  - Extracted `ensure_markdown_header()` as a shared utility used by both `log-event.py` and `log-prompt.py`
- Log file path resolution refactored into shared `resolve_log_path()` utility used by `log-response.py` and `log-event.py`

## [0.2.4] - 2026-02-13

### Fixed
- Correct GitHub repository URLs in plugin metadata
  - .claude-plugin/plugin.json: Update homepage and repository fields to match actual GitHub organization
  - Change from `https://github.com/cruelds/claude-conversation-logger` to `https://github.com/ecorheim/conversation-logger`
  - Impact: Plugin marketplace links now point to the correct repository location

## [0.2.3] - 2026-02-13

### Changed
- Reorganize documentation structure for better accessibility
  - Move detailed architecture content from README.md to docs/architecture.md
  - README.md: Replace detailed diagrams with concise summary and link to architecture docs
  - docs/architecture.md: Add comprehensive architecture documentation including hook execution flow, session state management, and error handling
  - .claude/rules/merge-strategy.md: Add docs/architecture.md to main branch allowlist
  - Impact: README is now more user-friendly while preserving detailed technical documentation for developers

## [0.2.2] - 2026-02-12

### Changed
- Remove redundant session ID from log body content
  - Session ID is already included in the log filename (`YYYY-MM-DD_{session_id}_conversation-log.{ext}`)
  - Text format: merge timestamp into USER header line (`👤 USER (HH:MM:SS):`)
  - Markdown format: remove `> Session:` blockquote line below user heading
  - Impact: Cleaner log output without duplicated session information

### Fixed
- Fix tool rejection not being detected due to Unicode apostrophe mismatch
  - scripts/log-response.py: Change curly apostrophe (U+2019) to ASCII apostrophe (U+0027) in `classify_user_entry()` pattern matching
  - tests/test_classify.py: Fix test fixtures to use ASCII apostrophe matching actual Claude Code output
  - Impact: Tool rejections (e.g., "User declined to answer questions") are now correctly classified as TOOL_REJECTION, preserving assistant output in logs

## [0.2.1] - 2026-02-12

### Fixed
- Remove invalid `commands` field from plugin.json manifest
  - .claude-plugin/plugin.json: Remove `"commands": ["commands/setup.md"]` that caused schema validation failure
  - Impact: Resolves "commands: Invalid input" error when other users install the plugin
- Remove invalid `name` field from setup command frontmatter
  - commands/setup.md: Remove `name: setup` that is not part of the command spec
  - Impact: Ensures `/conversation-logger:setup` command is properly discovered

## [0.2.0] - 2026-02-12

### Added
- Setup command (`/conversation-logger:setup`) for interactive configuration
  - Supports global and project scope settings
- Configurable log format: plain text (default) or Markdown
  - Markdown: structured headings, code blocks, horizontal rules, icon-based interaction labels
- Dual config path system: `~/.claude/conversation-logger-config.json` (global), `{project}/.claude/conversation-logger-config.json` (project)
- Environment variable override (`CONVERSATION_LOG_FORMAT`)
- Dynamic backtick fencing in Markdown to prevent code block collision
- Shared utility module (`scripts/utils.py`) for common logic
- Comprehensive TDD test suite (79 tests across 6 modules)
  - Tier 1: E2E integration tests for critical path scenarios
  - Tier 2: Safety net tests for discovered edge cases
  - Tier 3: Regression guard tests for all core functions

### Changed
- **Breaking**: Tool results are no longer truncated at 10 lines (both text and markdown formats)
- **Breaking**: Tool input parameters are no longer truncated at 60 characters (both text and markdown formats)
- Refactored common logic (config loading, path generation, temp session, encoding, debug logging) into shared module

### Fixed
- Restore emoji prefixes in text format output that were unintentionally removed during v0.2.0 refactoring
  - scripts/log-prompt.py: Restore `👤 USER:` prefix in prompt header
  - scripts/log-response.py: Restore `👤 USER` prefix in follow-up interaction headers
  - scripts/log-response.py: Restore `🤖 CLAUDE` prefix in response header
  - Impact: Maintains visual consistency with v0.1.x text format output
- Fix incorrect parsing of tool rejection reason when user message contains "user message:" substring
  - scripts/log-response.py: Use `split("user message:", 1)` instead of `split("user message:")` to prevent over-splitting
  - Impact: Tool rejection reasons containing "user message:" are now fully preserved

## [0.1.3] - 2026-02-11

### Fixed
- Fix Windows compatibility issues causing hook failures
  - hooks/hooks.json: Replace 'python3' command with 'python' for cross-platform support
  - scripts/log-prompt.py, scripts/log-response.py: Update shebang from python3 to python
  - scripts/log-prompt.py, scripts/log-response.py: Add UTF-8 wrapper for stdin, stdout, and stderr on Windows
  - scripts/log-prompt.py, scripts/log-response.py: Remove Unicode characters from print statements
  - CONTRIBUTING.md: Update python3 reference to python
  - README.md: Add note about python PATH requirement for Windows users
  - Impact: Resolves "Failed with non-blocking status code: Python" error on Windows

## [0.1.0] - 2026-02-11

### Added
- Initial release
- User prompt logging via UserPromptSubmit hook
- Claude response and tool usage logging via Stop hook
- Log file separation by date and session ID
- Tool usage formatting (parameter summary, result truncation)
- Follow-up interaction support (user answers, plan approval, tool rejection, interrupt)
- Duplicate logging prevention mechanism
- Automatic cleanup of temporary files older than 1 hour