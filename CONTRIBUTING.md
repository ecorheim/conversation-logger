# Contributing

Thank you for your interest in contributing to conversation-logger!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-conversation-logger.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.6 or later
- Claude Code v1.0.33 or later

### Local Testing

Load the plugin locally to test your changes:

```bash
claude --plugin-dir ./conversation-logger
```

## Making Changes

### Code Style

- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Add docstrings to all functions
- Write comments in English

### Commit Messages

Follow the Gitmoji convention:

```
<gitmoji> <type>: <subject>

<body>
```

Common prefixes:
- ✨ feat: New feature
- 🐛 fix: Bug fix
- 📝 docs: Documentation
- ♻️ refactor: Code refactoring
- ✅ test: Tests

### Changelog

Update `CHANGELOG.md` under the `[Unreleased]` section before committing. Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## Pull Request Process

1. Ensure your changes work with `claude --plugin-dir`
2. Update `CHANGELOG.md` with your changes
3. Update `README.md` if you changed user-facing behavior
4. Submit a pull request with a clear description of changes

## Reporting Issues

When reporting bugs, please include:

- Claude Code version (`claude --version`)
- Python version (`python3 --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output from `.claude/logs/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
