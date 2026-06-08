"""Tests for cli.stream module."""

from click.testing import CliRunner

from openmusic.cli.stream import stream


class TestStreamCommandGroup:
    def test_start_requires_audio(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["start"])
        assert result.exit_code != 0
        assert "audio" in result.output.lower() or "Error" in result.output


class TestStreamStartCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["start", "--help"])
        assert result.exit_code == 0
        assert "--audio" in result.output
        assert "--platform" in result.output

    def test_nonexistent_audio_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            stream, ["start", "--audio", "/nonexistent/file.wav", "--stream-key", "test"]
        )
        assert result.exit_code != 0

    def test_unsupported_platform_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            stream,
            [
                "start",
                "--audio",
                "/tmp/test.wav",
                "--platform",
                "nonexistent",
                "--stream-key",
                "test",
            ],
        )
        assert result.exit_code != 0


class TestStreamStopCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["stop", "--help"])
        assert result.exit_code == 0


class TestStreamStatusCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["status", "--help"])
        assert result.exit_code == 0
