"""Shared test utilities for conversation-logger test suite."""
import importlib.util
import os
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


def import_script(name, filename):
    """Import script with hyphenated filename using importlib."""
    path = os.path.join(SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = os.path.abspath(path)
    spec.loader.exec_module(mod)
    return mod
