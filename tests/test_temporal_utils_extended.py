"""
Tests for py3plex.temporal_utils_extended module.

This module tests extended temporal utilities including:
- Duration string parsing
- Duration formatting
"""

import pytest
from py3plex.temporal_utils_extended import parse_duration_string, format_duration


class TestParseDurationString:
    """Test parse_duration_string function."""
    
    def test_parse_numeric_int(self):
        """Test parsing numeric integer."""
        result = parse_duration_string(100)
        assert result == 100.0
        assert isinstance(result, float)
    
    def test_parse_numeric_float(self):
        """Test parsing numeric float."""
        result = parse_duration_string(42.5)
        assert result == 42.5
        assert isinstance(result, float)
    
    def test_parse_weeks_short(self):
        """Test parsing weeks (short form)."""
        assert parse_duration_string("1w") == 7 * 24 * 3600
        assert parse_duration_string("2w") == 2 * 7 * 24 * 3600
    
    def test_parse_weeks_long(self):
        """Test parsing weeks (long forms)."""
        assert parse_duration_string("1week") == 7 * 24 * 3600
        assert parse_duration_string("2weeks") == 2 * 7 * 24 * 3600
    
    def test_parse_days_short(self):
        """Test parsing days (short form)."""
        assert parse_duration_string("1d") == 24 * 3600
        assert parse_duration_string("7d") == 7 * 24 * 3600
    
    def test_parse_days_long(self):
        """Test parsing days (long forms)."""
        assert parse_duration_string("1day") == 24 * 3600
        assert parse_duration_string("2days") == 2 * 24 * 3600
    
    def test_parse_hours_short(self):
        """Test parsing hours (short form)."""
        assert parse_duration_string("1h") == 3600
        assert parse_duration_string("24h") == 24 * 3600
    
    def test_parse_hours_variants(self):
        """Test parsing hours (all variants)."""
        assert parse_duration_string("1hour") == 3600
        assert parse_duration_string("2hours") == 2 * 3600
        assert parse_duration_string("3hr") == 3 * 3600
        assert parse_duration_string("4hrs") == 4 * 3600
    
    def test_parse_minutes_short(self):
        """Test parsing minutes (short form)."""
        assert parse_duration_string("1m") == 60
        assert parse_duration_string("30m") == 30 * 60
    
    def test_parse_minutes_variants(self):
        """Test parsing minutes (all variants)."""
        assert parse_duration_string("1min") == 60
        assert parse_duration_string("2minute") == 2 * 60
        assert parse_duration_string("3minutes") == 3 * 60
        assert parse_duration_string("5mins") == 5 * 60
    
    def test_parse_seconds_short(self):
        """Test parsing seconds (short form)."""
        assert parse_duration_string("1s") == 1
        assert parse_duration_string("60s") == 60
    
    def test_parse_seconds_variants(self):
        """Test parsing seconds (all variants)."""
        assert parse_duration_string("1sec") == 1
        assert parse_duration_string("2second") == 2
        assert parse_duration_string("3seconds") == 3
        assert parse_duration_string("10secs") == 10
    
    def test_parse_with_whitespace(self):
        """Test parsing with leading/trailing whitespace."""
        assert parse_duration_string("  7d  ") == 7 * 24 * 3600
        assert parse_duration_string("24h ") == 24 * 3600
        assert parse_duration_string(" 30m") == 30 * 60
    
    def test_parse_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        assert parse_duration_string("7D") == 7 * 24 * 3600
        assert parse_duration_string("24H") == 24 * 3600
        assert parse_duration_string("30M") == 30 * 60
        assert parse_duration_string("WEEK") == 7 * 24 * 3600
    
    def test_parse_decimal_values(self):
        """Test parsing decimal values."""
        assert parse_duration_string("1.5h") == 1.5 * 3600
        assert parse_duration_string("2.5d") == 2.5 * 24 * 3600
        assert parse_duration_string("0.5m") == 30
    
    def test_parse_invalid_format_no_unit(self):
        """Test error on invalid format (no unit)."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration_string("100")
    
    def test_parse_invalid_format_no_number(self):
        """Test error on invalid format (no number)."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration_string("days")
    
    def test_parse_invalid_unit(self):
        """Test error on unknown time unit."""
        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_duration_string("5x")
    
    def test_parse_negative_not_supported(self):
        """Test that negative durations are not supported in string format."""
        # Note: The function doesn't explicitly handle negative strings
        # This would fail at the regex match
        with pytest.raises(ValueError):
            parse_duration_string("-5d")
    
    def test_parse_empty_string(self):
        """Test error on empty string."""
        with pytest.raises(ValueError):
            parse_duration_string("")
    
    def test_parse_zero(self):
        """Test parsing zero."""
        assert parse_duration_string(0) == 0.0
        assert parse_duration_string(0.0) == 0.0


