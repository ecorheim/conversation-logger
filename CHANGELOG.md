# Changelog

## [0.1.2] - 2026-02-11

### Fixed
- Fix Windows Unicode encoding error causing hook failure
  - scripts/log-prompt.py, scripts/log-response.py: Add UTF-8 stdout/stderr wrapper for Windows
  - scripts/log-prompt.py, scripts/log-response.py: Remove Unicode characters from print statements
  - Impact: Resolves "Failed with non-blocking status code: Python" error on Windows

## [0.1.1] - 2026-02-11

### Fixed
- Replace python3 with python for Windows compatibility
  - hooks/hooks.json: Update command entries to use 'python' instead of 'python3'
  - scripts/log-prompt.py, scripts/log-response.py: Update shebang lines
  - Impact: Plugin now works on Windows where 'python3' command is not available

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
