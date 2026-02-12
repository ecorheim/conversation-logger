# Merge Strategy: dev → main

## tests/ Directory Exclusion

The `tests/` directory exists only in the `dev` branch and must NOT be included in `main`.

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

# 3. Handle conflicts (if tests/ causes modify/delete conflict)
#    This is expected when test files were modified in dev
git rm -r --cached tests/

# 4. Remove any untracked test files left on disk
rm -rf tests/

# 5. Commit using the SAME message as dev's last commit
git commit -m "<copy dev's last commit message including gitmoji, subject, and body>"

# 6. Create version tag on the merge commit
VERSION=$(python -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
git tag -a "v$VERSION" -m "v$VERSION"

# 7. Switch back to dev
#    tests/ files may need cleanup before checkout
rm -rf tests/ 2>/dev/null; git checkout dev
```

### Step Explanation

1. `--no-ff`: Force merge commit (prevent fast-forward)
2. `--no-commit`: Stop before committing to allow modifications
3. `git rm -r --cached tests/`: Remove tests/ from staging area only
4. `rm -rf tests/`: Clean up untracked test files on disk to prevent checkout conflicts
5. Commit message copies dev's last commit verbatim (gitmoji + type + subject + body)
6. Create annotated tag `v<version>` on the merge commit (e.g., `v0.2.2`)
7. Clean up and return to dev branch

## Rationale

- `main` is the release branch; test files are development-only artifacts
- `dev` retains full test coverage for development workflow
- Consistent commit messages between branches maintain clear git history on GitHub