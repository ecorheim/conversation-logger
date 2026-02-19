# Changelog Automation

## Principles

- **File**: `CHANGELOG.md` (project root)
- **Format**: Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- **Versioning**: Follow [Semantic Versioning](https://semver.org/)

## Execution Timing

**Key**: Changelog updates must happen **before Git commit**

```
1. Complete work → 2. Update CHANGELOG.md → 3. git add (work files + CHANGELOG.md) → 4. git commit
```

## Classification Criteria

### Included

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Fixed**: Bug fixes
- **Security**: Security-related fixes
- **Deprecated**: Features to be removed in the future
- **Removed**: Removed features

### Excluded

- Code formatting, simple typos, comment-only changes, IDE config files

## Format Rules

```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description
```

1. **No emojis**
2. **Date format**: `YYYY-MM-DD`
3. **Category order**: Added → Changed → Deprecated → Removed → Fixed → Security
4. **Self-explanatory descriptions**: Understandable without project context (see `commit-message-format.md` for details)

## Example: Bug Fix

```markdown
## [Unreleased]

### Fixed
- Fix program unable to terminate gracefully
  - wifi/tcp_client.cpp: Add is_stopped_ flag in Stop() function
  - Impact: Program can now terminate normally via SIGINT (Ctrl+C)
```

```bash
git add wifi/tcp_client.cpp CHANGELOG.md
git commit -m "fix: resolve program unable to terminate gracefully"
```

## Verification Checklist

- [ ] Follows Keep a Changelog format
- [ ] Correct category classification
- [ ] Clear and specific descriptions
- [ ] CHANGELOG.md included in git add
