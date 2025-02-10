import pytest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
import sys
import os

# Set Qt to use minimal platform plugin to avoid opening windows during tests
os.environ['QT_QPA_PLATFORM'] = 'minimal'

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def mock_file_operations():
    """Mock file operations to avoid actual file I/O during tests."""
    with patch('builtins.open', create=True) as mock_open:
        # Mock empty data files
        mock_open.return_value.__enter__.return_value.read.return_value = '{}'
        yield mock_open
