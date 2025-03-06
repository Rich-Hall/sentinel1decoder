from sentinel1decoder._sample_code_bypass import _ten_bit_unsigned_to_signed_int


def test_ten_bit_unsigned_to_signed_int():
    # 0000000000
    assert _ten_bit_unsigned_to_signed_int(0x000) == 0

    # 1111111111
    assert _ten_bit_unsigned_to_signed_int(0x3FF) == -511

    # 0111111111
    assert _ten_bit_unsigned_to_signed_int(0x1FF) == 511

    # 1000000001
    assert _ten_bit_unsigned_to_signed_int(0x201) == -1

    # 0000000001
    assert _ten_bit_unsigned_to_signed_int(0x001) == 1

    # 1010111100 - example used in ESA's documentation
    assert _ten_bit_unsigned_to_signed_int(0x2BC) == -188

    # 0101010101
    assert _ten_bit_unsigned_to_signed_int(0x155) == 341

    # 111111111111111111111111111111111111 - too long
    assert _ten_bit_unsigned_to_signed_int(0xFFFFFFFFFF) == -511
