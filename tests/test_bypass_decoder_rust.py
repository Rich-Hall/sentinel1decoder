from __future__ import annotations

import numpy as np
import pytest

from sentinel1decoder._sentinel1decoder import (
    decode_batched_bypass_packets,
    decode_single_bypass_packet,
)
from tests.conftest import BypassSpecExample

from .data_generation_utils import pack_10bit_samples, pack_bits


@pytest.mark.parametrize(
    "example_index",
    [0],  # Add more indices as more examples are added to conftest
    ids=["bypass_example_1"],
)
def test_bypass_spec_examples(example_index: int, bypass_spec_examples: list[BypassSpecExample]) -> None:
    """Test bypass decoder against spec examples from conftest."""
    example = bypass_spec_examples[example_index]

    # Create packet data using pack_bits directly
    # Bypass mode: 4 channels (IE, IO, QE, QO), each with 1 quad (10-bit sample)
    # pack_bits with pack_to_16_bits=True pads to 16-bit boundaries
    ie_data = pack_bits([example.bits], pack_to_16_bits=True)
    io_data = pack_bits([example.bits], pack_to_16_bits=True)
    qe_data = pack_bits([example.bits], pack_to_16_bits=True)
    qo_data = pack_bits([example.bits], pack_to_16_bits=True)

    data = ie_data + io_data + qe_data + qo_data

    # Decode the packet
    decoded = decode_single_bypass_packet(data, num_quads=1)

    # Expected result: all channels should decode to the expected value
    expected = np.array(
        [
            complex(example.expected_value, example.expected_value),
            complex(example.expected_value, example.expected_value),
        ],
        dtype=np.complex64,
    )

    np.testing.assert_allclose(
        decoded,
        expected,
        rtol=1e-6,
        atol=1e-6,
        err_msg=f"Spec example page {example.page}: {example.description}",
    )


def test_decoding() -> None:
    # Default case - 8 * 10-bit words per channel packs exactly into 10 * 8-bit bytes, so no padding
    data = pack_10bit_samples(np.arange(32).tolist())
    decoded = decode_single_bypass_packet(data, 8)

    # Rust decoder returns interleaved complex samples: IE[0]+QE[0]j, IO[0]+QO[0]j, IE[1]+QE[1]j, IO[1]+QO[1]j, ...
    # Extract individual channels
    i_evens = decoded[0::2].real  # Real part of even indices (IE)
    i_odds = decoded[1::2].real  # Real part of odd indices (IO)
    q_evens = decoded[0::2].imag  # Imaginary part of even indices (QE)
    q_odds = decoded[1::2].imag  # Imaginary part of odd indices (QO)

    assert np.array_equal(i_evens, np.arange(8))
    assert np.array_equal(i_odds, np.arange(8, 16))
    assert np.array_equal(q_evens, np.arange(16, 24))
    assert np.array_equal(q_odds, np.arange(24, 32))

    # 4 channels, 3 quads each. 30 bits total per channel, so 2 bits padding
    ie = [200, 201, 202]
    io = [300, 301, 302]
    qe = [400, 401, 402]
    qo = [500, 501, 502]
    data = pack_10bit_samples(ie) + pack_10bit_samples(io) + pack_10bit_samples(qe) + pack_10bit_samples(qo)
    decoded = decode_single_bypass_packet(data, 3)

    i_evens = decoded[0::2].real
    i_odds = decoded[1::2].real
    q_evens = decoded[0::2].imag
    q_odds = decoded[1::2].imag

    assert np.array_equal(i_evens, ie)
    assert np.array_equal(i_odds, io)
    assert np.array_equal(q_evens, qe)
    assert np.array_equal(q_odds, qo)

    # 4 channels, 4 quads each. 40 bits total per channel, so 8 bits padding
    ie = [-200, -201, -202, -203]
    io = [-300, -301, -302, -303]
    qe = [-400, -401, -402, -403]
    qo = [-500, -501, -502, -503]
    data = pack_10bit_samples(ie) + pack_10bit_samples(io) + pack_10bit_samples(qe) + pack_10bit_samples(qo)
    decoded = decode_single_bypass_packet(data, 4)

    i_evens = decoded[0::2].real
    i_odds = decoded[1::2].real
    q_evens = decoded[0::2].imag
    q_odds = decoded[1::2].imag

    assert np.array_equal(i_evens, ie)
    assert np.array_equal(i_odds, io)
    assert np.array_equal(q_evens, qe)
    assert np.array_equal(q_odds, qo)


