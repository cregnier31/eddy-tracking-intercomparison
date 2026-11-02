"""Unit tests for member indexing and member-specific detection paths."""
import pytest

from eddy_detect.gloens_members import detection_paths, member_indices


def test_member_indices_one_based_inclusive():
    assert list(member_indices(50, 1, 1)) == [0]
    assert list(member_indices(50, 49, 50)) == [48, 49]
    assert list(member_indices(50, 1, 50)) == list(range(50))


@pytest.mark.parametrize("start,end", [(0, 1), (2, 1), (1, 51), (51, 51)])
def test_member_indices_reject_invalid_ranges(start, end):
    with pytest.raises(ValueError, match="Member range"):
        list(member_indices(50, start, end))


def test_member_output_paths_are_isolated(tmp_path):
    a1, c1 = detection_paths(tmp_path, 1, "20261022")
    a2, c2 = detection_paths(tmp_path, 2, "20261022")
    assert a1 != a2
    assert c1 != c2
    assert "member_001" in str(a1)
    assert "member_002" in str(a2)
    assert a1.name == "Anticyclonic_GLOENS_20261022.nc"
    assert c1.name == "Cyclonic_GLOENS_20261022.nc"
