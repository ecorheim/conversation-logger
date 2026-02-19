"""Tests for scripts/log-event.py — session event logging."""
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

log_event_mod = import_script("log_event", "log-event.py")


def _run_event(tmpdir, event_payload, log_format="text"):
    """Simulate log_event with mocked stdin. Sets up markdown config if needed."""
    if log_format == "markdown":
        claude_dir = os.path.join(tmpdir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        with open(os.path.join(claude_dir, "conversation-logger-config.json"), 'w') as f:
            json.dump({"log_format": "markdown"}, f)

    mock_input = json.dumps(event_payload)
    with patch('sys.stdin', io.StringIO(mock_input)):
        with patch('sys.stderr', io.StringIO()):
            log_event_mod.log_event()


def _read_log(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        return f.read()


def _setup_session(tmpdir, session_id, log_format="text"):
    """Run SessionStart and return log file path."""
    _run_event(tmpdir, {
        "hook_event_name": "SessionStart",
        "session_id": session_id,
        "cwd": tmpdir,
        "source": "startup"
    }, log_format=log_format)
    log_dir = os.path.join(tmpdir, ".claude", "logs")
    return utils.read_temp_session(log_dir, session_id)["log_file_path"]


# ---------------------------------------------------------------------------
# SessionStart — text
# ---------------------------------------------------------------------------
class TestSessionStartText(unittest.TestCase):

    def test_writes_session_start_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-ss-1"
                _run_event(tmpdir, {
                    "hook_event_name": "SessionStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "source": "startup",
                    "model": "claude-sonnet-4-5"
                })
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                log_file = utils.read_temp_session(log_dir, session_id)["log_file_path"]
                content = _read_log(log_file)
                self.assertIn("~ SESSION START", content)
                self.assertIn("source=startup", content)
                self.assertIn("model=claude-sonnet-4-5", content)

    def test_creates_temp_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-ss-2"
                _run_event(tmpdir, {
                    "hook_event_name": "SessionStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "source": "startup"
                })
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                temp = utils.read_temp_session(log_dir, session_id)
                self.assertIsNotNone(temp)
                self.assertIn("log_file_path", temp)

    def test_missing_model_field(self):
        """model field is optional; line must not contain 'model=' when absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-ss-3"
                _run_event(tmpdir, {
                    "hook_event_name": "SessionStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "source": "reconnect"
                })
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                log_file = utils.read_temp_session(log_dir, session_id)["log_file_path"]
                content = _read_log(log_file)
                self.assertIn("~ SESSION START", content)
                self.assertNotIn("model=", content)


# ---------------------------------------------------------------------------
# SessionStart — markdown
# ---------------------------------------------------------------------------
class TestSessionStartMarkdown(unittest.TestCase):

    def test_writes_markdown_header_and_blockquote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-ssmd-1"
                _run_event(tmpdir, {
                    "hook_event_name": "SessionStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "source": "startup",
                    "model": "claude-sonnet-4-5"
                }, log_format="markdown")
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                log_file = utils.read_temp_session(log_dir, session_id)["log_file_path"]
                content = _read_log(log_file)
                self.assertIn("# Conversation Log", content)
                self.assertIn("> **Session Start**", content)
                self.assertIn("`startup`", content)
                self.assertIn("model: `claude-sonnet-4-5`", content)

    def test_does_not_duplicate_header(self):
        """Running SessionStart twice must not produce two markdown headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-ssmd-2"
                payload = {
                    "hook_event_name": "SessionStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "source": "startup"
                }
                _run_event(tmpdir, payload, log_format="markdown")
                _run_event(tmpdir, payload, log_format="markdown")
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                log_file = utils.read_temp_session(log_dir, session_id)["log_file_path"]
                content = _read_log(log_file)
                self.assertEqual(content.count("# Conversation Log"), 1)


# ---------------------------------------------------------------------------
# SessionEnd
# ---------------------------------------------------------------------------
class TestSessionEnd(unittest.TestCase):

    def test_writes_session_end_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-se-1"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "SessionEnd",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "reason": "prompt_input_exit"
                })
                content = _read_log(log_file)
                self.assertIn("~ SESSION END", content)
                self.assertIn("reason=prompt_input_exit", content)

    def test_cleans_up_temp_session_if_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-se-2"
                _setup_session(tmpdir, session_id)
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                self.assertIsNotNone(utils.read_temp_session(log_dir, session_id))

                _run_event(tmpdir, {
                    "hook_event_name": "SessionEnd",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "reason": "normal"
                })
                self.assertIsNone(utils.read_temp_session(log_dir, session_id))

    def test_graceful_when_temp_session_already_gone(self):
        """SessionEnd must not crash if Stop hook already deleted temp_session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-se-3"
                log_file = _setup_session(tmpdir, session_id)
                log_dir = os.path.join(tmpdir, ".claude", "logs")
                # Simulate Stop hook having already deleted temp_session
                os.remove(os.path.join(log_dir, f".temp_session_{session_id}.json"))

                _run_event(tmpdir, {
                    "hook_event_name": "SessionEnd",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "reason": "normal"
                })
                content = _read_log(log_file)
                self.assertIn("~ SESSION END", content)

    def test_session_end_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-semd-1"
                log_file = _setup_session(tmpdir, session_id, log_format="markdown")
                _run_event(tmpdir, {
                    "hook_event_name": "SessionEnd",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "reason": "prompt_input_exit"
                }, log_format="markdown")
                content = _read_log(log_file)
                self.assertIn("> **Session End**", content)
                self.assertIn("reason: `prompt_input_exit`", content)


# ---------------------------------------------------------------------------
# SubagentStart / SubagentStop
# ---------------------------------------------------------------------------
class TestSubagentEvents(unittest.TestCase):

    def test_subagent_start_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-sub-1"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "SubagentStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "subagent_type": "Explore",
                    "subagent_id": "agent-abc"
                })
                content = _read_log(log_file)
                self.assertIn("~ SUBAGENT START", content)
                self.assertIn("type=Explore", content)
                self.assertIn("id=agent-abc", content)

    def test_subagent_stop_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-sub-2"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "SubagentStop",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "subagent_type": "Bash",
                    "subagent_id": "agent-xyz"
                })
                content = _read_log(log_file)
                self.assertIn("~ SUBAGENT STOP", content)
                self.assertIn("type=Bash", content)
                self.assertIn("id=agent-xyz", content)

    def test_subagent_start_without_id(self):
        """subagent_id is optional; id= must not appear when absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-sub-3"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "SubagentStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "subagent_type": "Explore"
                })
                content = _read_log(log_file)
                self.assertIn("~ SUBAGENT START", content)
                self.assertNotIn("id=", content)

    def test_subagent_start_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-submd-1"
                log_file = _setup_session(tmpdir, session_id, log_format="markdown")
                _run_event(tmpdir, {
                    "hook_event_name": "SubagentStart",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "subagent_type": "Explore",
                    "subagent_id": "agent-abc"
                }, log_format="markdown")
                content = _read_log(log_file)
                self.assertIn("> **Subagent Start**", content)
                self.assertIn("type: `Explore`", content)
                self.assertIn("id: `agent-abc`", content)


