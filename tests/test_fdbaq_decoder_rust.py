import itertools

import numpy as np
import pytest

from sentinel1decoder._sentinel1decoder import (
    decode_batched_fdbaq_packets,
    decode_single_fdbaq_packet,
)
from tests.conftest import FDBAQSpecExample
from tests.data_generation_utils import (
    PacketConfig,
    create_synthetic_fdbaq_data,
    pack_bits,
)


@pytest.mark.parametrize(
    "example_index",
    [0, 1, 2, 3],
    ids=["Spec example 1", "Spec example 2", "Spec example 3", "Longest HCode case"],
)
def test_fdbaq_single_packet_spec_example(example_index: int, fdbaq_spec_examples: list[FDBAQSpecExample]) -> None:
    example = fdbaq_spec_examples[example_index]

    config = PacketConfig(
        num_quads=1,
        const_brc=example.brc,
        const_thidx=example.thidx,
    )

    data = create_synthetic_fdbaq_data(config, example.huffman_bits)
    decoded = decode_single_fdbaq_packet(data, num_quads=1)

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


def test_fdbaq_batched_decoding_matches_single(
    fdbaq_spec_examples: list[FDBAQSpecExample],
) -> None:
    """
    Each spec example decoded in a batch must match
    the corresponding single-packet decode.
    """

    packet_data_list = []
    expected_results = []

    for example in fdbaq_spec_examples:
        config = PacketConfig(
            num_quads=1,
            const_brc=example.brc,
            const_thidx=example.thidx,
        )

        data = create_synthetic_fdbaq_data(config, example.huffman_bits)
        packet_data_list.append(data)

        single = decode_single_fdbaq_packet(data, num_quads=1)
        expected_results.append(single)

    batched = decode_batched_fdbaq_packets(packet_data_list, num_quads=1)

    assert batched.shape == (len(fdbaq_spec_examples), 2)
    assert batched.dtype == np.complex64

    for i, expected in enumerate(expected_results):
        np.testing.assert_allclose(
            batched[i],
            expected,
            rtol=1e-6,
            atol=1e-6,
            err_msg=f"Mismatch for spec example on page {fdbaq_spec_examples[i].page}",
        )


def test_fdbaq_multiple_blocks_one_packet(
    fdbaq_spec_examples: list[FDBAQSpecExample],
) -> None:
    """
    Test decoding a single packet with multiple blocks (128 samples each),
    where each block uses a different spec example.
    """
    # Create data with 3 blocks of 128 samples each (384 quads total)
    # Block 0: example 0, Block 1: example 1, Block 2: example 2

    all_bit_strings_ie = []
    all_bit_strings_io = []
    all_bit_strings_qe = []
    all_bit_strings_qo = []

    for example in fdbaq_spec_examples:
        # IE channel: BRC prefix (3 bits) + 128 huffman patterns
        all_bit_strings_ie.append(format(example.brc, "03b"))
        all_bit_strings_ie.extend([example.huffman_bits] * 128)

        # IO channel: no prefix + 128 huffman patterns
        all_bit_strings_io.extend([example.huffman_bits] * 128)

        # QE channel: THIDX prefix (8 bits) + 128 huffman patterns
        all_bit_strings_qe.append(format(example.thidx, "08b"))
        all_bit_strings_qe.extend([example.huffman_bits] * 128)

        # QO channel: no prefix + 128 huffman patterns
        all_bit_strings_qo.extend([example.huffman_bits] * 128)

    # Pack all bits together (pack_to_16_bits=True pads to 16-bit boundaries)
    ie_data = pack_bits(all_bit_strings_ie, pack_to_16_bits=True)
    io_data = pack_bits(all_bit_strings_io, pack_to_16_bits=True)
    qe_data = pack_bits(all_bit_strings_qe, pack_to_16_bits=True)
    qo_data = pack_bits(all_bit_strings_qo, pack_to_16_bits=True)

    # Combine all channels
    data = ie_data + io_data + qe_data + qo_data

    # Decode the packet (384 quads = 3 blocks of 128)
    num_quads = len(fdbaq_spec_examples) * 128
    decoded = decode_single_fdbaq_packet(data, num_quads=num_quads)

    # Build expected result: each block of 128 samples should decode to the example's expected value
    expected_blocks = []
    for example in fdbaq_spec_examples:
        # Each block has 128 quads = 256 complex samples (128 * 2)
        block_expected = np.array(
            [
                complex(example.expected_value, example.expected_value),
                complex(example.expected_value, example.expected_value),
            ]
            * 128,
            dtype=np.complex64,
        )
        expected_blocks.append(block_expected)

    expected = np.concatenate(expected_blocks)

    assert (
        decoded.shape == expected.shape
    ), f"Decoded shape {decoded.shape} doesn't match expected shape {expected.shape}"

    np.testing.assert_allclose(
        decoded,
        expected,
        rtol=1e-6,
        atol=1e-6,
        err_msg="Multi-block packet should decode correctly with each block using different spec examples",
    )


