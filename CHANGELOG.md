# Changelog

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