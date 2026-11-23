import pytest

from morph_studio.schema import load_storyboard
from morph_studio.timeline import compile_timeline, frame_count_for_beats, timeline_as_dict

STORYBOARD = "configs/sequences/organic-machines.yaml"


def test_beat_to_wan_65_frames():
    assert frame_count_for_beats(8, 120, 16) == 65


def test_valid_wan_lengths_and_limits():
    for beats in (1, 2, 4, 8, 10):
        result = frame_count_for_beats(beats, 120, 16)
        assert (result - 1) % 4 == 0
        assert result <= 81
    with pytest.raises(ValueError):
        frame_count_for_beats(12, 120, 16, max_frames=81)


def test_anchor_timestamp_and_seam_dedupe():
    data = load_storyboard(STORYBOARD)
    plans = compile_timeline(data)
    assert [p.frames for p in plans] == [65, 65]
    assert [p.actual_span_seconds for p in plans] == [4.0, 4.0]
    out = timeline_as_dict(data)
    assert out["frame_total_if_matching_endpoints"] == 129
    assert out["anchor_timestamp_span_seconds"] == 8.0


def test_negative_timing_rejected():
    with pytest.raises(ValueError):
        frame_count_for_beats(-1, 120, 16)
    with pytest.raises(ValueError):
        frame_count_for_beats(4, 0, 16)
