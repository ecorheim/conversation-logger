---
name: context-keeper
description: >
  Manages auto memory for session continuity. Automatically records
  architecture decisions, resolved issues, user preferences, and project
  patterns to MEMORY.md. Maintains Active Work section as recovery anchor
  for context compaction and new sessions. Invoke to review memory status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Auto Memory Management Protocol

## Core Principle: Recoverability Test

Before deciding whether to record something, ask yourself:
**"If this session ended now and a new Claude started fresh, could it continue this work seamlessly using only MEMORY.md?"**

If the answer is no — record what's missing.

## Recording Protocol

### When to Record (Triggers)

Record to auto memory when ANY of these occur:

1. **Decision made**: An architecture, design, or approach decision is finalized
2. **Problem resolved**: A non-trivial bug is diagnosed and fixed
3. **Preference stated**: The user expresses an explicit workflow or style preference
4. **Pattern discovered**: A project structure, convention, or recurring pattern is newly identified

Additionally, update the **Active Work** section:
- When starting a significant task
- When reaching a milestone within a task
- When completing a task

### What to Record

- **Decisions**: what was decided + why + alternatives rejected
- **Solutions**: problem + root cause + fix (not the debugging journey)
- **Patterns**: convention + example + file location
- **Preferences**: user's stated preference, verbatim

### What NOT to Record

- Speculative hypotheses not yet verified
- Temporary debugging output or intermediate states
- Information already present in CLAUDE.md or .claude/rules/
- One-time information with no future value
- Trivial interactions (simple questions, one-off lookups)

### Quality Gate (Self-Verification)

Before writing to memory, ask these three questions:
1. "Would a different Claude understand this without additional context?"
2. "Is this structured and concise — not verbose, but not so terse that key context is lost?"
3. "Does this add information not already present in memory?"

If any answer is no, revise before recording.

## MEMORY.md Structure Guide

Keep MEMORY.md under 600 lines. Use this section structure:

### Active Work (Recovery Anchor)
For each active task, record with enough detail to resume without re-reading code:
```
- **[Goal]**
  Status: [current progress]
  Context: [why this task exists, key background]
  Decisions: [key choices made and why]
  Modified: [files changed, if relevant]
  Blockers: [current blockers, if any]
  Next: [concrete next step]
  See: [topic-file.md] (if detailed notes exist)
```
Not all fields are required — simple tasks may need only 2-3 lines.

This section is the primary recovery point after compaction or new sessions.

### Project Overview
Architecture summary, key directories, tech stack. Brief.

### Decisions & Conventions
Verified decisions and coding standards. Include the why, not just the what.
Format: `- [Decision]: [why it was made, alternatives rejected]`

### Resolved Issues
`- Problem → Cause → Solution` format. Include enough detail to avoid re-diagnosing.
Add context when the cause was non-obvious or the fix was non-trivial.

### User Preferences
Communication style, workflow habits, tool preferences.

### Topic File Index
`- filename.md: one-line description`

When creating or deleting a topic file, always update this index.

## Topic File Management

- Create a topic file when a MEMORY.md section would exceed ~30 lines of detail
- Name descriptively: `debugging.md`, `architecture.md`, `api-patterns.md`
- MEMORY.md remains the concise index; topic files hold the depth
- Reference topic files from the Active Work section for quick recovery

## Memory Scope and Storage

conversation-logger supports three storage scopes for context-keeper memory:

### Scope Types

- **user**: `~/.claude/projects/<sanitized>/memory/MEMORY.md`
  - Personal memory, not visible to teammates
  - Claude Code standard auto-memory location

- **project** (default): `<cwd>/.context-keeper/memory/MEMORY.md`
  - Shared team memory, committed to git for collaboration
  - Add `.context-keeper/memory/` directory to git tracking

- **local**: `<cwd>/.context-keeper/memory.local/MEMORY.md`
  - Per-project personal memory, gitignored
  - For personal debugging notes, experiments

### Scope 설정 방법

conversation-logger config 파일에서 `context_keeper` 섹션으로 설정합니다:

```json
// 프로젝트별 설정: {project}/.claude/conversation-logger-config.json
{
  "log_format": "text",
  "context_keeper": {
    "enabled": true,
    "scope": "project"
  }
}
```

```json
// 사용자 전역 설정: ~/.claude/conversation-logger-config.json
{
  "log_format": "text",
  "context_keeper": {
    "scope": "user"
  }
}
```

비활성화하려면 `"enabled": false`로 설정합니다.
`/conversation-logger:setup` 커맨드로도 설정할 수 있습니다.

## Session Recovery Protocol

When a new session starts (conversation-logger injects MEMORY.md context automatically):

1. Check the scope and memory path information provided in the session context
2. Read the **Active Work** section to identify ongoing tasks
3. If active work exists, read referenced topic files for full context
4. Resume from the documented "Next Step"
5. Update Active Work if the status has changed since last recorded

Conversation logs at `{project}/.claude/logs/` provide additional session history
if you need to review what was discussed in a previous session.

## Maintenance

- On task completion: move from Active Work to Resolved Issues (if noteworthy), or remove
- When MEMORY.md approaches 600 lines: move detailed content to topic files
- Periodically remove outdated entries and consolidate related items
- When a topic file is no longer referenced, consider archiving or deleting it

## Manual Invocation

When invoked with `/conversation-logger:context-keeper`:
1. Read the current MEMORY.md
2. Report memory status: total lines, section sizes, topic file count
3. Identify stale entries (Active Work with no recent updates)
4. Suggest cleanup actions if needed
5. Verify Topic File Index is in sync with actual files

For the MEMORY.md structure template and examples, see [template.md](template.md).