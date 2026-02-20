"""Tests for scripts/utils.py — config, fence, temp session, cleanup, debug."""
import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import utils


# ---------------------------------------------------------------------------
# Tier 2.3: calculate_fence edge cases
# ---------------------------------------------------------------------------
class TestCalculateFence(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(utils.calculate_fence(""), "```")

    def test_no_backticks(self):
        self.assertEqual(utils.calculate_fence("hello world"), "```")

    def test_three_consecutive_backticks(self):
        self.assertEqual(utils.calculate_fence("```code```"), "````")

    def test_four_consecutive_backticks(self):
        self.assertEqual(utils.calculate_fence("````code````"), "`````")

    def test_five_consecutive_backticks(self):
        self.assertEqual(utils.calculate_fence("`````"), "``````")

    def test_ten_consecutive_backticks(self):
        self.assertEqual(utils.calculate_fence("``````````"), "```````````")

    def test_scattered_non_consecutive_backticks(self):
        self.assertEqual(utils.calculate_fence("` `` `"), "```")

    def test_nested_markdown_code_blocks(self):
        content = "Some text\n```python\ncode\n```\nMore text"
        self.assertEqual(utils.calculate_fence(content), "````")


# ---------------------------------------------------------------------------
# Tier 2.4: load_config with HOME isolation
# ---------------------------------------------------------------------------
class TestLoadConfig(unittest.TestCase):

    def test_env_overrides_project_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            with patch.dict(os.environ, {"CONVERSATION_LOG_FORMAT": "text"}):
                config = utils.load_config(tmpdir)
                self.assertEqual(config["log_format"], "text")

    def test_project_config_over_user_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = os.path.join(tmpdir, "home")
            project_dir = os.path.join(tmpdir, "project")

            user_claude = os.path.join(home_dir, ".claude")
            os.makedirs(user_claude)
            with open(os.path.join(user_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "text"}, f)

            proj_claude = os.path.join(project_dir, ".claude")
            os.makedirs(proj_claude)
            with open(os.path.join(proj_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            with patch.dict(os.environ, {"HOME": home_dir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(project_dir)
                self.assertEqual(config["log_format"], "markdown")

    def test_user_config_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = os.path.join(tmpdir, "home")
            project_dir = os.path.join(tmpdir, "project")
            os.makedirs(project_dir)

            user_claude = os.path.join(home_dir, ".claude")
            os.makedirs(user_claude)
            with open(os.path.join(user_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            with patch.dict(os.environ, {"HOME": home_dir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(project_dir)
                self.assertEqual(config["log_format"], "markdown")

    def test_no_config_returns_text_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(tmpdir)
                self.assertEqual(config["log_format"], "text")

    def test_home_isolation_prevents_real_config(self):
        """HOME mocked to tempdir — real user config must not influence result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(tmpdir)
                self.assertEqual(config["log_format"], "text")

    def test_invalid_json_falls_back_to_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                f.write("{invalid json}")

            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(tmpdir)
                self.assertEqual(config["log_format"], "text")

    def test_invalid_format_value_falls_back_to_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "yaml"}, f)

            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                config = utils.load_config(tmpdir)
                self.assertEqual(config["log_format"], "text")


# ---------------------------------------------------------------------------
# Tier 3.8: temp_session I/O
# ---------------------------------------------------------------------------
class TestTempSession(unittest.TestCase):

    def test_write_read_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {"session_id": "abc", "log_format": "text", "log_file_path": "/tmp/t.txt"}
            utils.write_temp_session("abc", data, temp_dir=tmpdir)
            result = utils.read_temp_session("abc", temp_dir=tmpdir)
            self.assertEqual(result, data)

    def test_nonexistent_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(utils.read_temp_session("nonexistent", temp_dir=tmpdir))

    def test_corrupted_json_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, ".temp_session_bad.json")
            with open(path, 'w') as f:
                f.write("{corrupted")
            self.assertIsNone(utils.read_temp_session("bad", temp_dir=tmpdir))


# ---------------------------------------------------------------------------
# Tier 3.9: cleanup_stale_temp_files
# ---------------------------------------------------------------------------
class TestCleanupStaleTempFiles(unittest.TestCase):

    def test_fresh_file_kept(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fresh = os.path.join(tmpdir, ".temp_session_fresh.json")
            with open(fresh, 'w') as f:
                f.write('{}')
            utils.cleanup_stale_temp_files(temp_dir=tmpdir)
            self.assertTrue(os.path.exists(fresh))

    def test_stale_file_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stale = os.path.join(tmpdir, ".temp_session_stale.json")
            with open(stale, 'w') as f:
                f.write('{}')
            old_time = time.time() - 7200
            os.utime(stale, (old_time, old_time))
            utils.cleanup_stale_temp_files(temp_dir=tmpdir)
            self.assertFalse(os.path.exists(stale))


# ---------------------------------------------------------------------------
# Tier 3.10: debug_log
# ---------------------------------------------------------------------------
class TestDebugLog(unittest.TestCase):

    def test_debug_disabled_no_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            utils.debug_log(tmpdir, "test message")
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "debug-response.log")))

    def test_debug_enabled_writes_timestamped_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(utils, 'DEBUG', True):
                utils.debug_log(tmpdir, "test message")
            path = os.path.join(tmpdir, "debug-response.log")
            self.assertTrue(os.path.exists(path))
            with open(path, 'r') as f:
                content = f.read()
            self.assertIn("test message", content)
            self.assertRegex(content, r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]')


# ---------------------------------------------------------------------------
# get_log_file_path
# ---------------------------------------------------------------------------
class TestGetLogFilePath(unittest.TestCase):

    def test_filename_includes_time_component(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = utils.get_log_file_path(tmpdir, "abc123", "text")
            filename = os.path.basename(path)
            # Must match YYYY-MM-DD_HH-MM-SS_session_conversation-log.ext
            import re
            self.assertRegex(filename, r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_')

    def test_txt_extension_for_text_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = utils.get_log_file_path(tmpdir, "abc123", "text")
            self.assertTrue(path.endswith(".txt"))

    def test_md_extension_for_markdown_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = utils.get_log_file_path(tmpdir, "abc123", "markdown")
            self.assertTrue(path.endswith(".md"))


# ---------------------------------------------------------------------------
# resolve_log_path
# ---------------------------------------------------------------------------
class TestResolveLogPath(unittest.TestCase):

    def test_returns_temp_session_path_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                log_dir = utils.get_log_dir(tmpdir)
                expected_path = os.path.join(tmpdir, "custom-log.txt")
                utils.write_temp_session("sid-1", {
                    "log_file_path": expected_path,
                    "log_format": "markdown"
                })
                log_file, log_format, returned_log_dir = utils.resolve_log_path(tmpdir, "sid-1")
                self.assertEqual(log_file, expected_path)
                self.assertEqual(log_format, "markdown")
                self.assertEqual(returned_log_dir, log_dir)

    def test_falls_back_to_config_when_no_temp_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                log_file, log_format, log_dir = utils.resolve_log_path(tmpdir, "sid-2")
                self.assertEqual(log_format, "text")
                self.assertTrue(log_file.endswith(".txt"))
                self.assertIn("sid-2", log_file)

    def test_temp_session_without_log_file_path_falls_back(self):
        """temp_session missing log_file_path key must fall back to config chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                utils.write_temp_session("sid-3", {"log_format": "markdown"})
                log_file, log_format, _ = utils.resolve_log_path(tmpdir, "sid-3")
                self.assertEqual(log_format, "text")
                self.assertTrue(log_file.endswith(".txt"))


# ---------------------------------------------------------------------------
# ensure_markdown_header
# ---------------------------------------------------------------------------
class TestEnsureMarkdownHeader(unittest.TestCase):

    def test_writes_header_to_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.md")
            with open(log_file, 'a', encoding='utf-8') as f:
                utils.ensure_markdown_header(f, log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("# Conversation Log", content)

    def test_does_not_write_header_when_file_has_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.md")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("# Existing content\n")
            with open(log_file, 'a', encoding='utf-8') as f:
                utils.ensure_markdown_header(f, log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content.count("# "), 1)
            self.assertNotIn("# Conversation Log", content)


# ---------------------------------------------------------------------------
# ensure_config
# ---------------------------------------------------------------------------
class TestEnsureConfig(unittest.TestCase):

    def test_creates_default_config_when_none_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                utils.ensure_config(tmpdir)
            project_config = os.path.join(tmpdir, ".claude", "conversation-logger-config.json")
            self.assertTrue(os.path.exists(project_config))

    def test_default_values_correct(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                utils.ensure_config(tmpdir)
            project_config = os.path.join(tmpdir, ".claude", "conversation-logger-config.json")
            with open(project_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config["log_format"], "text")
            self.assertTrue(config["context_keeper"]["enabled"])
            self.assertEqual(config["context_keeper"]["scope"], "project")

    def test_skips_when_project_config_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            project_config = os.path.join(claude_dir, "conversation-logger-config.json")
            with open(project_config, 'w', encoding='utf-8') as f:
                json.dump({"log_format": "markdown"}, f)
            with patch.dict(os.environ, {"HOME": tmpdir}):
                utils.ensure_config(tmpdir)
            with open(project_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config["log_format"], "markdown")

    def test_skips_when_user_config_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = os.path.join(tmpdir, "home")
            project_dir = os.path.join(tmpdir, "project")
            os.makedirs(project_dir)
            user_claude = os.path.join(home_dir, ".claude")
            os.makedirs(user_claude)
            with open(os.path.join(user_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)
            with patch.dict(os.environ, {"HOME": home_dir}):
                utils.ensure_config(project_dir)
            project_config = os.path.join(project_dir, ".claude", "conversation-logger-config.json")
            self.assertFalse(os.path.exists(project_config))

    def test_creates_claude_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir}):
                utils.ensure_config(tmpdir)
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, ".claude")))


# ---------------------------------------------------------------------------
# extract_recent_prompts
# ---------------------------------------------------------------------------
class TestExtractRecentPrompts(unittest.TestCase):

    def _text_log(self, prompts):
        """Build text-format log content from list of (timestamp, text) tuples."""
        content = ""
        for ts, text in prompts:
            content += f"\n{'='*80}\n"
            ts_part = f" ({ts})" if ts else ""
            content += f"\U0001f464 USER{ts_part}:\n{text}\n"
            content += f"{'-'*80}\n"
        return content

    def _md_log(self, prompts):
        """Build markdown-format log content from list of (timestamp, text) tuples."""
        content = "# Conversation Log\n"
        for ts, text in prompts:
            content += f"\n---\n\n## \U0001f464 User \u2014 {ts}\n\n{text}\n"
        return content

    def test_text_single_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._text_log([("10:00:00", "Fix the login button")]))
            result = utils.extract_recent_prompts(path, "text")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "10:00:00")
            self.assertIn("Fix the login button", result[0][1])

    def test_text_legacy_no_timestamp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._text_log([("", "Old prompt without timestamp")]))
            result = utils.extract_recent_prompts(path, "text")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "")
            self.assertIn("Old prompt without timestamp", result[0][1])

    def test_markdown_single_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.md")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._md_log([("14:30:00", "Update the tests")]))
                f.write("\n---\n")
            result = utils.extract_recent_prompts(path, "markdown")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "14:30:00")
            self.assertIn("Update the tests", result[0][1])

    def test_nonexistent_file_returns_empty(self):
        result = utils.extract_recent_prompts("/nonexistent/path.txt", "text")
        self.assertEqual(result, [])

    def test_empty_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.txt")
            open(path, 'w').close()
            result = utils.extract_recent_prompts(path, "text")
            self.assertEqual(result, [])

    def test_truncation_at_max_length(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._text_log([("09:00:00", "A" * 300)]))
            result = utils.extract_recent_prompts(path, "text", max_length=200)
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0][1].endswith("..."))
            self.assertEqual(len(result[0][1]), 203)  # 200 + len("...")

    def test_max_prompts_returns_last_n(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log.txt")
            prompts = [(f"0{i}:00:00", f"Prompt {i}") for i in range(5)]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._text_log(prompts))
            result = utils.extract_recent_prompts(path, "text", max_prompts=2)
            self.assertEqual(len(result), 2)
            self.assertIn("Prompt 3", result[0][1])
            self.assertIn("Prompt 4", result[1][1])


