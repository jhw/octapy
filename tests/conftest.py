"""
Pytest fixtures for octapy tests.
"""

import tempfile
from pathlib import Path

import pytest

# Import from internal modules for testing
from octapy._io import BankFile, MarkersFile, ProjectFile, extract_template


def pytest_addoption(parser):
    """Add --slow option to run slow tests."""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests (roundtrips, etc.)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --slow is passed."""
    if config.getoption("--slow"):
        return
    skip_slow = pytest.mark.skip(reason="use --slow to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def template_project(temp_dir):
    """Extract a template project to a temp directory."""
    project_dir = temp_dir / "TEST_PROJECT"
    extract_template(project_dir)
    return project_dir


@pytest.fixture
def bank_file():
    """Create a new BankFile from template."""
    return BankFile.new()


@pytest.fixture
def markers_file():
    """Create a new MarkersFile from template."""
    return MarkersFile.new()


@pytest.fixture
def project_file():
    """Create a new ProjectFile with defaults."""
    return ProjectFile()
