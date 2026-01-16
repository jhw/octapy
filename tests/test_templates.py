"""
Tests for template and project zip utilities.
"""

import pytest

from octapy._io import (
    BankFile,
    MarkersFile,
    extract_template,
    read_template_file,
    zip_project,
    unzip_project,
)


class TestTemplateExtraction:
    """Template extraction tests."""

    def test_extract_template(self, temp_dir):
        """Test extracting template creates all files."""
        project_dir = temp_dir / "TEST_PROJECT"
        extract_template(project_dir)

        # Check essential files exist
        assert (project_dir / "project.work").exists()
        assert (project_dir / "markers.work").exists()
        assert (project_dir / "bank01.work").exists()
        assert (project_dir / "bank16.work").exists()
        assert (project_dir / "arr01.work").exists()

    def test_extract_template_file_count(self, temp_dir):
        """Test extracted template has correct number of files."""
        project_dir = temp_dir / "TEST_PROJECT"
        extract_template(project_dir)

        files = list(project_dir.glob("*.work"))
        # 16 banks + 8 arrangements + 1 project + 1 markers = 26
        assert len(files) == 26

    def test_read_template_file_bank(self):
        """Test reading a bank file from template."""
        data = read_template_file("bank01.work")

        assert data is not None
        assert len(data) > 0

        # Verify it's valid bank data
        bank = BankFile.read(data)
        assert bank.check_header() is True

    def test_read_template_file_markers(self):
        """Test reading markers file from template."""
        data = read_template_file("markers.work")

        assert data is not None

        # Verify it's valid markers data
        markers = MarkersFile.read(data)
        assert markers.check_header() is True


class TestBankFileNew:
    """BankFile.new() tests."""

    def test_new_creates_valid_bank(self):
        """Test BankFile.new() creates valid bank."""
        bank = BankFile.new()

        assert bank.check_header() is True
        assert bank.check_version() is True

    def test_new_bank_numbers(self):
        """Test BankFile.new() with different bank numbers."""
        for bank_num in [1, 8, 16]:
            bank = BankFile.new(bank_num=bank_num)
            assert bank.check_header() is True


class TestMarkersFileNew:
    """MarkersFile.new() tests."""

    def test_new_creates_valid_markers(self):
        """Test MarkersFile.new() creates valid markers."""
        markers = MarkersFile.new()

        assert markers.check_header() is True
        assert markers.check_version() is True


class TestProjectZip:
    """Project zip/unzip tests."""

    def test_zip_project(self, template_project, temp_dir):
        """Test zipping a project."""
        zip_path = temp_dir / "test.zip"
        zip_project(template_project, zip_path)

        assert zip_path.exists()
        assert zip_path.stat().st_size > 0

    def test_unzip_project(self, template_project, temp_dir):
        """Test unzipping a project."""
        # First zip
        zip_path = temp_dir / "test.zip"
        zip_project(template_project, zip_path)

        # Then unzip to new location
        unzip_dir = temp_dir / "unzipped"
        unzip_project(zip_path, unzip_dir)

        # Verify files exist
        assert (unzip_dir / "project.work").exists()
        assert (unzip_dir / "bank01.work").exists()
        assert (unzip_dir / "markers.work").exists()

    def test_zip_unzip_roundtrip(self, template_project, temp_dir):
        """Test that zip/unzip preserves file contents."""
        # Read original bank
        original_bank = BankFile.from_file(template_project / "bank01.work")

        # Zip
        zip_path = temp_dir / "test.zip"
        zip_project(template_project, zip_path)

        # Unzip
        unzip_dir = temp_dir / "unzipped"
        unzip_project(zip_path, unzip_dir)

        # Read unzipped bank
        loaded_bank = BankFile.from_file(unzip_dir / "bank01.work")

        # Compare
        assert loaded_bank._data == original_bank._data

    def test_zip_only_work_files(self, template_project, temp_dir):
        """Test that zip only includes .work files."""
        # Create a non-.work file
        (template_project / "extra.txt").write_text("test")

        # Zip
        zip_path = temp_dir / "test.zip"
        zip_project(template_project, zip_path)

        # Unzip and check
        unzip_dir = temp_dir / "unzipped"
        unzip_project(zip_path, unzip_dir)

        # extra.txt should not be in the zip
        assert not (unzip_dir / "extra.txt").exists()
