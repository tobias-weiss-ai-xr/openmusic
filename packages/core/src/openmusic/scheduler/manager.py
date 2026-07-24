"""Job management for cron-based scheduling.

Manages scheduled jobs in the system crontab, with persistent job
metadata stored in ~/.config/openmusic/schedules.json.
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from openmusic.notification import NotificationConfig as GenericNotificationConfig
from openmusic.notification import NotificationEvent as GenericNotificationEvent
from openmusic.notification import Notifier as GenericNotifier
from openmusic.scheduler.cron import CronExpression, validate_cron
from openmusic.scheduler.notifier import NotifierConfig, NotificationEvent, notify

logger = logging.getLogger(__name__)

# Marker comment prefix for identifying our crontab entries
_CRON_MARKER = "# openmusic-schedule:"
_CONFIG_DIR = Path.home() / ".config" / "openmusic"
_CONFIG_PATH = _CONFIG_DIR / "schedules.json"
_SCRIPTS_DIR = _CONFIG_DIR / "scripts"


class ScheduleJobStatus(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    REMOVED = "removed"


@dataclass
class ScheduleJob:
    """A scheduled job definition."""

    name: str
    cron_expression: str
    command: str
    status: ScheduleJobStatus = ScheduleJobStatus.ACTIVE
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    notifier_config: Optional[Dict[str, Any]] = None
    notification_config: Optional[Dict[str, Any]] = None

    @property
    def parsed_cron(self) -> CronExpression:
        return validate_cron(self.cron_expression)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScheduleJob:
        data = data.copy()
        data["status"] = ScheduleJobStatus(data.get("status", "active"))
        return cls(**data)


def _load_schedules() -> Dict[str, Dict[str, Any]]:
    """Load all registered schedules from the config file."""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load schedules: {e}")
        return {}


def _save_schedules(schedules: Dict[str, Dict[str, Any]]) -> None:
    """Save all registered schedules to the config file."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(schedules, f, indent=2)
    logger.info(f"Saved {len(schedules)} schedules to {_CONFIG_PATH}")


