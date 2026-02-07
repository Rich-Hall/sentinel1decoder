import pandas as pd
import pytest

import sentinel1decoder.constants as cnst
from sentinel1decoder.utilities import (
    range_dec_to_sample_rate,
    rename_packet_metadata_columns_to_parsed,
    rename_packet_metadata_columns_to_raw,
)


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


def test_rename_packet_metadata_columns_to_raw() -> None:
    """Rename parsed columns to raw; no-op when already raw."""
    df_decoded = pd.DataFrame({"ECC Number": [1], "BAQ Mode": [12]})
    df_raw = rename_packet_metadata_columns_to_raw(df_decoded)
    assert "ECC" in df_raw.columns
    assert "BAQMOD" in df_raw.columns
    assert "ECC Number" not in df_raw.columns

    # No-op when already raw
    df_raw2 = rename_packet_metadata_columns_to_raw(df_raw)
    assert df_raw2 is df_raw
    assert list(df_raw2.columns) == ["ECC", "BAQMOD"]


def test_rename_packet_metadata_columns_to_parsed() -> None:
    """Rename raw columns to parsed; no-op when already parsed."""
    df_raw = pd.DataFrame({"ECC": [1], "BAQMOD": [12]})
    df_decoded = rename_packet_metadata_columns_to_parsed(df_raw)
    assert "ECC Number" in df_decoded.columns
    assert "BAQ Mode" in df_decoded.columns
    assert "ECC" not in df_decoded.columns

    # No-op when already decoded
    df_decoded2 = rename_packet_metadata_columns_to_parsed(df_decoded)
    assert df_decoded2 is df_decoded
