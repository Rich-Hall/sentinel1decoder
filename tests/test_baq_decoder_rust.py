from __future__ import annotations

import numpy as np
import pytest

from sentinel1decoder._sentinel1decoder import (
    decode_batched_baq_packets,
    decode_single_baq_packet,
)
from tests.data_generation_utils import pack_bits


BLOCK_QUADS = 128


def _encode_baq_sample(value: int, baq_bits: int) -> str:
    max_magnitude = (1 << (baq_bits - 1)) - 1
    if not -max_magnitude <= value <= max_magnitude:
        raise ValueError(f"value {value} is out of range for {baq_bits}-bit BAQ")

    sign_bit = "1" if value < 0 else "0"
    magnitude_bits = format(abs(value), f"0{baq_bits - 1}b")
    return sign_bit + magnitude_bits


def _pack_baq_channel(values: list[int], baq_bits: int) -> bytes:
    return pack_bits([_encode_baq_sample(value, baq_bits) for value in values], pack_to_16_bits=True)


def _build_baq_packet(
    ie_values: list[int],
    io_values: list[int],
    qe_values: list[int],
    qo_values: list[int],
    baq_bits: int,
    thidx_values: list[int],
) -> bytes:
    num_quads = len(ie_values)
    num_blocks = (num_quads + BLOCK_QUADS - 1) // BLOCK_QUADS

    if not (
        len(io_values) == len(qe_values) == len(qo_values) == num_quads
        and len(thidx_values) == num_blocks
    ):
        raise ValueError("channel lengths must match and thidx values must match the block count")

    ie_data = _pack_baq_channel(ie_values, baq_bits)
    io_data = _pack_baq_channel(io_values, baq_bits)
    qo_data = _pack_baq_channel(qo_values, baq_bits)

    qe_bits: list[str] = []
    for block_idx in range(num_blocks):
        block_start = block_idx * BLOCK_QUADS
        block_end = min(block_start + BLOCK_QUADS, num_quads)
        qe_bits.append(format(thidx_values[block_idx], "08b"))
        qe_bits.extend(_encode_baq_sample(value, baq_bits) for value in qe_values[block_start:block_end])

    qe_data = pack_bits(qe_bits, pack_to_16_bits=True)
    return ie_data + io_data + qe_data + qo_data


def _expected_samples(
    ie_values: list[int],
    io_values: list[int],
    qe_values: list[int],
    qo_values: list[int],
) -> np.ndarray:
    expected = np.empty(len(ie_values) * 2, dtype=np.complex64)
    expected[0::2] = np.asarray(ie_values, dtype=np.float32) + 1j * np.asarray(qe_values, dtype=np.float32)
    expected[1::2] = np.asarray(io_values, dtype=np.float32) + 1j * np.asarray(qo_values, dtype=np.float32)
    return expected


def _assert_decoded_packet(decoded: np.ndarray, expected: np.ndarray, num_quads: int) -> None:
    assert decoded.dtype == np.complex64
    assert decoded.shape == (num_quads * 2,)
    np.testing.assert_allclose(decoded, expected, rtol=1e-6, atol=1e-6)


_SIGMA_FACTORS = [0, 0, 0, 0, 0, 3.13] # sigma factors for THIDX values 5
_A4 = [0, 0, 0, 0, 0, 7.76]
_A5 = [0, 0, 0, 0, 0, 15.0, 0, 0, 0, 0, 0]
_NRL_A3 = [0.2490, 0.7681, 1.3655, 2.1864]
_NRL_A4 = [0.129, 0.39, 0.6601, 0.9471, 1.2623, 1.6261, 2.0793, 2.7467]



def _reconstruct_unsigned_sample_value_baq(mcode: int, baq_bits: int, thidx: int) -> float:
    if baq_bits == 3:
        if mcode >= 4:
            raise ValueError(f"mcode {mcode} is out of range for {baq_bits}-bit BAQ")
        if thidx <= 3:
            return float(mcode) if mcode < 3 else _A3[thidx]
        return _NRL_A3[mcode] * _SIGMA_FACTORS[thidx]

    if baq_bits == 4:
        if mcode >= 8:
            raise ValueError(f"mcode {mcode} is out of range for {baq_bits}-bit BAQ")
        if thidx <= 5:
            return float(mcode) if mcode < 7 else _A4[thidx]
        return _NRL_A4[mcode] * _SIGMA_FACTORS[thidx]

    if baq_bits == 5:
        if mcode >= 16:
            raise ValueError(f"mcode {mcode} is out of range for {baq_bits}-bit BAQ")
        if thidx <= 10:
            return float(mcode) if mcode < 15 else _A5[thidx]
        return _NRL_A5[mcode] * _SIGMA_FACTORS[thidx]

    raise ValueError(f"unsupported BAQ width: {baq_bits}")