def _get_current_crontab() -> str:
    """Get the current user crontab content. Returns empty string if no crontab."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
        return ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def _set_crontab(content: str) -> bool:
    """Set the user crontab to the given content."""
    try:
        proc = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(input=content.encode(), timeout=10)
        if proc.returncode != 0:
            logger.error(f"Failed to set crontab: {stderr.decode()}")
            return False
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to set crontab: {e}")
        return False


def _generate_wrapper_script(job: ScheduleJob) -> str:
    """Generate a shell wrapper script path for the job command."""
    _SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    script_path = _SCRIPTS_DIR / f"{job.job_id}.sh"

    shell = os.environ.get("SHELL", "/bin/bash")

    script_content = "#!/usr/bin/env bash\n"
    script_content += f"# OpenMusic scheduled job: {job.name}\n"
    script_content += f"# Command: {job.command}\n"
    script_content += f"set -e\n"
    script_content += f"cd {shlex.quote(str(Path.cwd()))}\n"
    script_content += f"exec {job.command}\n"

    script_path.write_text(script_content)
    script_path.chmod(0o755)

    return str(script_path)


def _build_crontab_entry(job: ScheduleJob) -> str:
    """Build a crontab line for the given job."""
    cron = job.parsed_cron
    script_path = _generate_wrapper_script(job)
    line = cron.to_crontab_line(
        command=script_path,
        comment=f"{_CRON_MARKER} {job.job_id} {job.name}",
    )
    return line


class ScheduleManager:
    """Manages scheduled jobs via the system crontab.

    Usage:
        manager = ScheduleManager()
        job = manager.add("0 2 * * 5", "openmusic generate --length 2h", name="weekly-mix")
        manager.list_jobs()
        manager.remove("weekly-mix")
    """

    def __init__(self) -> None:
        self._schedules = _load_schedules()

    def add(
        self,
        cron_expression: str,
        command: str,
        name: Optional[str] = None,
        description: str = "",
        notifier_config: Optional[NotifierConfig] = None,
        notification_config: Optional[GenericNotificationConfig] = None,
    ) -> ScheduleJob:
        """Register a new scheduled job and add it to the system crontab.

        Args:
            cron_expression: Standard 5-field cron expression (e.g., "0 2 * * 5").
            command: Shell command to execute.
            name: Human-readable name for the job (auto-generated if omitted).
            description: Optional description of the job.
            notifier_config: Optional Telegram/Discord notification config.
            notification_config: Optional webhook/email notification config.

        Returns:
            The created ScheduleJob.

        Raises:
            CronParseError: If the cron expression is invalid.
        """
        validate_cron(cron_expression)

        if not name:
            name = f"job-{uuid.uuid4().hex[:8]}"

        job = ScheduleJob(
            name=name,
            cron_expression=cron_expression,
            command=command,
            description=description,
            notifier_config=asdict(notifier_config) if notifier_config else None,
            notification_config=asdict(notification_config) if notification_config else None,
        )

        self._schedules[job.job_id] = job.to_dict()
        _save_schedules(self._schedules)
        self._sync_crontab()

        logger.info(f"Added scheduled job '{name}': {cron_expression} → {command}")
        return job

    def remove(self, job_id_or_name: str) -> bool:
        """Remove a scheduled job by its ID or name.

        Args:
            job_id_or_name: Job ID or name to remove.

        Returns:
            True if the job was found and removed.
        """
        job_id = self._resolve_id(job_id_or_name)
        if not job_id:
            logger.warning(f"Job '{job_id_or_name}' not found")
            return False

        script_path = _SCRIPTS_DIR / f"{job_id}.sh"
        if script_path.exists():
            script_path.unlink()

        self._schedules.pop(job_id, None)
        _save_schedules(self._schedules)
        self._sync_crontab()

        logger.info(f"Removed scheduled job '{job_id_or_name}'")
        return True

    def list_jobs(self) -> List[ScheduleJob]:
        """List all registered scheduled jobs."""
        return [
            ScheduleJob.from_dict(data)
            for data in self._schedules.values()
        ]

    def get_job(self, job_id_or_name: str) -> Optional[ScheduleJob]:
        """Get a specific job by ID or name."""
        job_id = self._resolve_id(job_id_or_name)
        if not job_id:
            return None
        data = self._schedules.get(job_id)
        if data is None:
            return None
        return ScheduleJob.from_dict(data)

    def disable(self, job_id_or_name: str) -> bool:
        """Disable a scheduled job without removing it."""
        job_id = self._resolve_id(job_id_or_name)
        if not job_id:
            return False
        job_data = self._schedules.get(job_id)
        if job_data is None:
            return False
        job_data["status"] = "disabled"
        job_data["updated_at"] = datetime.now().isoformat()
        _save_schedules(self._schedules)
        self._sync_crontab()
        logger.info(f"Disabled scheduled job '{job_id_or_name}'")
        return True

    def enable(self, job_id_or_name: str) -> bool:
        """Enable a previously disabled scheduled job."""
        job_id = self._resolve_id(job_id_or_name)
        if not job_id:
            return False
        job_data = self._schedules.get(job_id)
        if job_data is None:
            return False
        job_data["status"] = "active"
        job_data["updated_at"] = datetime.now().isoformat()
        _save_schedules(self._schedules)
        self._sync_crontab()
        logger.info(f"Enabled scheduled job '{job_id_or_name}'")
        return True

    def run_now(self, job_id_or_name: str) -> Dict[str, Any]:
        """Execute a scheduled job immediately (bypasses cron).

        Args:
            job_id_or_name: Job ID or name to run.

        Returns:
            Dict with keys: success, output, error.
        """
        job = self.get_job(job_id_or_name)
        if not job:
            return {"success": False, "output": "", "error": f"Job '{job_id_or_name}' not found"}

        logger.info(f"Running job '{job.name}' immediately: {job.command}")
        result: Dict[str, Any] = {"success": False, "output": "", "error": ""}

        try:
            proc = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=7200,
            )
            result["output"] = proc.stdout
            result["error"] = proc.stderr
            result["success"] = proc.returncode == 0

            if proc.returncode == 0:
                logger.info(f"Job '{job.name}' completed successfully")
            else:
                logger.warning(f"Job '{job.name}' failed with exit code {proc.returncode}")

        except subprocess.TimeoutExpired:
            result["error"] = "Job timed out after 2 hours"
            logger.warning(f"Job '{job.name}' timed out")

        if job.notifier_config:
            nc = NotifierConfig(**job.notifier_config)
            event = (
                NotificationEvent.ON_SUCCESS
                if result["success"]
                else NotificationEvent.ON_FAILURE
            )
            notify(
                config=nc,
                event=event,
                job_name=job.name,
                command=job.command,
                output=result.get("output"),
                error=result.get("error"),
            )

        if job.notification_config:
            gnc = GenericNotificationConfig(**job.notification_config)
            if gnc.is_configured:
                notifier = GenericNotifier(gnc)
                notifier.notify(GenericNotificationEvent(
                    status="success" if result["success"] else "failure",
                    title=job.name,
                    error_message=result.get("error") if not result["success"] else None,
                    duration_seconds=None,
                    metadata={
                        "command": job.command,
                        "cron_expression": job.cron_expression,
                        "output": result.get("output", ""),
                    },
                ))

        return result

    def _resolve_id(self, job_id_or_name: str) -> Optional[str]:
        """Resolve a job ID or name to a job ID."""
        if job_id_or_name in self._schedules:
            return job_id_or_name
        for jid, data in self._schedules.items():
            if data.get("name") == job_id_or_name:
                return jid
        return None

    def _sync_crontab(self) -> bool:
        """Synchronize the system crontab with our registered jobs.

        Removes all entries marked with our marker, then re-adds
        entries for all active jobs.
        """
        current = _get_current_crontab()
        lines = current.splitlines()

        filtered_lines = [
            line
            for line in lines
            if _CRON_MARKER not in line
        ]

        for job_data in self._schedules.values():
            job = ScheduleJob.from_dict(job_data)
            if job.status == ScheduleJobStatus.ACTIVE:
                filtered_lines.append(_build_crontab_entry(job))

        new_content = "\n".join(filtered_lines)
        if new_content.strip() and not new_content.endswith("\n"):
            new_content += "\n"

        return _set_crontab(new_content)