# ---------------------------------------------------------------------------
# PreCompact
# ---------------------------------------------------------------------------
class TestPreCompact(unittest.TestCase):

    def test_compact_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-cmp-1"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "PreCompact",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "trigger": "auto"
                })
                content = _read_log(log_file)
                self.assertIn("~ COMPACT", content)
                self.assertIn("trigger=auto", content)

    def test_compact_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-cmpmd-1"
                log_file = _setup_session(tmpdir, session_id, log_format="markdown")
                _run_event(tmpdir, {
                    "hook_event_name": "PreCompact",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "trigger": "manual"
                }, log_format="markdown")
                content = _read_log(log_file)
                self.assertIn("> **Context Compacted**", content)
                self.assertIn("trigger: `manual`", content)


# ---------------------------------------------------------------------------
# PostToolUseFailure
# ---------------------------------------------------------------------------
class TestPostToolUseFailure(unittest.TestCase):

    def test_tool_failure_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-tf-1"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "PostToolUseFailure",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "tool_name": "Bash",
                    "error": "Command exited with non-zero status code 1"
                })
                content = _read_log(log_file)
                self.assertIn("~ TOOL FAILED", content)
                self.assertIn("tool=Bash", content)
                self.assertIn("Command exited with non-zero status code 1", content)

    def test_multiline_error_uses_first_line_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-tf-2"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "PostToolUseFailure",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "tool_name": "Bash",
                    "error": "First line error\nSecond line detail\nThird line"
                })
                content = _read_log(log_file)
                self.assertIn("First line error", content)
                self.assertNotIn("Second line detail", content)

    def test_long_error_truncated_to_200_chars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-tf-3"
                log_file = _setup_session(tmpdir, session_id)
                _run_event(tmpdir, {
                    "hook_event_name": "PostToolUseFailure",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "tool_name": "Bash",
                    "error": "E" * 300
                })
                content = _read_log(log_file)
                self.assertIn("E" * 200, content)
                self.assertNotIn("E" * 201, content)

    def test_tool_failure_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = "evt-tfmd-1"
                log_file = _setup_session(tmpdir, session_id, log_format="markdown")
                _run_event(tmpdir, {
                    "hook_event_name": "PostToolUseFailure",
                    "session_id": session_id,
                    "cwd": tmpdir,
                    "tool_name": "Bash",
                    "error": "Permission denied"
                }, log_format="markdown")
                content = _read_log(log_file)
                self.assertIn("> **Tool Failed**", content)
                self.assertIn("tool: `Bash`", content)
                self.assertIn("Permission denied", content)


# ---------------------------------------------------------------------------
# Unknown event
# ---------------------------------------------------------------------------
class TestUnknownEvent(unittest.TestCase):

    def test_unknown_event_exits_cleanly(self):
        """An unrecognized event name must not crash (exit 0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                try:
                    _run_event(tmpdir, {
                        "hook_event_name": "UnknownEvent",
                        "session_id": "evt-unk-1",
                        "cwd": tmpdir
                    })
                except SystemExit as e:
                    self.assertEqual(e.code, 0)


if __name__ == '__main__':
    unittest.main()
