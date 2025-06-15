import numpy as np

from sentinel1decoder._bypass_decoder import (
    BypassDecoder,
    _ten_bit_unsigned_to_signed_int,
)

from .data_generation_utils import pack_10bit_samples


def test_ten_bit_unsigned_to_signed_int() -> None:
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


def test_decoding() -> None:
    # Default case - 8 * 10-bit words per channel packs exactly into 10 * 8-bit bytes, so no padding
    data = pack_10bit_samples(np.arange(32).tolist())
    decoder = BypassDecoder(data, 8)
    assert np.array_equal(decoder.i_evens, np.arange(8))
    assert np.array_equal(decoder.i_odds, np.arange(8, 16))
    assert np.array_equal(decoder.q_evens, np.arange(16, 24))
    assert np.array_equal(decoder.q_odds, np.arange(24, 32))

    # 4 channels, 3 quads each. 30 bits total per channel, so 2 bits padding
    ie = [200, 201, 202]
    io = [300, 301, 302]
    qe = [400, 401, 402]
    qo = [500, 501, 502]
    data = pack_10bit_samples(ie) + pack_10bit_samples(io) + pack_10bit_samples(qe) + pack_10bit_samples(qo)
    decoder = BypassDecoder(data, 3)
    assert np.array_equal(decoder.i_evens, ie)
    assert np.array_equal(decoder.i_odds, io)
    assert np.array_equal(decoder.q_evens, qe)
    assert np.array_equal(decoder.q_odds, qo)

    # 4 channels, 4 quads each. 40 bits total per channel, so 8 bits padding
    ie = [-200, -201, -202, -203]
    io = [-300, -301, -302, -303]
    qe = [-400, -401, -402, -403]
    qo = [-500, -501, -502, -503]
    data = pack_10bit_samples(ie) + pack_10bit_samples(io) + pack_10bit_samples(qe) + pack_10bit_samples(qo)
    decoder = BypassDecoder(data, 4)
    assert np.array_equal(decoder.i_evens, ie)
    assert np.array_equal(decoder.i_odds, io)
    assert np.array_equal(decoder.q_evens, qe)
    assert np.array_equal(decoder.q_odds, qo)
