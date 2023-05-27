from sentinel1decoder._headers import decode_primary_header

import pytest

def test_decode_primary_header():
    # Supply too few bytes
    with pytest.raises(Exception):
        decode_primary_header(0xFF)
    # Supply too many bytes
    with pytest.raises(Exception):
        decode_primary_header(0xFFFFFFFFFFFFFF)

    # TODO: More tests here - get some mock data