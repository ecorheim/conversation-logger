"""Tests for markdown format output — tool_rejection parsing (FINDING-2), helpers."""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

log_response_mod = import_script("log_response", "log-response.py")


# ---------------------------------------------------------------------------
# Tier 2.2: FINDING-2 — tool_rejection "user message:" nested parsing
# ---------------------------------------------------------------------------
class TestToolRejectionParsing(unittest.TestCase):

    def test_normal_rejection_extracts_reason(self):
        outputs = [("tool_rejection",
                     "  \u23bf  Tool use rejected with user message: I don't want that")]
        result = log_response_mod._format_output_markdown(outputs)
        self.assertEqual(len(result), 1)
        self.assertIn("I don't want that", result[0])

    def test_nested_user_message_in_reason(self):
        """FINDING-2: 'user message:' appears in the user's own text."""
        outputs = [("tool_rejection",
                     "  \u23bf  Tool use rejected with user message: check user message: test")]
        result = log_response_mod._format_output_markdown(outputs)
        self.assertEqual(len(result), 1)
        # Must extract full reason, not just the last split fragment
        self.assertIn("check user message: test", result[0])

    def test_rejection_without_user_message(self):
        outputs = [("tool_rejection", "  \u23bf  Tool use rejected")]
        result = log_response_mod._format_output_markdown(outputs)
        self.assertEqual(result, ["> **Tool Rejected**"])


# ---------------------------------------------------------------------------
# Tier 3.4: format_tool_input_md
# ---------------------------------------------------------------------------
class TestFormatToolInputMd(unittest.TestCase):

    def test_empty_input_heading_only(self):
        result = log_response_mod.format_tool_input_md("Read", {})
        self.assertIn("### \U0001f6e0\ufe0f Tool: `Read`", result)
        self.assertNotIn(">", result)

    def test_known_params_as_blockquote(self):
        result = log_response_mod.format_tool_input_md("Read", {"file_path": "/tmp/x.py"})
        self.assertIn("> file_path=/tmp/x.py", result)

    def test_newline_in_value_replaced(self):
        result = log_response_mod.format_tool_input_md("Edit", {"old_string": "line1\nline2"})
        self.assertIn("old_string=line1 line2", result)
        self.assertNotIn("\n>", result.split("\n", 1)[-1] if "\n" in result else "")

    def test_non_string_values_ignored(self):
        result = log_response_mod.format_tool_input_md("Custom", {"count": 42})
        self.assertNotIn(">", result)


# ---------------------------------------------------------------------------
# Tier 3.5: format_tool_result_md
# ---------------------------------------------------------------------------
class TestFormatToolResultMd(unittest.TestCase):

    def test_empty_content_returns_empty(self):
        self.assertEqual(log_response_mod.format_tool_result_md(""), "")

    def test_normal_text_triple_backtick(self):
        result = log_response_mod.format_tool_result_md("hello world")
        self.assertTrue(result.startswith("```"))
        self.assertIn("hello world", result)

    def test_backticks_in_content_dynamic_fence(self):
        content = "```python\nprint('hi')\n```"
        result = log_response_mod.format_tool_result_md(content)
        # Fence must be longer than the 3-backtick sequence in content
        fence = result.split("\n")[0]
        self.assertGreater(len(fence), 3)


# ---------------------------------------------------------------------------
# Tier 3.6: _format_output_markdown
# ---------------------------------------------------------------------------
class TestFormatOutputMarkdown(unittest.TestCase):

    def test_text_output_plain(self):
        result = log_response_mod._format_output_markdown([("text", "Hello!")])
        self.assertEqual(result, ["Hello!"])

    def test_tool_use_heading(self):
        tool_data = {"name": "Read", "input": {"file_path": "/tmp/x"}}
        result = log_response_mod._format_output_markdown([("tool_use", tool_data)])
        self.assertEqual(len(result), 1)
        self.assertIn("### \U0001f6e0\ufe0f Tool:", result[0])

    def test_interrupt(self):
        result = log_response_mod._format_output_markdown([("interrupt", "  \u23bf  Interrupted")])
        self.assertEqual(result, ["> **Interrupted**"])


# ---------------------------------------------------------------------------
# Tier 3.7: _write_followups_markdown
# ---------------------------------------------------------------------------
class TestWriteFollowupsMarkdown(unittest.TestCase):

    def test_answer_label(self):
        buf = io.StringIO()
        log_response_mod._write_followups_markdown(buf, [("answer", "My answer")])
        output = buf.getvalue()
        self.assertIn("## \U0001f4ac User", output)
        self.assertIn("> **Answer**", output)
        self.assertIn("My answer", output)

    def test_plan_approved_label(self):
        buf = io.StringIO()
        log_response_mod._write_followups_markdown(buf, [("plan approved", "(plan approved)")])
        output = buf.getvalue()
        self.assertIn("## \u2705 User", output)
        self.assertIn("> **Plan Approved**", output)

    def test_interrupt_label(self):
        buf = io.StringIO()
        log_response_mod._write_followups_markdown(buf, [("interrupt", "")])
        output = buf.getvalue()
        self.assertIn("## \u26a1 User", output)
        self.assertIn("> **Interrupted**", output)

    def test_other_label_uses_speech_bubble(self):
        buf = io.StringIO()
        log_response_mod._write_followups_markdown(buf, [("custom label", "details")])
        output = buf.getvalue()
        self.assertIn("## \U0001f4ac User", output)
        self.assertIn("> **custom label**", output)


if __name__ == '__main__':
    unittest.main()
