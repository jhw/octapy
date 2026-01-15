"""
Pytest fixtures for octapy tests.
"""

import tempfile
from pathlib import Path

import pytest

from octapy import BankFile, MarkersFile, ProjectFile, extract_template


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
