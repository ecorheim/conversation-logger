# Changelog

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
