"""Tier 1: E2E integration tests — critical path scenarios."""
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
from conftest import import_script

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import utils

log_prompt_mod = import_script("log_prompt", "log-prompt.py")
log_response_mod = import_script("log_response", "log-response.py")


def _create_transcript(path, entries):
    """Create a JSONL transcript file."""
    with open(path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')


def _run_prompt(tmpdir, session_id, prompt_text):
    """Simulate log_prompt with mocked stdin/stderr."""
    mock_input = json.dumps({
        "prompt": prompt_text,
        "session_id": session_id,
        "cwd": tmpdir,
    })
    with patch('sys.stdin', io.StringIO(mock_input)):
        with patch('sys.stderr', io.StringIO()):
            log_prompt_mod.log_prompt()


def _run_response(tmpdir, session_id, transcript_path):
    """Simulate log_response with mocked stdin/stdout/stderr."""
    mock_input = json.dumps({
        "transcript_path": transcript_path,
        "session_id": session_id,
        "cwd": tmpdir,
    })
    with patch('sys.stdin', io.StringIO(mock_input)):
        with patch('sys.stdout', io.StringIO()):
            with patch('sys.stderr', io.StringIO()):
                log_response_mod.log_response()


SIMPLE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "Hello Claude"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "Hi there! How can I help you?"}
    ]}},
]

TOOL_USE_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "Read my file"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "Let me read that file."},
        {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/test.py"}},
    ]}},
    {"type": "tool_result", "content": "print('hello')"},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "The file contains a print statement."},
    ]}},
]


