"""Tests for GLOENS tracking config and input validation."""
import pytest

from eddy_track.gloens_members import (
    POLARITIES, track_members, tracking_config, tracking_directories,
)


def test_tracking_directories_are_member_specific(tmp_path):
    detect, track = tracking_directories(tmp_path, 2)
    assert detect == tmp_path / "GLOENS/MEMBERS/member_002/DETECT"
    assert track == tmp_path / "GLOENS/MEMBERS/member_002/TRACK"


def test_config_reuses_overlap_template(tmp_path):
    template = tmp_path / "overlap_template.yaml"
    template.write_text(
        "PATHS:\n  FILES_PATTERN: DIR_IN/EDDY_TYPE*.nc\n"
        "  SAVE_DIR: DIR_OUT\nVIRTUAL_LENGTH_MAX: 2\n"
        "TRACK_DURATION_MIN: 5\nCLASS:\n  MODULE: "
        "py_eddy_tracker.featured_tracking.area_tracker\n"
        "  CLASS: AreaTracker\n  OPTIONS:\n    cmin: .02\n"
    )
    for polarity in POLARITIES:
        content = tracking_config(template, tmp_path / "DETECT", tmp_path / "TRACK", polarity)
        assert f"{polarity}*.nc" in content
        assert "AreaTracker" in content
        assert "cmin: .02" in content
        assert "TRACK_DURATION_MIN: 5" in content
        assert "DIR_IN" not in content
        assert "DIR_OUT" not in content


def test_tracking_rejects_missing_daily_files(tmp_path, monkeypatch):
    monkeypatch.setattr("eddy_track.gloens_members.shutil.which", lambda _: "/bin/true")
    with pytest.raises(ValueError, match="expected 28"):
        track_members(tmp_path)
