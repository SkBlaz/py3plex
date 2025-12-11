"""Tests for duration string parsing."""

import pytest
from py3plex.temporal_utils_extended import parse_duration_string, format_duration


class TestDurationParsing:
    """Test parsing duration strings."""
    
    def test_parse_numeric(self):
        """Test parsing numeric values."""
        assert parse_duration_string(100) == 100.0
        assert parse_duration_string(100.5) == 100.5
    
    def test_parse_seconds(self):
        """Test parsing seconds."""
        assert parse_duration_string("60s") == 60.0
        assert parse_duration_string("30sec") == 30.0
        assert parse_duration_string("45second") == 45.0
        assert parse_duration_string("90seconds") == 90.0
    
    def test_parse_minutes(self):
        """Test parsing minutes."""
        assert parse_duration_string("1m") == 60.0
        assert parse_duration_string("30m") == 1800.0
        assert parse_duration_string("5min") == 300.0
        assert parse_duration_string("10minute") == 600.0
        assert parse_duration_string("15minutes") == 900.0
    
    def test_parse_hours(self):
        """Test parsing hours."""
        assert parse_duration_string("1h") == 3600.0
        assert parse_duration_string("24h") == 86400.0
        assert parse_duration_string("2hour") == 7200.0
        assert parse_duration_string("3hours") == 10800.0
    
    def test_parse_days(self):
        """Test parsing days."""
        assert parse_duration_string("1d") == 86400.0
        assert parse_duration_string("7d") == 604800.0
        assert parse_duration_string("2day") == 172800.0
        assert parse_duration_string("3days") == 259200.0
    
    def test_parse_weeks(self):
        """Test parsing weeks."""
        assert parse_duration_string("1w") == 604800.0
        assert parse_duration_string("2w") == 1209600.0
        assert parse_duration_string("1week") == 604800.0
        assert parse_duration_string("2weeks") == 1209600.0
    
    def test_parse_decimal(self):
        """Test parsing decimal values."""
        assert parse_duration_string("1.5h") == 5400.0
        assert parse_duration_string("0.5d") == 43200.0
        assert parse_duration_string("2.5m") == 150.0
    
    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        assert parse_duration_string("1D") == 86400.0
        assert parse_duration_string("1H") == 3600.0
        assert parse_duration_string("1M") == 60.0
    
    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        assert parse_duration_string(" 7d ") == 604800.0
        assert parse_duration_string("24 h") == 86400.0
    
    def test_parse_invalid_format(self):
        """Test that invalid format raises error."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration_string("abc")
        
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration_string("7")  # Missing unit
        
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration_string("d7")  # Wrong order
    
    def test_parse_invalid_unit(self):
        """Test that invalid unit raises error."""
        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_duration_string("7x")
        
        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_duration_string("10years")


class TestDurationFormatting:
    """Test formatting durations."""
    
    def test_format_seconds(self):
        """Test formatting seconds."""
        assert format_duration(0) == "0s"
        assert format_duration(30) == "30s"
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
        assert format_duration(86400) == "1d"
        assert format_duration(172800) == "2d"
        assert format_duration(90000) == "1d 1h"
    
    def test_format_weeks(self):
        """Test formatting weeks."""
        assert format_duration(604800) == "1w"
        assert format_duration(1209600) == "2w"
    
    def test_format_precision(self):
        """Test precision parameter."""
        duration = 90061  # 1d 1h 1m 1s
        assert format_duration(duration, precision=1) == "1d"
        assert format_duration(duration, precision=2) == "1d 1h"
        assert format_duration(duration, precision=3) == "1d 1h 1m"
        assert format_duration(duration, precision=4) == "1d 1h 1m 1s"
    
    def test_format_subsecond(self):
        """Test formatting subsecond values."""
        result = format_duration(0.5)
        assert "0.5" in result
        assert "s" in result


class TestDurationRoundTrip:
    """Test round-trip conversion."""
    
    def test_roundtrip_simple(self):
        """Test round-trip for simple values."""
        durations = ["7d", "24h", "30m", "60s", "1w"]
        
        for duration in durations:
            seconds = parse_duration_string(duration)
            formatted = format_duration(seconds, precision=1)
            # Parse again and check
            seconds2 = parse_duration_string(formatted)
            assert seconds == seconds2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
