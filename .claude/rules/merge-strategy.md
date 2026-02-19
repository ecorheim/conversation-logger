# Branch & Merge Strategy

## Remote Push Strategy

Two remotes are configured with different visibility:

```
origin   → git@github-ecorheim (public GitHub)                      → main only
private  → 192.168.1.220:10023 / git.cruelds.synology.me (NAS)     → main + dev
```

### Push Rules

- **main**: Push to both `origin` and `private`
- **dev**: Push to `private` only (NEVER push dev to origin)
- After every merge or commit on main: `git push origin main && git push private main`
- After every commit on dev: `git push private dev`

# Merge Strategy: dev → main

## Plugin Structure Allowlist

Only files matching the plugin structure below are included in `main`. Everything else stays in `dev` only.

```
.claude-plugin/          # Plugin metadata
.gitignore               # Repository settings
CHANGELOG.md             # Change history
CLAUDE.md                # Project instructions
CONTRIBUTING.md          # Contribution guide
LICENSE                  # License
README.md                # Project description
commands/                # Slash commands
docs/architecture.md     # Architecture documentation
docs/infographic.png     # README-referenced image
hooks/                   # Hook registration
scripts/log-event.py     # Session event hook script
scripts/log-prompt.py    # UserPromptSubmit hook script
scripts/log-response.py  # Stop hook script
scripts/utils.py         # Shared utilities
skills/                  # Skill definitions
```

**Excluded dev-only files** (examples): `tests/`, `.claude/rules/`, `.claude/settings.json`, `.claude/skills/`, `docs/design/`, `docs/prd/`, `docs/infographic.svg`, `scripts/convert-svg.js`

### Maintenance

When adding a new file that should ship to `main`, add it to both this allowlist and the `ALLOWED` regex in the Merge Procedure below.

## Pre-merge Version Check

Before merging, verify that the project version in `dev` has been bumped compared to `main`. **If the version has not changed, do NOT proceed with the merge.**

```bash
DEV_VERSION=$(git show dev:.claude-plugin/plugin.json | python -c "import sys,json; print(json.load(sys.stdin)['version'])")
MAIN_VERSION=$(git show main:.claude-plugin/plugin.json | python -c "import sys,json; print(json.load(sys.stdin)['version'])")

if [ "$DEV_VERSION" = "$MAIN_VERSION" ]; then
  echo "ERROR: dev version ($DEV_VERSION) is the same as main ($MAIN_VERSION)."
  echo "Bump the version in .claude-plugin/plugin.json and CHANGELOG.md before merging."
  exit 1
fi
```

### Checklist

- [ ] `.claude-plugin/plugin.json` version is bumped
- [ ] `.claude-plugin/marketplace.json` version fields synced (`metadata.version`, `plugins[0].version`)
- [ ] `CHANGELOG.md` has a new version entry matching the bumped version
- [ ] Version follows [Semantic Versioning](https://semver.org/): patch for fixes, minor for features, major for breaking changes

## Commit Message

The merge commit on `main` must use the **same commit message as the last dev commit**, not a merge-style message. This is because `main` is the public-facing branch on GitHub.

```
❌ 🔀 merge: v0.2.2 fix tool rejection ...
✅ 🐛 fix: resolve tool rejection misclassification ...
```

## Merge Procedure

When merging `dev` into `main`, always follow these steps:

```bash
# 1. Switch to main
git checkout main

# 2. Start merge without committing
git merge --no-ff --no-commit dev

# 3. Remove non-allowlisted files from staging area
ALLOWED='^(\.claude-plugin/|\.gitignore$|CHANGELOG\.md$|CLAUDE\.md$|CONTRIBUTING\.md$|LICENSE$|README\.md$|commands/|docs/architecture\.md$|docs/infographic\.png$|hooks/|scripts/log-event\.py$|scripts/log-prompt\.py$|scripts/log-response\.py$|scripts/utils\.py$|skills/)'
git diff --cached --name-only | grep -vE "$ALLOWED" | xargs -r git rm --cached

# 4. Remove non-allowlisted files left on disk
find . -maxdepth 3 -not -path './.git/*' -type f | sed 's|^\./||' | grep -vE "$ALLOWED" | xargs -r rm -f

# 5. Commit using the SAME message as dev's last commit
git commit -m "<copy dev's last commit message including gitmoji, subject, and body>"

# 6. Create version tag on the merge commit
VERSION=$(python -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
git tag -a "v$VERSION" -m "v$VERSION"

# 7. Push main to both remotes
git push origin main && git push private main

# 8. Push the version tag to both remotes
git push origin "v$VERSION" && git push private "v$VERSION"

# 9. Switch back to dev
git checkout dev
```

### Step Explanation

1. `--no-ff`: Force merge commit (prevent fast-forward)
2. `--no-commit`: Stop before committing to allow modifications
3. Unstage non-allowlisted files using the `ALLOWED` regex pattern (plugin structure only)
4. Delete non-allowlisted files from disk to prevent checkout conflicts
5. Commit message copies dev's last commit verbatim (gitmoji + type + subject + body)
6. Create annotated tag `v<version>` on the merge commit (e.g., `v0.2.2`)
7. Push main branch to origin (public) and private
8. Push version tag to both remotes
9. Clean up and return to dev branch

## Rationale

- `main` is the release branch containing only plugin-distributable files
- `dev` retains full development environment (tests, rules, design docs, build scripts)
- Allowlist approach ensures new dev-only files are excluded by default without manual updates
- Consistent commit messages between branches maintain clear git history on GitHub
