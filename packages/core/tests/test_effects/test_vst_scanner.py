"""Tests for VST plugin scanner."""

import pytest


class TestVSTScanner:
    def test_scan_nonexistent_dir(self):
        from openmusic.effects.vst_scanner import scan_vst_directory

        results = scan_vst_directory("/nonexistent/path/that/does/not/exist")
        assert results == []

    def test_scan_empty_dir(self, tmp_path):
        from openmusic.effects.vst_scanner import scan_vst_directory

        results = scan_vst_directory(str(tmp_path))
        assert results == []

    def test_scan_finds_vst3_files(self, tmp_path):
        from openmusic.effects.vst_scanner import scan_vst_directory

        (tmp_path / "TestPlugin.vst3").touch()
        results = scan_vst_directory(str(tmp_path))
        assert len(results) == 1
        assert results[0].name == "TestPlugin"
        assert results[0].path.endswith("TestPlugin.vst3")
