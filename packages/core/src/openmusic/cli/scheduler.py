"""CLI commands for managing scheduled jobs."""
import json
import sys
from pathlib import Path

import click

from openmusic.scheduler.cron import CronParseError
from openmusic.scheduler.manager import ScheduleManager
from openmusic.scheduler.notifier import NotifierConfig


@click.group(help="Manage cron-scheduled mix generation jobs.")
def schedule():
    pass


@schedule.command("add")
@click.option(
    "--cron",
    required=True,
    help="Cron expression (e.g. '0 2 * * 5' for Fridays at 2am, or '@daily')",
)
@click.option(
    "--command",
    required=True,
    help="OpenMusic command to run (e.g. 'openmusic generate --length 2h')",
)
@click.option("--name", default=None, help="Human-readable name for this job")
@click.option("--description", default="", help="Optional job description")
@click.option(
    "--telegram-token",
    default=None,
    help="Telegram bot token for notifications",
)
@click.option(
    "--telegram-chat",
    default=None,
    help="Telegram chat ID for notifications",
)
@click.option(
    "--discord-webhook",
    default=None,
    help="Discord webhook URL for notifications",
)
@click.option(
    "--notify-on",
    default="success,failure",
    help="Events to notify on: start,success,failure (comma-separated, default: success,failure)",
)
def schedule_add(
    cron: str,
    command: str,
    name: str | None,
    description: str,
    telegram_token: str | None,
    telegram_chat: str | None,
    discord_webhook: str | None,
    notify_on: str,
):
    """Add a new scheduled job to the system crontab."""
    manager = ScheduleManager()

    notifier_config = None
    if telegram_token or discord_webhook:
        from openmusic.scheduler.notifier import NotificationEvent

        event_map = {
            "start": NotificationEvent.ON_START,
            "success": NotificationEvent.ON_SUCCESS,
            "failure": NotificationEvent.ON_FAILURE,
        }
        notify_events = set()
        for name in notify_on.split(","):
            name = name.strip().lower()
            if name in event_map:
                notify_events.add(event_map[name])
            else:
                click.echo(f"Warning: Unknown notification event '{name}'", err=True)

        notifier_config = NotifierConfig(
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat,
            discord_webhook_url=discord_webhook,
            notify_on=notify_events,
        )

    try:
        job = manager.add(
            cron_expression=cron,
            command=command,
            name=name,
            description=description,
            notifier_config=notifier_config,
        )
    except CronParseError as e:
        click.echo(f"Error: Invalid cron expression: {e}", err=True)
        sys.exit(1)

    click.echo(f"Added scheduled job:")
    click.echo(f"  Name:     {job.name}")
    click.echo(f"  ID:       {job.job_id}")
    click.echo(f"  Cron:     {job.cron_expression}")
    click.echo(f"  Command:  {job.command}")
    if notifier_config and notifier_config.is_configured:
        click.echo(f"  Notifications: enabled")


@schedule.command("remove")
@click.argument("job_id_or_name")
def schedule_remove(job_id_or_name: str):
    """Remove a scheduled job by its ID or name."""
    manager = ScheduleManager()
    if manager.remove(job_id_or_name):
        click.echo(f"Removed scheduled job: {job_id_or_name}")
    else:
        click.echo(f"Error: Job '{job_id_or_name}' not found", err=True)
        sys.exit(1)


@schedule.command("list")
def schedule_list():
    """List all scheduled jobs."""
    manager = ScheduleManager()
    jobs = manager.list_jobs()

    if not jobs:
        click.echo("No scheduled jobs found.")
        return

    click.echo(f"Scheduled jobs ({len(jobs)}):")
    click.echo("")
    for job in jobs:
        status_icon = "✓" if job.status.value == "active" else "✗"
        click.echo(f"  {status_icon} {job.name} ({job.job_id})")
        click.echo(f"     Cron: {job.cron_expression}")
        click.echo(f"     Cmd:  {job.command}")
        if job.description:
            click.echo(f"     Desc: {job.description}")
        click.echo("")


@schedule.command("run")
@click.argument("job_id_or_name")
def schedule_run(job_id_or_name: str):
    """Execute a scheduled job immediately (bypasses cron)."""
    manager = ScheduleManager()
    result = manager.run_now(job_id_or_name)

    if result["output"]:
        click.echo(result["output"])

    if result["error"]:
        click.echo(result["error"], err=True)

    if result["success"]:
        click.echo(f"Job completed successfully.")
    else:
        click.echo(f"Job failed.", err=True)
        sys.exit(1)


@schedule.command("enable")
@click.argument("job_id_or_name")
def schedule_enable(job_id_or_name: str):
    """Enable a disabled scheduled job."""
    manager = ScheduleManager()
    if manager.enable(job_id_or_name):
        click.echo(f"Enabled scheduled job: {job_id_or_name}")
    else:
        click.echo(f"Error: Job '{job_id_or_name}' not found", err=True)
        sys.exit(1)


@schedule.command("disable")
@click.argument("job_id_or_name")
def schedule_disable(job_id_or_name: str):
    """Disable a scheduled job without removing it."""
    manager = ScheduleManager()
    if manager.disable(job_id_or_name):
        click.echo(f"Disabled scheduled job: {job_id_or_name}")
    else:
        click.echo(f"Error: Job '{job_id_or_name}' not found", err=True)
        sys.exit(1)
