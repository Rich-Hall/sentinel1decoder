import pytest

from sentinel1decoder._headers import decode_primary_header


def test_decode_primary_header() -> None:
    # Supply too few bytes
    with pytest.raises(Exception):
        decode_primary_header(b"\xFF")
    # Supply too many bytes
    with pytest.raises(Exception):
        decode_primary_header(
            b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
        )

    # TODO: More tests here - get some mock data
