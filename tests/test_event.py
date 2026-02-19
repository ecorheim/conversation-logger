"""Tests for scripts/log-event.py — SessionStart event handling."""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from conftest import import_script

log_event_mod = import_script("log_event", "log-event.py")


class TestSessionStartCreatesConfig(unittest.TestCase):

    def _run_session_start(self, tmpdir, extra_input=None):
        """Invoke handle_session_start via log_event() with a SessionStart payload."""
        session_id = "test-session-001"
        input_data = {
            "hook_event_name": "SessionStart",
            "session_id": session_id,
            "cwd": tmpdir,
            "source": "user",
            "model": "claude-test",
        }
        if extra_input:
            input_data.update(extra_input)
        stdin_payload = json.dumps(input_data)
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = stdin_payload
            import io
            mock_stdin = io.StringIO(stdin_payload)
            with patch.object(sys, "stdin", mock_stdin):
                log_event_mod.log_event()
        return session_id

    def test_session_start_creates_config_when_none_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                self._run_session_start(tmpdir)
            project_config = os.path.join(tmpdir, ".claude", "conversation-logger-config.json")
            self.assertTrue(os.path.exists(project_config))

    def test_session_start_config_has_correct_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                self._run_session_start(tmpdir)
            project_config = os.path.join(tmpdir, ".claude", "conversation-logger-config.json")
            with open(project_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config["log_format"], "text")
            self.assertTrue(config["context_keeper"]["enabled"])
            self.assertEqual(config["context_keeper"]["scope"], "project")

    def test_session_start_writes_log_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                session_id = self._run_session_start(tmpdir)
            log_dir = os.path.join(tmpdir, ".claude", "logs")
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".txt") and not f.startswith(".")]
            self.assertEqual(len(log_files), 1)
            with open(os.path.join(log_dir, log_files[0]), 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("SESSION START", content)

    def test_session_start_does_not_overwrite_existing_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude")
            os.makedirs(claude_dir)
            project_config = os.path.join(claude_dir, "conversation-logger-config.json")
            with open(project_config, 'w', encoding='utf-8') as f:
                json.dump({"log_format": "markdown"}, f)
            with patch.dict(os.environ, {"HOME": tmpdir, "CONVERSATION_LOG_FORMAT": ""}):
                self._run_session_start(tmpdir)
            with open(project_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config["log_format"], "markdown")


if __name__ == '__main__':
    unittest.main()
