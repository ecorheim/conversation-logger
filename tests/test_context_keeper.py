"""Tests for context-keeper utilities in scripts/utils.py."""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import utils


def _write_config(tmpdir, config, scope="project"):
    """Write a conversation-logger config file for testing."""
    if scope == "project":
        claude_dir = os.path.join(tmpdir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        path = os.path.join(claude_dir, "conversation-logger-config.json")
    else:
        claude_dir = os.path.join(tmpdir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        path = os.path.join(claude_dir, "conversation-logger-config.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f)
    return path


def _write_memory(path, content):
    """Create MEMORY.md at given path with content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


# ---------------------------------------------------------------------------
# get_context_keeper_config
# ---------------------------------------------------------------------------
class TestGetContextKeeperConfig(unittest.TestCase):

    def test_default_when_no_config(self):
        """Returns enabled=True, scope=user when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                result = utils.get_context_keeper_config(tmpdir)
                self.assertTrue(result["enabled"])
                self.assertEqual(result["scope"], "user")

    def test_disabled(self):
        """enabled: false is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                _write_config(tmpdir, {
                    "log_format": "text",
                    "context_keeper": {"enabled": False}
                })
                result = utils.get_context_keeper_config(tmpdir)
                self.assertFalse(result["enabled"])

    def test_custom_scope(self):
        """scope value from config is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                _write_config(tmpdir, {
                    "log_format": "text",
                    "context_keeper": {"enabled": True, "scope": "project"}
                })
                result = utils.get_context_keeper_config(tmpdir)
                self.assertEqual(result["scope"], "project")

    def test_local_scope(self):
        """scope=local is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                _write_config(tmpdir, {
                    "log_format": "text",
                    "context_keeper": {"scope": "local"}
                })
                result = utils.get_context_keeper_config(tmpdir)
                self.assertEqual(result["scope"], "local")

    def test_invalid_scope_falls_back_to_user(self):
        """Invalid scope value falls back to 'user' with a warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                _write_config(tmpdir, {
                    "log_format": "text",
                    "context_keeper": {"scope": "bogus"}
                })
                with patch('sys.stderr'):
                    result = utils.get_context_keeper_config(tmpdir)
                self.assertEqual(result["scope"], "user")

    def test_config_without_context_keeper_key_returns_defaults(self):
        """Config with only log_format but no context_keeper returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                _write_config(tmpdir, {"log_format": "markdown"})
                result = utils.get_context_keeper_config(tmpdir)
                self.assertTrue(result["enabled"])
                self.assertEqual(result["scope"], "user")

    def test_user_scope_config_used_when_no_project_config(self):
        """Falls through to user config when no project config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                # Write only user config (HOME/.claude/...)
                user_claude_dir = os.path.join(tmpdir, ".claude")
                os.makedirs(user_claude_dir, exist_ok=True)
                with open(os.path.join(user_claude_dir, "conversation-logger-config.json"), 'w') as f:
                    json.dump({"log_format": "text", "context_keeper": {"scope": "local"}}, f)
                # Use a different cwd (no project config there)
                result = utils.get_context_keeper_config(tmpdir + "/subdir/that/does/not/exist")
                self.assertEqual(result["scope"], "local")


# ---------------------------------------------------------------------------
# get_memory_path
# ---------------------------------------------------------------------------
class TestGetMemoryPath(unittest.TestCase):

    def test_user_scope_path_structure(self):
        """user scope builds ~/.claude/projects/<sanitized>/memory/MEMORY.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                path = utils.get_memory_path("/test/project", scope="user")
                self.assertIn(".claude", path)
                self.assertIn("projects", path)
                self.assertTrue(path.endswith("MEMORY.md"))
                self.assertIn("memory", path)

    def test_user_scope_sanitizes_slashes(self):
        """user scope replaces / with - in project path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                path = utils.get_memory_path("/test/my/project", scope="user")
                # sanitized: test-my-project
                self.assertIn("test-my-project", path)

    def test_project_scope_path(self):
        """project scope uses <cwd>/.context-keeper/memory/MEMORY.md."""
        path = utils.get_memory_path("/my/project", scope="project")
        self.assertEqual(path, "/my/project/.context-keeper/memory/MEMORY.md")

    def test_local_scope_path(self):
        """local scope uses <cwd>/.context-keeper/memory.local/MEMORY.md."""
        path = utils.get_memory_path("/my/project", scope="local")
        self.assertEqual(path, "/my/project/.context-keeper/memory.local/MEMORY.md")

    def test_default_scope_is_user(self):
        """Calling without scope argument defaults to user scope."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                path = utils.get_memory_path("/some/cwd")
                self.assertIn(".claude", path)
                self.assertIn("projects", path)


# ---------------------------------------------------------------------------
# read_active_work
# ---------------------------------------------------------------------------
class TestReadActiveWork(unittest.TestCase):

    def test_extracts_active_work_section(self):
        """Returns content between ## Active Work and next ## header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, (
                "# Project Memory\n\n"
                "## Active Work\n"
                "- task A | in progress | Next: step 2\n"
                "- task B | done\n\n"
                "## Decisions\n"
                "- use sqlite\n"
            ))
            result = utils.read_active_work(memory_file)
            self.assertIn("task A", result)
            self.assertIn("task B", result)
            self.assertNotIn("## Decisions", result)
            self.assertNotIn("use sqlite", result)

    def test_returns_empty_when_section_missing(self):
        """Returns empty string when ## Active Work section is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Decisions\n- some decision\n")
            result = utils.read_active_work(memory_file)
            self.assertEqual(result, "")

    def test_returns_empty_when_file_missing(self):
        """Returns empty string when MEMORY.md does not exist."""
        result = utils.read_active_work("/does/not/exist/MEMORY.md")
        self.assertEqual(result, "")

    def test_section_at_end_of_file(self):
        """Handles Active Work as the last section (no following ## header)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Active Work\n- ongoing task\n")
            result = utils.read_active_work(memory_file)
            self.assertIn("ongoing task", result)


# ---------------------------------------------------------------------------
# write_compaction_marker
# ---------------------------------------------------------------------------
class TestWriteCompactionMarker(unittest.TestCase):

    def test_inserts_marker_after_active_work_header(self):
        """Marker is inserted immediately after ## Active Work line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Active Work\n- task A\n")
            utils.write_compaction_marker(memory_file, "auto", [])
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.splitlines()
            aw_idx = next(i for i, l in enumerate(lines) if l.startswith("## Active Work"))
            self.assertIn("<!-- compaction:", lines[aw_idx + 1])

    def test_creates_active_work_section_when_missing(self):
        """Creates ## Active Work section when it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Decisions\n- use sqlite\n")
            utils.write_compaction_marker(memory_file, "manual", [])
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("## Active Work", content)
            self.assertIn("<!-- compaction:", content)

    def test_includes_modified_files_list(self):
        """Modified files are listed under the compaction marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Active Work\n- task\n")
            utils.write_compaction_marker(
                memory_file, "auto",
                ["/src/foo.py", "/src/bar.py"]
            )
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("/src/foo.py", content)
            self.assertIn("/src/bar.py", content)
            self.assertIn("Compaction occurred", content)

    def test_atomic_write_preserves_file(self):
        """Original file is replaced atomically; file exists after write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Active Work\n- task\n")
            original_inode = os.stat(memory_file).st_ino
            utils.write_compaction_marker(memory_file, "auto", [])
            self.assertTrue(os.path.isfile(memory_file))
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("## Active Work", content)

    def test_graceful_when_file_missing(self):
        """Does not crash when memory file does not exist."""
        with patch('sys.stderr'):
            utils.write_compaction_marker("/does/not/exist/MEMORY.md", "auto", [])
        # No exception raised = pass


# ---------------------------------------------------------------------------
# extract_modified_files
# ---------------------------------------------------------------------------
class TestExtractModifiedFiles(unittest.TestCase):

    def _make_transcript(self, tmpdir, entries):
        path = os.path.join(tmpdir, "transcript.jsonl")
        with open(path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        return path

    def test_extracts_edit_and_write_paths(self):
        """Edit and Write tool_use entries are extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_transcript(tmpdir, [
                {"type": "tool_use", "tool_name": "Edit",
                 "tool_input": {"file_path": "/src/a.py"}},
                {"type": "tool_use", "tool_name": "Write",
                 "tool_input": {"file_path": "/src/b.py"}},
            ])
            result = utils.extract_modified_files(path)
            self.assertIn("/src/a.py", result)
            self.assertIn("/src/b.py", result)

    def test_ignores_non_edit_write_tools(self):
        """Bash and Read tool_use entries are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_transcript(tmpdir, [
                {"type": "tool_use", "tool_name": "Bash",
                 "tool_input": {"command": "ls"}},
                {"type": "tool_use", "tool_name": "Read",
                 "tool_input": {"file_path": "/src/a.py"}},
            ])
            result = utils.extract_modified_files(path)
            self.assertEqual(result, [])

    def test_deduplicates_paths(self):
        """Same file appearing multiple times is returned once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_transcript(tmpdir, [
                {"type": "tool_use", "tool_name": "Edit",
                 "tool_input": {"file_path": "/src/a.py"}},
                {"type": "tool_use", "tool_name": "Edit",
                 "tool_input": {"file_path": "/src/a.py"}},
            ])
            result = utils.extract_modified_files(path)
            self.assertEqual(result.count("/src/a.py"), 1)

    def test_empty_transcript(self):
        """Empty JSONL file returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_transcript(tmpdir, [])
            result = utils.extract_modified_files(path)
            self.assertEqual(result, [])

    def test_returns_empty_when_file_missing(self):
        """Missing transcript returns empty list."""
        result = utils.extract_modified_files("/does/not/exist.jsonl")
        self.assertEqual(result, [])

    def test_returns_empty_for_empty_path(self):
        """Empty string transcript_path returns empty list."""
        result = utils.extract_modified_files("")
        self.assertEqual(result, [])

    def test_ignores_malformed_json_lines(self):
        """Malformed JSONL lines are skipped without crashing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "transcript.jsonl")
            with open(path, 'w', encoding='utf-8') as f:
                f.write("not-valid-json\n")
                f.write(json.dumps({"type": "tool_use", "tool_name": "Edit",
                                    "tool_input": {"file_path": "/src/ok.py"}}) + "\n")
            result = utils.extract_modified_files(path)
            self.assertEqual(result, ["/src/ok.py"])


# ---------------------------------------------------------------------------
# build_restore_context
# ---------------------------------------------------------------------------
class TestBuildRestoreContext(unittest.TestCase):

    def test_returns_message_when_active_work_present(self):
        """Returns context string containing active work content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, (
                "# Memory\n\n"
                "## Active Work\n"
                "- build feature X | 50% | Next: write tests\n"
            ))
            result = utils.build_restore_context(memory_file, "startup")
            self.assertIsNotNone(result)
            self.assertIn("[Context Keeper]", result)
            self.assertIn("Active work detected", result)
            self.assertIn("build feature X", result)
            self.assertIn("startup", result)

    def test_returns_message_when_no_active_work_but_large_memory(self):
        """Returns context string when MEMORY.md has >5 lines but no Active Work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            content = "# Memory\n\n## Decisions\n" + "\n".join(f"- item {i}" for i in range(10))
            _write_memory(memory_file, content)
            result = utils.build_restore_context(memory_file, "reconnect")
            self.assertIsNotNone(result)
            self.assertIn("[Context Keeper]", result)
            self.assertIn("MEMORY.md exists", result)

    def test_returns_none_when_small_memory_no_active_work(self):
        """Returns None when MEMORY.md has <=5 lines and no Active Work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Decisions\n- one item\n")
            result = utils.build_restore_context(memory_file, "startup")
            self.assertIsNone(result)

    def test_returns_none_when_file_missing(self):
        """Returns None when MEMORY.md does not exist."""
        result = utils.build_restore_context("/does/not/exist/MEMORY.md", "startup")
        self.assertIsNone(result)

    def test_source_included_in_message(self):
        """Source parameter is included in the context message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = os.path.join(tmpdir, "MEMORY.md")
            _write_memory(memory_file, "# Memory\n\n## Active Work\n- task\n")
            result = utils.build_restore_context(memory_file, "project-manager-mcp")
            self.assertIn("project-manager-mcp", result)


if __name__ == '__main__':
    unittest.main()