# ---------------------------------------------------------------------------
# 1.1: Text default without config
# ---------------------------------------------------------------------------
class TestTextDefaultWithoutConfig(unittest.TestCase):

    def test_text_format_produces_txt_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                _run_prompt(tmpdir, "sess-1", "Hello Claude")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                txt_files = [f for f in os.listdir(log_dir)
                             if f.endswith('.txt') and not f.startswith('.')]
                self.assertEqual(len(txt_files), 1)

                # Check temp_session
                temp = utils.read_temp_session(log_dir, "sess-1")
                self.assertIsNotNone(temp)
                self.assertEqual(temp["log_format"], "text")
                self.assertIn("log_file_path", temp)

                # Check log content
                with open(temp["log_file_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn("Hello Claude", content)
                self.assertIn("=" * 80, content)
                self.assertIn("-" * 80, content)


# ---------------------------------------------------------------------------
# 1.2: Markdown E2E
# ---------------------------------------------------------------------------
class TestMarkdownE2E(unittest.TestCase):

    def test_markdown_produces_md_file_with_full_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up project config
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir, exist_ok=True)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                _run_prompt(tmpdir, "sess-md", "Hello Claude")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                temp = utils.read_temp_session(log_dir, "sess-md")
                log_path = temp["log_file_path"]

                self.assertTrue(log_path.endswith(".md"))

                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn("# Conversation Log", content)
                self.assertIn("## \U0001f464 User", content)

                # Run response with tool use transcript
                transcript_path = os.path.join(tmpdir, "transcript.jsonl")
                _create_transcript(transcript_path, TOOL_USE_TRANSCRIPT)
                _run_response(tmpdir, "sess-md", transcript_path)

                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn("## \U0001f916 Claude", content)
                self.assertIn("### \U0001f6e0\ufe0f Tool:", content)


# ---------------------------------------------------------------------------
# 1.3: Config priority chain
# ---------------------------------------------------------------------------
class TestConfigPriority(unittest.TestCase):

    def test_priority_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = os.path.join(tmpdir, "home")
            project_dir = os.path.join(tmpdir, "project")

            # User config: text
            user_claude = os.path.join(home_dir, ".claude")
            os.makedirs(user_claude)
            with open(os.path.join(user_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "text"}, f)

            # Project config: markdown
            proj_claude = os.path.join(project_dir, ".claude")
            os.makedirs(proj_claude)
            with open(os.path.join(proj_claude, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            # project(md) > user(text)
            with patch.dict(os.environ, {"HOME": home_dir, "CONVERSATION_LOG_FORMAT": ""}):
                fmt = utils.get_log_format(project_dir)
                self.assertEqual(fmt, "markdown")

            # ENV(text) > project(md)
            with patch.dict(os.environ, {"HOME": home_dir, "CONVERSATION_LOG_FORMAT": "text"}):
                fmt = utils.get_log_format(project_dir)
                self.assertEqual(fmt, "text")

            # No config at all → text default
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                fmt = utils.get_log_format(tmpdir)
                self.assertEqual(fmt, "text")


# ---------------------------------------------------------------------------
# 1.4: Prompt-response file consistency
# ---------------------------------------------------------------------------
class TestPromptResponseConsistency(unittest.TestCase):

    def test_prompt_and_response_in_same_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                _run_prompt(tmpdir, "sess-c", "Test prompt")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                temp = utils.read_temp_session(log_dir, "sess-c")
                prompt_log_path = temp["log_file_path"]

                transcript_path = os.path.join(tmpdir, "transcript.jsonl")
                _create_transcript(transcript_path, SIMPLE_TRANSCRIPT)
                _run_response(tmpdir, "sess-c", transcript_path)

                # Both prompt and response in the same file
                with open(prompt_log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn("Test prompt", content)
                self.assertIn("Hi there!", content)


# ---------------------------------------------------------------------------
# 1.5: Bad config fallback
# ---------------------------------------------------------------------------
class TestBadConfigFallback(unittest.TestCase):

    def test_invalid_json_falls_back_to_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                f.write("{bad json}")

            stderr_buf = io.StringIO()
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                with patch('sys.stderr', stderr_buf):
                    _run_prompt(tmpdir, "sess-bad", "Hello")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                txt_files = [f for f in os.listdir(log_dir)
                             if f.endswith('.txt') and not f.startswith('.')]
                self.assertTrue(len(txt_files) >= 1)

    def test_invalid_format_value_falls_back_to_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "yaml"}, f)

            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                with patch('sys.stderr', io.StringIO()):
                    _run_prompt(tmpdir, "sess-inv", "Hello")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                txt_files = [f for f in os.listdir(log_dir)
                             if f.endswith('.txt') and not f.startswith('.')]
                self.assertTrue(len(txt_files) >= 1)


# ---------------------------------------------------------------------------
# 1.6: Markdown second prompt — no header duplication
# ---------------------------------------------------------------------------
class TestMarkdownSecondPrompt(unittest.TestCase):

    def test_second_prompt_no_header_duplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
                json.dump({"log_format": "markdown"}, f)

            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                # First prompt
                _run_prompt(tmpdir, "sess-2p", "First question")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                temp = utils.read_temp_session(log_dir, "sess-2p")
                log_path = temp["log_file_path"]

                # Simulate response so temp_session is consumed
                transcript_path = os.path.join(tmpdir, "transcript.jsonl")
                _create_transcript(transcript_path, SIMPLE_TRANSCRIPT)
                _run_response(tmpdir, "sess-2p", transcript_path)

                # Second prompt — same session, same file
                _run_prompt(tmpdir, "sess-2p", "Second question")

                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Header appears exactly once
                self.assertEqual(content.count("# Conversation Log"), 1)
                # Both prompts present
                self.assertIn("First question", content)
                self.assertIn("Second question", content)
                # Separator present
                self.assertIn("---", content)


# ---------------------------------------------------------------------------
# FINDING-1 integration: CLAUDE response header emoji in text format
# ---------------------------------------------------------------------------
class TestCLAUDEHeaderEmoji(unittest.TestCase):

    def test_claude_response_header_has_emoji(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                _run_prompt(tmpdir, "sess-em", "Hello")

                log_dir = os.path.join(tmpdir, ".claude", "logs")
                temp = utils.read_temp_session(log_dir, "sess-em")
                log_path = temp["log_file_path"]

                transcript_path = os.path.join(tmpdir, "transcript.jsonl")
                _create_transcript(transcript_path, SIMPLE_TRANSCRIPT)
                _run_response(tmpdir, "sess-em", transcript_path)

                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn("\U0001f916 CLAUDE", content)


if __name__ == '__main__':
    unittest.main()
