# Git Commit Rules

## Principles

1. **Use Gitmoji**: Emoji prefix indicating commit type
2. **English messages**: Write commit messages in English
3. **Self-explanatory**: Understandable without project context
4. Attribution disabled globally via ~/.claude/settings.json.

## Self-Explanatory Rules

Commit messages must be **understandable by others without project context**.

- Avoid: Internal jargon ("Phase 1-4"), vague descriptions ("improve structure"), implicit context ("temporary fix")
- Prefer: Specific descriptions, intuitive terms, clear impact

### Examples

```
❌ ♻️ refactor: clean up code
❌ 🐛 fix: fix Task-456

✅ ♻️ refactor: restructure MQTT client as singleton pattern
   - Reuse same connection across multiple components

✅ 🐛 fix: resolve memory leak on WiFi reconnection
   - Fix unreleased socket on EW11 module restart
```

## Commit Message Structure

```
<gitmoji> <type>: <subject>

<body>
```

## Common Gitmoji

📝 docs | ✨ feat | 🐛 fix | ♻️ refactor | 🎨 style | ✅ test | 🔧 chore | 🙈 .gitignore
