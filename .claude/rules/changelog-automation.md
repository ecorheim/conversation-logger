# Changelog Automation

## Principles

- **File**: `CHANGELOG.md` (project root)
- **Format**: Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- **Versioning**: Follow [Semantic Versioning](https://semver.org/)

## Execution Timing

Two workflows depending on branch:

**Development (dev branch):**
```
1. Complete work → 2. Update CHANGELOG.md ([Unreleased]) → 3. git add → 4. git commit
```

**Release (when merging dev → main):**
```
1. Determine version (semver)
2. Convert CHANGELOG.md [Unreleased] → [x.y.z] - YYYY-MM-DD
3. Update version files (see Version Files section)
4. Follow merge-strategy.md merge procedure
```

## Version Files

Release 시 아래 3개 파일의 버전을 동기화:

| File | Field |
|------|-------|
| `CHANGELOG.md` | `## [x.y.z] - YYYY-MM-DD` header |
| `.claude-plugin/plugin.json` | `version` |
| `.claude-plugin/marketplace.json` | `metadata.version`, `plugins[0].version` |

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
- [ ] Version files synced on release (plugin.json, marketplace.json)