def _expected_reconstructed_samples(
    ie_values: list[int],
    io_values: list[int],
    qe_values: list[int],
    qo_values: list[int],
    baq_bits: int,
    thidx_values: list[int],
) -> np.ndarray:
    expected = np.empty(len(ie_values) * 2, dtype=np.complex64)

    for block_idx, thidx in enumerate(thidx_values):
        block_start = block_idx * 128
        block_end = min(block_start + 128, len(ie_values))

        ie_block = [
            _reconstruct_unsigned_sample_value_baq(abs(value), baq_bits, thidx)
            * (-1.0 if value < 0 else 1.0)
            for value in ie_values[block_start:block_end]
        ]
        io_block = [
            _reconstruct_unsigned_sample_value_baq(abs(value), baq_bits, thidx)
            * (-1.0 if value < 0 else 1.0)
            for value in io_values[block_start:block_end]
        ]
        qe_block = [
            _reconstruct_unsigned_sample_value_baq(abs(value), baq_bits, thidx)
            * (-1.0 if value < 0 else 1.0)
            for value in qe_values[block_start:block_end]
        ]
        qo_block = [
            _reconstruct_unsigned_sample_value_baq(abs(value), baq_bits, thidx)
            * (-1.0 if value < 0 else 1.0)
            for value in qo_values[block_start:block_end]
        ]

        block_expected = np.empty((block_end - block_start) * 2, dtype=np.complex64)
        block_expected[0::2] = np.asarray(ie_block, dtype=np.float32) + 1j * np.asarray(qe_block, dtype=np.float32)
        block_expected[1::2] = np.asarray(io_block, dtype=np.float32) + 1j * np.asarray(qo_block, dtype=np.float32)
        expected[block_start * 2 : block_end * 2] = block_expected

    return expected


@pytest.mark.parametrize("baq_bits", [3, 4, 5])
def test_single_baq_packet_roundtrip(baq_bits: int) -> None:
    num_quads = 256

    ie_values = [1] * 128 + [2] * 128
    io_values = [-1] * 128 + [-2] * 128
    qe_values = [3] * 128 + [1] * 128
    qo_values = [-2] * 128 + [-3] * 128

    data = _build_baq_packet(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values=[0, 0])
    decoded = decode_single_baq_packet(data, num_quads=num_quads, baq_bits=baq_bits)

    expected = _expected_samples(ie_values, io_values, qe_values, qo_values)

    _assert_decoded_packet(decoded, expected, num_quads)


@pytest.mark.parametrize("baq_bits", [3, 4, 5])
def test_batched_baq_packets_match_single(baq_bits: int) -> None:
    num_quads = 256

    packet_specs = [
        (
            [1] * 128 + [2] * 128,
            [-1] * 128 + [-2] * 128,
            [3] * 128 + [1] * 128,
            [-2] * 128 + [-3] * 128,
        ),
        (
            [2] * 128 + [1] * 128,
            [-2] * 128 + [-1] * 128,
            [1] * 128 + [3] * 128,
            [-3] * 128 + [-2] * 128,
        ),
    ]

    packet_data_list = []
    expected_results = []

    for ie_values, io_values, qe_values, qo_values in packet_specs:
        packet_data = _build_baq_packet(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values=[0, 0])
        packet_data_list.append(packet_data)
        expected_results.append(_expected_samples(ie_values, io_values, qe_values, qo_values))

    batched = decode_batched_baq_packets(packet_data_list, num_quads=num_quads, baq_bits=baq_bits)

    assert batched.dtype == np.complex64
    assert batched.shape == (len(packet_specs), num_quads * 2)

    for index, expected in enumerate(expected_results):
        single = decode_single_baq_packet(packet_data_list[index], num_quads=num_quads, baq_bits=baq_bits)
        _assert_decoded_packet(batched[index], expected, num_quads)
        _assert_decoded_packet(batched[index], single, num_quads)


@pytest.mark.parametrize("baq_bits", [3, 4, 5])
def test_single_baq_packet_with_nonezero_thidx(baq_bits: int) -> None:
    num_quads = 256
    thidx_values = [5,5]

    if baq_bits == 3:
        block_pattern = [0, -1, -2, -3] * 32 # thidx 5 > 3
    elif baq_bits == 4:
        block_pattern = [0, 1, 2, 3, 4, 5, 6, 7] * 16 # thidx 5 = 5
    else:
        block_pattern = list(range(16)) * 8 # thidx 5 < 10

    ie_values = block_pattern + block_pattern
    io_values = [-value for value in block_pattern] + [-value for value in block_pattern]
    qe_values = block_pattern + block_pattern
    qo_values = [-value for value in block_pattern] + [-value for value in block_pattern]

    data = _build_baq_packet(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values=thidx_values)
    decoded = decode_single_baq_packet(data, num_quads=num_quads, baq_bits=baq_bits)

    expected = _expected_reconstructed_samples(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values)

    _assert_decoded_packet(decoded, expected, num_quads)


@pytest.mark.parametrize("baq_bits", [3, 4, 5])
def test_single_baq_packet_with_partial_final_block(baq_bits: int) -> None:
    num_quads = 129
    thidx_values = [0, 0]

    ie_values = [1] * 128 + [2]
    io_values = [-1] * 128 + [-2]
    qe_values = [3] * 128 + [1]
    qo_values = [-2] * 128 + [-3]

    data = _build_baq_packet(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values=thidx_values)
    decoded = decode_single_baq_packet(data, num_quads=num_quads, baq_bits=baq_bits)

    expected = _expected_samples(ie_values, io_values, qe_values, qo_values)

    _assert_decoded_packet(decoded, expected, num_quads)


@pytest.mark.parametrize("baq_bits", [3, 4, 5])
def test_single_baq_packet_short_packet_raises_value_error(baq_bits: int) -> None:
    num_quads = 256

    ie_values = [1] * 128 + [2] * 128
    io_values = [-1] * 128 + [-2] * 128
    qe_values = [3] * 128 + [1] * 128
    qo_values = [-2] * 128 + [-3] * 128

    valid_data = _build_baq_packet(ie_values, io_values, qe_values, qo_values, baq_bits, thidx_values=[0, 0])
    short_data = valid_data[:-1]

    with pytest.raises(ValueError, match="Data too short for BAQ"):
        decode_single_baq_packet(short_data, num_quads=num_quads, baq_bits=baq_bits)