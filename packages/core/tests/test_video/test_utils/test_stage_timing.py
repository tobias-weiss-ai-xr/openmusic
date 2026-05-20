"""Test stage timing utilities."""

from openmusic.video.utils.stage_timing import STAGE_BOUNDARIES, STAGE_PROMPTS, _compute_stage_timings


def test_stage_boundaries_structure():
    assert len(STAGE_BOUNDARIES) == 10
    assert STAGE_BOUNDARIES[0] == (0.00, "ambient-intro")
    assert STAGE_BOUNDARIES[9] == (1.30, "dissolution")


def test_stage_prompts_structure():
    stage_names = [name for _, name in STAGE_BOUNDARIES]
    for stage_name in stage_names:
        assert stage_name in STAGE_PROMPTS
        prompts = STAGE_PROMPTS[stage_name]
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert all(isinstance(p, str) for p in prompts)


def test_compute_stage_timings():
    timings = _compute_stage_timings(3600.0)

    assert len(timings) == 9
    assert timings[0] == (0.0, 360.0, "ambient-intro")
    assert timings[4] == (2160.0, 2700.0, "peak-one")