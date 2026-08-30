import pytest
from omnidown.utils.time_parser import (
    parse_single_timestamp,
    parse_time_range,
    format_seconds,
)

def test_parse_single_timestamp_seconds():
    assert parse_single_timestamp("90") == 90.0
    assert parse_single_timestamp("90s") == 90.0
    assert parse_single_timestamp("15.5s") == 15.5
    assert parse_single_timestamp("0") == 0.0

def test_parse_single_timestamp_units():
    assert parse_single_timestamp("1h20m30s") == 3600 + 20 * 60 + 30
    assert parse_single_timestamp("15m") == 15 * 60
    assert parse_single_timestamp("1.5m") == 90.0
    assert parse_single_timestamp("2h30s") == 7200 + 30

def test_parse_single_timestamp_clock():
    assert parse_single_timestamp("01:30") == 90.0
    assert parse_single_timestamp("1:30") == 90.0
    assert parse_single_timestamp("01:30:45") == 3600 + 30 * 60 + 45
    assert parse_single_timestamp("00:00:15.500") == 15.5

def test_parse_single_timestamp_garbage():
    with pytest.raises(ValueError):
        parse_single_timestamp("1:75") # invalid seconds >= 60 in clock format
    with pytest.raises(ValueError):
        parse_single_timestamp("75:30") # invalid minutes >= 60 in clock format
    with pytest.raises(ValueError):
        parse_single_timestamp("-15")
    with pytest.raises(ValueError):
        parse_single_timestamp("abc")
    with pytest.raises(ValueError):
        parse_single_timestamp("")

def test_parse_time_range_hyphen():
    r = parse_time_range("00:30-01:45")
    assert r.start_seconds == 30.0
    assert r.end_seconds == 105.0
    assert r.duration_seconds == 75.0
    assert r.formatted_start == "00:00:30"
    assert r.formatted_end == "00:01:45"
    assert r.ytdlp_section_spec == "*00:00:30-00:01:45"

def test_parse_time_range_plus():
    r = parse_time_range("00:30+15s")
    assert r.start_seconds == 30.0
    assert r.end_seconds == 45.0
    assert r.duration_seconds == 15.0

def test_parse_time_range_clamp():
    r = parse_time_range("01:00-05:00", max_duration=120.0) # max 2 minutes
    assert r.start_seconds == 60.0
    assert r.end_seconds == 120.0
    assert r.duration_seconds == 60.0

def test_parse_time_range_invalid():
    with pytest.raises(ValueError):
        parse_time_range("01:45-00:30") # start >= end
    with pytest.raises(ValueError):
        parse_time_range("01:00-01:00")
    with pytest.raises(ValueError):
        parse_time_range("invalid_range")