class TestFormatDuration:
    """Test format_duration function."""
    
    def test_format_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0s"
    
    def test_format_seconds(self):
        """Test formatting seconds only."""
        assert format_duration(1) == "1s"
        assert format_duration(59) == "59s"
    
    def test_format_minutes(self):
        """Test formatting minutes."""
        assert format_duration(60) == "1m"
        assert format_duration(120) == "2m"
        assert format_duration(90) == "1m 30s"
    
    def test_format_hours(self):
        """Test formatting hours."""
        assert format_duration(3600) == "1h"
        assert format_duration(7200) == "2h"
        assert format_duration(3661) == "1h 1m"
    
    def test_format_days(self):
        """Test formatting days."""
        assert format_duration(24 * 3600) == "1d"
        assert format_duration(2 * 24 * 3600) == "2d"
        assert format_duration(24 * 3600 + 3600) == "1d 1h"
    
    def test_format_weeks(self):
        """Test formatting weeks."""
        assert format_duration(7 * 24 * 3600) == "1w"
        assert format_duration(2 * 7 * 24 * 3600) == "2w"
        assert format_duration(7 * 24 * 3600 + 24 * 3600) == "1w 1d"
    
    def test_format_precision_default(self):
        """Test default precision (2 units)."""
        # 1 week + 1 day + 1 hour + 1 minute + 1 second
        duration = 7 * 24 * 3600 + 24 * 3600 + 3600 + 60 + 1
        result = format_duration(duration)
        assert result == "1w 1d"  # Only top 2 units
    
    def test_format_precision_one(self):
        """Test precision=1 (single unit)."""
        duration = 7 * 24 * 3600 + 24 * 3600 + 3600
        result = format_duration(duration, precision=1)
        assert result == "1w"
    
    def test_format_precision_three(self):
        """Test precision=3 (three units)."""
        duration = 24 * 3600 + 3600 + 60 + 1
        result = format_duration(duration, precision=3)
        assert result == "1d 1h 1m"
    
    def test_format_precision_high(self):
        """Test high precision shows all units."""
        duration = 7 * 24 * 3600 + 24 * 3600 + 3600 + 60 + 1
        result = format_duration(duration, precision=10)
        assert result == "1w 1d 1h 1m 1s"
    
    def test_format_sub_second(self):
        """Test formatting durations less than 1 second."""
        result = format_duration(0.5)
        assert "0.500s" in result
    
    def test_format_sub_second_very_small(self):
        """Test formatting very small durations."""
        result = format_duration(0.001)
        assert "0.001s" in result
    
    def test_format_negative(self):
        """Test formatting negative durations."""
        result = format_duration(-3600)
        assert result.startswith("-")
        assert "1h" in result
    
    def test_format_negative_complex(self):
        """Test formatting complex negative durations."""
        duration = -(24 * 3600 + 3600)
        result = format_duration(duration)
        assert result.startswith("-")
        assert "1d" in result
        assert "1h" in result
    
    def test_format_large_value(self):
        """Test formatting large values."""
        # 10 weeks
        duration = 10 * 7 * 24 * 3600
        result = format_duration(duration)
        assert result == "10w"
    
    def test_format_roundtrip(self):
        """Test that parse and format are somewhat inverse operations."""
        # Not exact inverse, but should be reasonable
        original = "7d"
        seconds = parse_duration_string(original)
        formatted = format_duration(seconds, precision=1)
        assert formatted == "7d"


class TestEdgeCases:
    """Test edge cases and integration."""
    
    def test_parse_format_roundtrip_simple(self):
        """Test simple round-trip conversion."""
        test_cases = [
            ("1w", 1),
            ("7d", 1),
            ("24h", 1),
            ("60m", 1),
            ("60s", 1),
        ]
        
        for duration_str, precision in test_cases:
            seconds = parse_duration_string(duration_str)
            formatted = format_duration(seconds, precision=precision)
            assert duration_str == formatted
    
    def test_parse_all_supported_units(self):
        """Test that all documented units are supported."""
        units = [
            # Weeks
            "1w", "1week", "1weeks",
            # Days
            "1d", "1day", "1days",
            # Hours
            "1h", "1hour", "1hours", "1hr", "1hrs",
            # Minutes
            "1m", "1min", "1minute", "1minutes", "1mins",
            # Seconds
            "1s", "1sec", "1second", "1seconds", "1secs",
        ]
        
        for unit_str in units:
            result = parse_duration_string(unit_str)
            assert result > 0, f"Failed to parse: {unit_str}"
    
    def test_consistency_across_representations(self):
        """Test that different representations of same duration parse to same value."""
        # 1 week = 7 days = 168 hours
        week_seconds = parse_duration_string("1w")
        days_seconds = parse_duration_string("7d")
        hours_seconds = parse_duration_string("168h")
        
        assert week_seconds == days_seconds == hours_seconds