# ---------------------------------------------------------------------------
# write_compaction_marker with recent_prompts
# ---------------------------------------------------------------------------
class TestWriteCompactionMarkerWithPrompts(unittest.TestCase):

    def _make_memory(self, tmpdir, content):
        path = os.path.join(tmpdir, "MEMORY.md")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_recent_prompts_written_to_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_memory(tmpdir, "# Memory\n\n## Active Work\n\n")
            recent_prompts = [("10:05", "Fix the login button"), ("10:08", "Update the tests")]
            utils.write_compaction_marker(path, "auto", [], recent_prompts)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("[Auto-saved context] Recent user requests before compaction:", content)
            self.assertIn("[10:05] Fix the login button", content)
            self.assertIn("[10:08] Update the tests", content)

    def test_no_recent_prompts_skips_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_memory(tmpdir, "# Memory\n\n## Active Work\n\n")
            utils.write_compaction_marker(path, "auto", [], None)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertNotIn("Recent user requests", content)

    def test_modified_files_use_new_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_memory(tmpdir, "# Memory\n\n## Active Work\n\n")
            utils.write_compaction_marker(path, "auto", ["scripts/utils.py"], None)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("[Auto-saved context] Files modified in previous context:", content)
            self.assertIn("scripts/utils.py", content)

    def test_both_prompts_and_files_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_memory(tmpdir, "# Memory\n\n## Active Work\n\n")
            recent_prompts = [("15:00", "Some request")]
            utils.write_compaction_marker(path, "manual", ["a.py", "b.py"], recent_prompts)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("[Auto-saved context] Recent user requests before compaction:", content)
            self.assertIn("[Auto-saved context] Files modified in previous context:", content)
            self.assertLess(
                content.index("Recent user requests"),
                content.index("Files modified")
            )

    def test_empty_timestamp_no_bracket_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_memory(tmpdir, "# Memory\n\n## Active Work\n\n")
            recent_prompts = [("", "Legacy prompt without timestamp")]
            utils.write_compaction_marker(path, "auto", [], recent_prompts)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("Legacy prompt without timestamp", content)
            self.assertNotIn("[] Legacy", content)


if __name__ == '__main__':
    unittest.main()