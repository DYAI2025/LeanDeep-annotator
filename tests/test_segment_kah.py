"""Tests for KAH transcript segmentation tool."""

import pytest

from tools.segment_kah_transcript import (
    assign_theme,
    merge_small_segments,
    segment_by_time_gaps,
)


def test_segments_at_30s_gap():
    messages = [
        {"text": "A", "start_time": 0, "role": "S0"},
        {"text": "B", "start_time": 10, "role": "S1"},
        {"text": "C", "start_time": 50, "role": "S0"},
        {"text": "D", "start_time": 55, "role": "S1"},
    ]
    segs = segment_by_time_gaps(messages, gap_threshold=30)
    assert len(segs) == 2
    assert len(segs[0]) == 2
    assert len(segs[1]) == 2


def test_no_gap_single_segment():
    messages = [
        {"text": "A", "start_time": 0, "role": "S0"},
        {"text": "B", "start_time": 5, "role": "S1"},
        {"text": "C", "start_time": 10, "role": "S0"},
    ]
    segs = segment_by_time_gaps(messages, gap_threshold=30)
    assert len(segs) == 1
    assert len(segs[0]) == 3


def test_empty_messages():
    segs = segment_by_time_gaps([], gap_threshold=30)
    assert len(segs) == 0


def test_merge_small_segments():
    segs = [
        [{"text": "a", "start_time": 0}],  # too small
        [{"text": "b", "start_time": 10}, {"text": "c", "start_time": 15}],  # small
        [{"text": "d", "start_time": 50}] * 15,  # big enough
    ]
    merged = merge_small_segments(segs, min_messages=5)
    assert len(merged) <= 2  # first two should merge


def test_merge_all_small():
    segs = [
        [{"text": "a", "start_time": 0}],
        [{"text": "b", "start_time": 10}],
        [{"text": "c", "start_time": 20}],
    ]
    merged = merge_small_segments(segs, min_messages=5)
    assert len(merged) == 1  # all merge into one


def test_assign_theme_by_keywords():
    messages = [{"text": "Ich habe solche Angst und mein Koerper verkrampft sich."}]
    theme = assign_theme(messages)
    assert theme is not None
    assert isinstance(theme, str)


def test_assign_theme_angst():
    messages = [
        {"text": "Ich habe Angst und Panik."},
        {"text": "Die Furcht ueberwaeltigt mich."},
    ]
    theme = assign_theme(messages)
    assert theme == "angst"


def test_assign_theme_admin():
    messages = [
        {"text": "Wir muessen den Antrag bei der Krankenkasse einreichen."},
        {"text": "Der Termin ist am Montag."},
    ]
    theme = assign_theme(messages)
    assert theme == "admin"


def test_assign_theme_koerper():
    messages = [
        {"text": "Mein Koerper ist total verkrampft."},
        {"text": "Ich habe Kopfschmerzen und bin muede."},
    ]
    theme = assign_theme(messages)
    assert theme == "koerper"


def test_assign_theme_fallback():
    messages = [{"text": "Ja genau."}]
    theme = assign_theme(messages)
    # Should still return a string, even if generic
    assert isinstance(theme, str)


def test_assign_theme_ego_state():
    messages = [
        {"text": "Die Ego-State Arbeit war sehr interessant."},
        {"text": "Die Integration nach der Ketamin-Sitzung."},
    ]
    theme = assign_theme(messages)
    assert theme == "ego_state_integration"