def test_batched_bypass_decoder_same_config() -> None:
    """Test batched decode with multiple packets of the same configuration."""
    # Create test data: 4 channels, 8 quads each
    num_quads = 8
    ie = np.arange(8)
    io = np.arange(8, 16)
    qe = np.arange(16, 24)
    qo = np.arange(24, 32)

    # Create a single packet
    single_packet_data = (
        pack_10bit_samples(ie.tolist())
        + pack_10bit_samples(io.tolist())
        + pack_10bit_samples(qe.tolist())
        + pack_10bit_samples(qo.tolist())
    )

    # Generate multiple identical packets
    num_packets = 5
    packet_data_list = [single_packet_data for _ in range(num_packets)]

    # Decode using batched function
    batched_result = decode_batched_bypass_packets(packet_data_list, num_quads)

    # Check array properties
    assert isinstance(batched_result, np.ndarray)
    assert batched_result.dtype == np.complex64
    assert batched_result.shape == (num_packets, num_quads * 2)

    # Decode one packet individually for expected values
    single_result = decode_single_bypass_packet(single_packet_data, num_quads)

    # All packets should decode to the same result
    for i in range(num_packets):
        np.testing.assert_array_equal(
            batched_result[i], single_result, err_msg=f"Packet {i} should match single decode result"
        )

    # Verify expected values
    i_evens = single_result[0::2].real
    i_odds = single_result[1::2].real
    q_evens = single_result[0::2].imag
    q_odds = single_result[1::2].imag

    assert np.array_equal(i_evens, ie)
    assert np.array_equal(i_odds, io)
    assert np.array_equal(q_evens, qe)
    assert np.array_equal(q_odds, qo)

    # Verify batched result also has correct values
    for i in range(num_packets):
        batched_i_evens = batched_result[i][0::2].real
        batched_i_odds = batched_result[i][1::2].real
        batched_q_evens = batched_result[i][0::2].imag
        batched_q_odds = batched_result[i][1::2].imag

        assert np.array_equal(batched_i_evens, ie)
        assert np.array_equal(batched_i_odds, io)
        assert np.array_equal(batched_q_evens, qe)
        assert np.array_equal(batched_q_odds, qo)


def test_batched_bypass_decoder_different_configs() -> None:
    """Test batched decode with multiple packets of different configurations."""
    num_quads = 4

    # Create different test data for each packet
    # Note: 10-bit signed integers have range -511 to +511
    packet_configs = [
        {
            "ie": [100, 101, 102, 103],
            "io": [200, 201, 202, 203],
            "qe": [300, 301, 302, 303],
            "qo": [400, 401, 402, 403],
        },
        {
            "ie": [-100, -101, -102, -103],
            "io": [-200, -201, -202, -203],
            "qe": [-300, -301, -302, -303],
            "qo": [-400, -401, -402, -403],
        },
        {
            "ie": [50, 51, 52, 53],
            "io": [150, 151, 152, 153],
            "qe": [250, 251, 252, 253],
            "qo": [350, 351, 352, 353],
        },
        {
            "ie": [0, 1, 2, 3],
            "io": [10, 11, 12, 13],
            "qe": [20, 21, 22, 23],
            "qo": [30, 31, 32, 33],
        },
        {
            "ie": [450, 451, 452, 453],
            "io": [480, 481, 482, 483],
            "qe": [500, 501, 502, 503],
            "qo": [510, 511, -511, -510],
        },
    ]

    # Create packet data for each configuration
    packet_data_list = []
    expected_results = []

    for config in packet_configs:
        packet_data = (
            pack_10bit_samples(config["ie"])
            + pack_10bit_samples(config["io"])
            + pack_10bit_samples(config["qe"])
            + pack_10bit_samples(config["qo"])
        )
        packet_data_list.append(packet_data)

        # Create expected result for this packet
        ie = np.array(config["ie"], dtype=np.float32)
        io = np.array(config["io"], dtype=np.float32)
        qe = np.array(config["qe"], dtype=np.float32)
        qo = np.array(config["qo"], dtype=np.float32)

        # Interleave as IE+QE*j, IO+QO*j
        expected = np.empty(num_quads * 2, dtype=np.complex64)
        expected[0::2] = ie + 1j * qe  # Even indices: IE+QE*j
        expected[1::2] = io + 1j * qo  # Odd indices: IO+QO*j
        expected_results.append(expected)

    # Decode using batched function
    batched_result = decode_batched_bypass_packets(packet_data_list, num_quads)

    # Check array properties
    assert isinstance(batched_result, np.ndarray)
    assert batched_result.dtype == np.complex64
    assert batched_result.shape == (len(packet_configs), num_quads * 2)

    # Verify each packet decodes correctly
    for i, (packet_data, expected) in enumerate(zip(packet_data_list, expected_results)):
        # Decode individually for comparison
        single_result = decode_single_bypass_packet(packet_data, num_quads)

        # Batched result should match single decode
        np.testing.assert_array_equal(
            batched_result[i], single_result, err_msg=f"Packet {i} batched result should match single decode result"
        )

        # Batched result should match expected values
        np.testing.assert_array_equal(batched_result[i], expected, err_msg=f"Packet {i} should match expected values")

        # Verify individual channels
        config = packet_configs[i]
        batched_i_evens = batched_result[i][0::2].real
        batched_i_odds = batched_result[i][1::2].real
        batched_q_evens = batched_result[i][0::2].imag
        batched_q_odds = batched_result[i][1::2].imag

        assert np.array_equal(batched_i_evens, config["ie"]), f"Packet {i} IE channel mismatch"
        assert np.array_equal(batched_i_odds, config["io"]), f"Packet {i} IO channel mismatch"
        assert np.array_equal(batched_q_evens, config["qe"]), f"Packet {i} QE channel mismatch"
        assert np.array_equal(batched_q_odds, config["qo"]), f"Packet {i} QO channel mismatch"
