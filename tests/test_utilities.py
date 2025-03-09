import pytest

import sentinel1decoder.constants as cnst
from sentinel1decoder.utilities import range_dec_to_sample_rate


def test_range_dec_to_sample_rate() -> None:
    base_sample_freq = 4 * cnst.F_REF
    assert range_dec_to_sample_rate(0) == (3 / 4) * base_sample_freq
    assert range_dec_to_sample_rate(1) == (2 / 3) * base_sample_freq
    # 2 is unused
    assert range_dec_to_sample_rate(3) == (5 / 9) * base_sample_freq
    assert range_dec_to_sample_rate(4) == (4 / 9) * base_sample_freq
    assert range_dec_to_sample_rate(5) == (3 / 8) * base_sample_freq
    assert range_dec_to_sample_rate(6) == (1 / 3) * base_sample_freq
    assert range_dec_to_sample_rate(7) == (1 / 6) * base_sample_freq
    assert range_dec_to_sample_rate(8) == (3 / 7) * base_sample_freq
    assert range_dec_to_sample_rate(9) == (5 / 16) * base_sample_freq
    assert range_dec_to_sample_rate(10) == (3 / 26) * base_sample_freq
    assert range_dec_to_sample_rate(11) == (4 / 11) * base_sample_freq

    with pytest.raises(Exception):
        range_dec_to_sample_rate(2)
    with pytest.raises(Exception):
        range_dec_to_sample_rate(12)
    with pytest.raises(Exception):
        range_dec_to_sample_rate(-1)
