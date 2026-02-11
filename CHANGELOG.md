# Changelog

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
