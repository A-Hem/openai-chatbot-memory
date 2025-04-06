"""
conftest.py - pytest configuration and shared fixtures
"""

import os
import pytest
import tempfile
import time

@pytest.fixture(scope="session", autouse=True)
def session_setup():
    """Setup and teardown for the entire test session."""
    # Setup code - ensure required dirs exist, etc.
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"  # Suppress HF symlink warnings
    
    # Make sure temp dir for tests exists
    os.makedirs("tests/tmp", exist_ok=True)
    
    # Return for test session
    yield
    
    # Teardown code - cleanup temp files
    try:
        for root, dirs, files in os.walk("tests/tmp", topdown=False):
            for name in files:
                try:
                    os.unlink(os.path.join(root, name))
                except OSError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
    except Exception:
        pass

@pytest.fixture
def temp_file():
    """Create a temporary file."""
    fd, path = tempfile.mkstemp(suffix='.tmp', dir="tests/tmp")
    yield path
    os.close(fd)
    try:
        os.unlink(path)
    except OSError:
        pass

@pytest.fixture
def sqlite_db():
    """Create a temporary SQLite database file."""
    fd, path = tempfile.mkstemp(suffix='.db', dir="tests/tmp")
    yield path
    os.close(fd)
    try:
        os.unlink(path)
    except OSError:
        pass 