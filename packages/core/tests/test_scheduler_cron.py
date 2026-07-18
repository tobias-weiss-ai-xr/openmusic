"""Tests for cron expression parsing and validation."""
import pytest
from openmusic.scheduler.cron import (
    CronExpression,
    CronParseError,
    validate_cron,
)


class TestValidateCron:
    def test_simple_expression(self):
        cron = validate_cron("0 2 * * 5")
        assert cron.minute == "0"
        assert cron.hour == "2"
        assert cron.day_of_month == "*"
        assert cron.month == "*"
        assert cron.day_of_week == "5"

    def test_wildcard_expression(self):
        cron = validate_cron("* * * * *")
        assert all(
            getattr(cron, f) == "*"
            for f in ["minute", "hour", "day_of_month", "month", "day_of_week"]
        )

    def test_daily_alias(self):
        cron = validate_cron("@daily")
        assert str(cron) == "0 0 * * *"

    def test_hourly_alias(self):
        cron = validate_cron("@hourly")
        assert str(cron) == "0 * * * *"

    def test_weekly_alias(self):
        cron = validate_cron("@weekly")
        assert str(cron) == "0 0 * * 0"

    def test_monthly_alias(self):
        cron = validate_cron("@monthly")
        assert str(cron) == "0 0 1 * *"

    def test_yearly_alias(self):
        cron = validate_cron("@yearly")
        assert str(cron) == "0 0 1 1 *"

    def test_annually_alias(self):
        cron = validate_cron("@annually")
        assert str(cron) == "0 0 1 1 *"

    def test_midnight_alias(self):
        cron = validate_cron("@midnight")
        assert str(cron) == "0 0 * * *"

    def test_step_values(self):
        cron = validate_cron("*/5 * * * *")
        assert cron.minute == "*/5"

    def test_range_values(self):
        cron = validate_cron("0 9-17 * * *")
        assert cron.hour == "9-17"

    def test_list_values(self):
        cron = validate_cron("0 0 * * 1,3,5")
        assert cron.day_of_week == "1,3,5"

    def test_to_crontab_line(self):
        cron = validate_cron("0 2 * * 5")
        line = cron.to_crontab_line("/usr/bin/true", comment="my job")
        assert "/usr/bin/true" in line
        assert "# my job" in line

    def test_unknown_alias(self):
        with pytest.raises(CronParseError, match="Unknown cron alias"):
            validate_cron("@unknown")

    def test_wrong_number_of_fields(self):
        with pytest.raises(CronParseError, match="exactly 5 fields"):
            validate_cron("0 2 * *")

    def test_extra_fields(self):
        with pytest.raises(CronParseError, match="exactly 5 fields"):
            validate_cron("0 2 * * 5 extra")

    def test_invalid_minute(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("60 * * * *")

    def test_invalid_hour(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("* 24 * * *")

    def test_invalid_day_of_month(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("* * 0 * *")

    def test_invalid_day_of_month_high(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("* * 32 * *")

    def test_invalid_month(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("* * * 13 *")

    def test_invalid_day_of_week(self):
        with pytest.raises(CronParseError, match="out of range"):
            validate_cron("* * * * 8")

    def test_nonedigit_field(self):
        with pytest.raises(CronParseError, match="Invalid cron field"):
            validate_cron("abc * * * *")

    def test_step_with_zero(self):
        with pytest.raises(CronParseError, match="Step value must be >= 1"):
            validate_cron("*/0 * * * *")

    def test_expression_str(self):
        cron = validate_cron("30 4 * * 1-5")
        assert str(cron) == "30 4 * * 1-5"


class TestCronExpression:
    def test_frozen_dataclass(self):
        cron = validate_cron("0 0 * * *")
        with pytest.raises(Exception):
            cron.minute = "1"
