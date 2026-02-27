"""Tests for text format output — emoji presence (FINDING-1), tool formatting."""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

log_prompt_mod = import_script("log_prompt", "log-prompt.py")
log_response_mod = import_script("log_response", "log-response.py")


# ---------------------------------------------------------------------------
# Tier 2.1: FINDING-1 — emoji must be present in text format
# ---------------------------------------------------------------------------
class TestTextEmojiPresence(unittest.TestCase):
    """v0.1.3 had emoji; v0.2.0 must restore them."""

    def test_write_prompt_text_has_user_emoji(self):
        buf = io.StringIO()
        log_prompt_mod._write_prompt_text(buf, "Hello", "12:00:00")
        self.assertIn("\U0001f464 USER", buf.getvalue())

    def test_write_followups_text_has_user_emoji(self):
        buf = io.StringIO()
        log_response_mod._write_followups_text(buf, [("answer", "My answer")])
        self.assertIn("\U0001f464 USER", buf.getvalue())

    def test_write_followups_text_without_text_has_user_emoji(self):
        buf = io.StringIO()
        log_response_mod._write_followups_text(buf, [("interrupt", "")])
        self.assertIn("\U0001f464 USER", buf.getvalue())


# ---------------------------------------------------------------------------
# Tier 2.5 / 3: format_tool_input — no truncation
# ---------------------------------------------------------------------------
class TestFormatToolInput(unittest.TestCase):

    def test_empty_input(self):
        result = log_response_mod.format_tool_input("Read", {})
        self.assertIn("Read()", result)

    def test_with_known_params(self):
        result = log_response_mod.format_tool_input("Read", {"file_path": "/tmp/x.py"})
        self.assertIn("file_path=/tmp/x.py", result)

    def test_long_value_not_truncated(self):
        long_path = "/very/long/" + "a" * 200
        result = log_response_mod.format_tool_input("Read", {"file_path": long_path})
        self.assertIn(long_path, result)

    def test_unknown_params_ellipsis(self):
        result = log_response_mod.format_tool_input("Custom", {"unknown_key": "val"})
        self.assertIn("...", result)

    def test_old_string_param(self):
        result = log_response_mod.format_tool_input("Edit", {"old_string": "foo"})
        self.assertIn("old_string=foo", result)

    def test_url_param(self):
        result = log_response_mod.format_tool_input("WebFetch", {"url": "https://example.com"})
        self.assertIn("url=https://example.com", result)


# ---------------------------------------------------------------------------
# Tier 2.5 / 3: format_tool_result — no truncation
# ---------------------------------------------------------------------------
class TestFormatToolResult(unittest.TestCase):

    def test_empty_content(self):
        result = log_response_mod.format_tool_result("")
        self.assertIn("(no output)", result)

    def test_single_line(self):
        result = log_response_mod.format_tool_result("hello")
        self.assertIn("hello", result)

    def test_multiline_full_output(self):
        lines = "\n".join([f"line {i}" for i in range(50)])
        result = log_response_mod.format_tool_result(lines)
        self.assertIn("line 0", result)
        self.assertIn("line 49", result)

    def test_none_content(self):
        result = log_response_mod.format_tool_result(None)
        self.assertIn("(no output)", result)


# ---------------------------------------------------------------------------
# extract_full_content
# ---------------------------------------------------------------------------
class TestExtractFullContent(unittest.TestCase):

    def test_empty_tool_result_passes_through(self):
        """Empty string tool results must not be filtered out during extraction."""
        entry = {"type": "tool_result", "content": ""}
        parts = log_response_mod.extract_full_content(entry)
        self.assertEqual(parts, [("tool_result", "")])


# ---------------------------------------------------------------------------
# Tier 3: _write_prompt_text structural checks
# ---------------------------------------------------------------------------
class TestWritePromptTextStructure(unittest.TestCase):

    def test_contains_separator_lines(self):
        buf = io.StringIO()
        log_prompt_mod._write_prompt_text(buf, "Hi", "12:00:00")
        output = buf.getvalue()
        self.assertIn("=" * 80, output)
        self.assertIn("-" * 80, output)

    def test_no_session_id_in_body(self):
        """Session ID is already in the filename; it should not appear in log body."""
        buf = io.StringIO()
        log_prompt_mod._write_prompt_text(buf, "Hi", "12:00:00")
        self.assertNotIn("Session:", buf.getvalue())

    def test_timestamp_in_user_line(self):
        """Timestamp should be merged into the USER header line."""
        buf = io.StringIO()
        log_prompt_mod._write_prompt_text(buf, "Hi", "14:30:45")
        self.assertIn("\U0001f464 USER (14:30:45):", buf.getvalue())

    def test_contains_prompt_content(self):
        buf = io.StringIO()
        log_prompt_mod._write_prompt_text(buf, "What is Python?", "12:00:00")
        self.assertIn("What is Python?", buf.getvalue())


if __name__ == '__main__':
    unittest.main()