def test_fdbaq_batched_multiple_blocks_different_permutations(
    fdbaq_spec_examples: list[FDBAQSpecExample],
) -> None:
    """
    Test batch decoding multiple packets, where each packet contains all spec examples
    as blocks of 128 samples, but in different permutations.
    """
    # Generate all permutations of the spec examples
    permutations = list(itertools.permutations(fdbaq_spec_examples))

    packet_data_list = []
    expected_results = []

    for permuted_examples in permutations:
        # Create packet data with this permutation of examples
        all_bit_strings_ie = []
        all_bit_strings_io = []
        all_bit_strings_qe = []
        all_bit_strings_qo = []

        for example in permuted_examples:
            # IE channel: BRC prefix (3 bits) + 128 huffman patterns
            all_bit_strings_ie.append(format(example.brc, "03b"))
            all_bit_strings_ie.extend([example.huffman_bits] * 128)

            # IO channel: no prefix + 128 huffman patterns
            all_bit_strings_io.extend([example.huffman_bits] * 128)

            # QE channel: THIDX prefix (8 bits) + 128 huffman patterns
            all_bit_strings_qe.append(format(example.thidx, "08b"))
            all_bit_strings_qe.extend([example.huffman_bits] * 128)

            # QO channel: no prefix + 128 huffman patterns
            all_bit_strings_qo.extend([example.huffman_bits] * 128)

        # Pack all bits together (pack_to_16_bits=True pads to 16-bit boundaries)
        ie_data = pack_bits(all_bit_strings_ie, pack_to_16_bits=True)
        io_data = pack_bits(all_bit_strings_io, pack_to_16_bits=True)
        qe_data = pack_bits(all_bit_strings_qe, pack_to_16_bits=True)
        qo_data = pack_bits(all_bit_strings_qo, pack_to_16_bits=True)

        # Combine all channels
        data = ie_data + io_data + qe_data + qo_data
        packet_data_list.append(data)

        # Build expected result for this permutation
        expected_blocks = []
        for example in permuted_examples:
            # Each block has 128 quads = 256 complex samples (128 * 2)
            block_expected = np.array(
                [
                    complex(example.expected_value, example.expected_value),
                    complex(example.expected_value, example.expected_value),
                ]
                * 128,
                dtype=np.complex64,
            )
            expected_blocks.append(block_expected)

        expected_array = np.concatenate(expected_blocks)
        expected_results.append(expected_array)

    # Decode all packets in batch
    num_quads = len(fdbaq_spec_examples) * 128
    batched = decode_batched_fdbaq_packets(packet_data_list, num_quads=num_quads)

    # Verify batch shape
    assert batched.shape == (len(permutations), num_quads * 2)
    assert batched.dtype == np.complex64

    # Verify each packet in the batch matches its expected result
    for i, expected in enumerate(expected_results):
        np.testing.assert_allclose(
            batched[i],
            expected,
            rtol=1e-6,
            atol=1e-6,
            err_msg=f"Mismatch for permutation {i}",
        )

        # Also verify against single-packet decode
        single = decode_single_fdbaq_packet(packet_data_list[i], num_quads=num_quads)
        np.testing.assert_allclose(
            batched[i],
            single,
            rtol=1e-6,
            atol=1e-6,
            err_msg=f"Batch decode doesn't match single decode for permutation {i}",
        )
