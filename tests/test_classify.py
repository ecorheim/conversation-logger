"""Tests for classify_user_entry, extract_full_content, extract_user_interaction."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

log_response_mod = import_script("log_response", "log-response.py")


# ---------------------------------------------------------------------------
# Tier 3.1: classify_user_entry
# ---------------------------------------------------------------------------
class TestClassifyUserEntry(unittest.TestCase):

    def test_prompt_string_content(self):
        entry = {"type": "user", "message": {"role": "user", "content": "Hello"}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "PROMPT")

    def test_user_answer(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "User has answered your questions: I prefer Python. You can now proceed."}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "USER_ANSWER")

    def test_plan_approval_approved(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "User has approved your plan with no feedback."}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "PLAN_APPROVAL")

    def test_plan_approval_exit_plan(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": "Exit plan mode? Yes"}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "PLAN_APPROVAL")

    def test_tool_rejection(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "The user doesn\u2019t want to proceed with the tool call."}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "TOOL_REJECTION")

    def test_interrupt(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": "[Request interrupted by user]"}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "INTERRUPT")

    def test_tool_result_string(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": "Some regular tool output"}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "TOOL_RESULT")

    def test_tool_result_list_content(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": [{"type": "text", "text": "output"}]}
        ]}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "TOOL_RESULT")

    def test_unknown_empty_content(self):
        entry = {"type": "user", "message": {"role": "user", "content": []}}
        self.assertEqual(log_response_mod.classify_user_entry(entry), "UNKNOWN")


# ---------------------------------------------------------------------------
# Tier 3.2: extract_full_content
# ---------------------------------------------------------------------------
class TestExtractFullContent(unittest.TestCase):

    def test_assistant_text(self):
        entry = {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "  Hello!  "}
        ]}}
        parts = log_response_mod.extract_full_content(entry)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], ("text", "Hello!"))

    def test_assistant_tool_use(self):
        entry = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/x"}}
        ]}}
        parts = log_response_mod.extract_full_content(entry)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0][0], "tool_use")
        self.assertEqual(parts[0][1]["name"], "Read")

    def test_tool_result_string(self):
        entry = {"type": "tool_result", "content": "  file content  "}
        parts = log_response_mod.extract_full_content(entry)
        self.assertEqual(parts, [("tool_result", "file content")])

    def test_tool_result_list(self):
        entry = {"type": "tool_result", "content": [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"}
        ]}
        parts = log_response_mod.extract_full_content(entry)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0][0], "tool_result")
        self.assertIn("Part 1", parts[0][1])
        self.assertIn("Part 2", parts[0][1])

    def test_unknown_entry_returns_empty(self):
        entry = {"type": "unknown"}
        self.assertEqual(log_response_mod.extract_full_content(entry), [])


# ---------------------------------------------------------------------------
# Tier 3.3: extract_user_interaction
# ---------------------------------------------------------------------------
class TestExtractUserInteraction(unittest.TestCase):

    def test_user_answer_extracts_text(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "User has answered your questions: I prefer Python. You can now proceed."}
        ]}}
        result = log_response_mod.extract_user_interaction(entry, "USER_ANSWER")
        self.assertEqual(result, "I prefer Python")

    def test_user_answer_without_you_can_now(self):
        """When '. You can now' is absent, return up to 300 chars from prefix end."""
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "User has answered your questions: I prefer Python"}
        ]}}
        result = log_response_mod.extract_user_interaction(entry, "USER_ANSWER")
        self.assertEqual(result, "I prefer Python")

    def test_tool_rejection_with_reason(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "The user doesn\u2019t want to proceed. the user said: I don't want that."}
        ]}}
        result = log_response_mod.extract_user_interaction(entry, "TOOL_REJECTION")
        self.assertEqual(result, "I don't want that.")

    def test_tool_rejection_no_reason(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "The user doesn\u2019t want to proceed with the tool call."}
        ]}}
        result = log_response_mod.extract_user_interaction(entry, "TOOL_REJECTION")
        self.assertEqual(result, "")

    def test_plan_approval_returns_marker(self):
        entry = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result",
             "content": "User has approved your plan with no feedback."}
        ]}}
        result = log_response_mod.extract_user_interaction(entry, "PLAN_APPROVAL")
        self.assertEqual(result, "(plan approved)")


if __name__ == '__main__':
    unittest.main()
