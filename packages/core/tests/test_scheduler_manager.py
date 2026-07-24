"""Tests for the scheduling manager (crontab management)."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from openmusic.scheduler.cron import CronParseError
from openmusic.scheduler.manager import (
    ScheduleJob,
    ScheduleJobStatus,
    ScheduleManager,
)


@pytest.fixture
def sample_job_data():
    return {
        "job_id": "abc123",
        "name": "test-job",
        "cron_expression": "0 2 * * 5",
        "command": "openmusic generate --length 2h",
        "status": "active",
        "description": "Weekly mix generation",
        "created_at": "2026-07-18T12:00:00",
        "updated_at": "2026-07-18T12:00:00",
        "notifier_config": None,
        "notification_config": None,
    }


class TestScheduleJob:
    def test_to_dict(self, sample_job_data):
        job = ScheduleJob.from_dict(sample_job_data)
        d = job.to_dict()
        assert d["name"] == "test-job"
        assert d["status"] == "active"

    def test_from_dict(self, sample_job_data):
        job = ScheduleJob.from_dict(sample_job_data)
        assert job.name == "test-job"
        assert job.status == ScheduleJobStatus.ACTIVE
        assert job.cron_expression == "0 2 * * 5"

    def test_from_dict_disabled(self, sample_job_data):
        data = dict(sample_job_data, status="disabled")
        job = ScheduleJob.from_dict(data)
        assert job.status == ScheduleJobStatus.DISABLED

    def test_parsed_cron(self, sample_job_data):
        job = ScheduleJob.from_dict(sample_job_data)
        cron = job.parsed_cron
        assert str(cron) == "0 2 * * 5"


@patch("openmusic.scheduler.manager._load_schedules", side_effect=lambda: {})
@patch("openmusic.scheduler.manager._save_schedules")
@patch("openmusic.scheduler.manager._get_current_crontab", return_value="")
@patch("openmusic.scheduler.manager._set_crontab", return_value=True)
class TestScheduleManager:
    def test_add_job(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        job = manager.add("0 2 * * 5", "openmusic generate --length 2h", name="weekly-mix")
        assert job.name == "weekly-mix"
        assert job.cron_expression == "0 2 * * 5"
        assert job.job_id is not None
        mock_save.assert_called_once()

    def test_add_job_invalid_cron(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        with pytest.raises(CronParseError):
            manager.add("invalid", "some command")

    def test_add_job_auto_name(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        job = manager.add("0 0 * * *", "echo hello")
        assert job.name.startswith("job-")

    def test_list_jobs_empty(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        jobs = manager.list_jobs()
        assert jobs == []

    def test_remove_job(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        manager.add("0 2 * * 5", "openmusic generate", name="test-remove")
        result = manager.remove("test-remove")
        assert result is True
        jobs = manager.list_jobs()
        assert len(jobs) == 0

    def test_remove_nonexistent(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        result = manager.remove("nonexistent")
        assert result is False

    def test_get_job_by_name(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        added = manager.add("0 2 * * 5", "openmusic generate", name="find-me")
        job = manager.get_job("find-me")
        assert job is not None
        assert job.job_id == added.job_id

    def test_get_job_by_id(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        added = manager.add("0 2 * * 5", "openmusic generate", name="by-id")
        job = manager.get_job(added.job_id)
        assert job is not None
        assert job.name == "by-id"

    def test_get_job_nonexistent(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        job = manager.get_job("nope")
        assert job is None

    def test_disable_job(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        added = manager.add("0 2 * * 5", "openmusic generate", name="to-disable")
        assert manager.disable("to-disable") is True
        job = manager.get_job("to-disable")
        assert job is not None
        assert job.status == ScheduleJobStatus.DISABLED

    def test_enable_job(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        added = manager.add("0 2 * * 5", "openmusic generate", name="to-enable")
        manager.disable("to-enable")
        assert manager.enable("to-enable") is True
        job = manager.get_job("to-enable")
        assert job is not None
        assert job.status == ScheduleJobStatus.ACTIVE


@patch("openmusic.scheduler.manager._load_schedules", side_effect=lambda: {})
@patch("openmusic.scheduler.manager._save_schedules")
@patch("openmusic.scheduler.manager._get_current_crontab", return_value="")
@patch("openmusic.scheduler.manager._set_crontab", return_value=True)
class TestScheduleManagerRunNow:
    def test_run_now_success(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        manager.add("0 2 * * 5", "echo hello", name="quick-job")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="hello\n", stderr=""
            )
            result = manager.run_now("quick-job")
            assert result["success"] is True
            assert "hello" in result["output"]

    def test_run_now_failure(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        manager.add("0 2 * * 5", "false", name="fail-job")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="error"
            )
            result = manager.run_now("fail-job")
            assert result["success"] is False

    def test_run_now_nonexistent(self, mock_set, mock_get, mock_save, mock_load):
        manager = ScheduleManager()
        result = manager.run_now("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]


class TestCrontabSync:
    def test_sync_removes_old_and_adds_new(self, tmp_path):
        mock_crontab_content = (
            "# some other entry\n"
            "0 5 * * * /usr/bin/backup\n"
            "# openmusic-schedule: old123 old-job\n"
            "0 3 * * * /tmp/old.sh\n"
        )
        with patch("openmusic.scheduler.manager._get_current_crontab", return_value=mock_crontab_content):
            with patch("openmusic.scheduler.manager._set_crontab") as mock_set:
                mock_set.return_value = True

                manager = ScheduleManager()
                manager.add(
                    "0 2 * * 5",
                    "openmusic generate --length 2h",
                    name="new-weekly-mix",
                )

                assert mock_set.called
                call_args = mock_set.call_args[0][0]
                assert "openmusic-schedule" in call_args
                assert "new-weekly-mix" in call_args or "openmusic generate" in call_args
                assert "old-job" not in call_args
                assert "/usr/bin/backup" in call_args
