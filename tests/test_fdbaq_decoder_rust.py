import math

import numpy as np

from sentinel1decoder._sample_code import SampleCode
from sentinel1decoder._sample_value_reconstruction import reconstruct_channel_vals
from sentinel1decoder._sentinel1decoder import (
    decode_batched_fdbaq_packets,
    decode_single_fdbaq_packet,
)

from .data_generation_utils import PacketConfig, create_synthetic_fdbaq_data, pack_bits


def assert_complex_arrays_close(
    actual: np.ndarray, expected: np.ndarray, rtol: float = 1e-5, atol: float = 1e-6
) -> None:
    """Assert that two complex arrays are close, with detailed diagnostics on failure.

    Args:
        actual: The actual array from the decoder
        expected: The expected array from reconstruction
        rtol: Relative tolerance
        atol: Absolute tolerance
    """
    try:
        np.testing.assert_allclose(actual, expected, rtol=rtol, atol=atol)
    except AssertionError as e:
        # Calculate differences
        diff = np.abs(actual - expected)
        max_diff_idx = np.argmax(diff)
        max_diff = diff[max_diff_idx]

        # Find all indices where difference exceeds tolerance
        # For complex numbers, we need to check both real and imaginary parts
        real_diff = np.abs(actual.real - expected.real)
        imag_diff = np.abs(actual.imag - expected.imag)

        # Relative tolerance check
        rel_tol_real = np.abs(real_diff / (np.abs(expected.real) + atol))
        rel_tol_imag = np.abs(imag_diff / (np.abs(expected.imag) + atol))

        # Find mismatches
        real_mismatches = np.where((real_diff > atol) & (rel_tol_real > rtol))[0]
        imag_mismatches = np.where((imag_diff > atol) & (rel_tol_imag > rtol))[0]
        all_mismatches = np.unique(np.concatenate([real_mismatches, imag_mismatches]))

        # Build detailed error message
        error_msg = [str(e)]
        error_msg.append(f"\nArray shape: actual={actual.shape}, expected={expected.shape}")
        error_msg.append(f"Array dtype: actual={actual.dtype}, expected={expected.dtype}")
        error_msg.append(f"\nTotal mismatches: {len(all_mismatches)} out of {len(actual)} elements")
        error_msg.append(f"Maximum absolute difference: {max_diff:.2e} at index {max_diff_idx}")
        error_msg.append(f"  actual[{max_diff_idx}] = {actual[max_diff_idx]}")
        error_msg.append(f"  expected[{max_diff_idx}] = {expected[max_diff_idx]}")

        if len(all_mismatches) > 0:
            error_msg.append("\nFirst 20 mismatches:")
            for idx in all_mismatches[:20]:
                error_msg.append(
                    f"  [{idx}] actual={actual[idx]}, expected={expected[idx]}, "
                    f"diff={diff[idx]:.2e} (real_diff={real_diff[idx]:.2e}, imag_diff={imag_diff[idx]:.2e})"
                )
            if len(all_mismatches) > 20:
                error_msg.append(f"  ... and {len(all_mismatches) - 20} more mismatches")

        # Summary statistics
        error_msg.append("\nDifference statistics:")
        error_msg.append(f"  Mean absolute difference: {np.mean(diff):.2e}")
        error_msg.append(f"  Median absolute difference: {np.median(diff):.2e}")
        error_msg.append(f"  Max absolute difference: {np.max(diff):.2e}")
        error_msg.append(f"  Min absolute difference: {np.min(diff):.2e}")
        error_msg.append(f"  Std dev of differences: {np.std(diff):.2e}")

        raise AssertionError("\n".join(error_msg)) from e


def test_fdbaq_decoder_brc0() -> None:
    config = PacketConfig(num_quads=128, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    complex_samples = decode_single_fdbaq_packet(data, 128)

    # Check array properties
    assert isinstance(complex_samples, np.ndarray)
    assert complex_samples.dtype == np.complex64
    assert len(complex_samples) == 128 * 2  # Interleaved: IE+QE, IO+QO

    # Expected value: sign=False (0), magnitude=0, BRC=0, THIDX=0
    sample_codes = [SampleCode(0, 0)] * 128
    expected_vals = reconstruct_channel_vals(sample_codes, [0], [0], 128)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=1234, const_brc=0, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    complex_samples = decode_single_fdbaq_packet(data, 1234)

    assert len(complex_samples) == 1234 * 2
    num_blocks = math.ceil(1234 / 128)
    sample_codes = [SampleCode(0, 1)] * 1234
    expected_vals = reconstruct_channel_vals(sample_codes, [0] * num_blocks, [63] * num_blocks, 1234)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=37, const_brc=0, const_thidx=2)
    data = create_synthetic_fdbaq_data(config, "1110")
    complex_samples = decode_single_fdbaq_packet(data, 37)

    assert len(complex_samples) == 37 * 2
    num_blocks = math.ceil(37 / 128)
    sample_codes = [SampleCode(1, 2)] * 37
    expected_vals = reconstruct_channel_vals(sample_codes, [0] * num_blocks, [2] * num_blocks, 37)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=55, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "1111")
    complex_samples = decode_single_fdbaq_packet(data, 55)

    assert len(complex_samples) == 55 * 2
    num_blocks = math.ceil(55 / 128)
    sample_codes = [SampleCode(1, 3)] * 55
    expected_vals = reconstruct_channel_vals(sample_codes, [0] * num_blocks, [0] * num_blocks, 55)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=123, const_brc=0, const_thidx=3)
    data = create_synthetic_fdbaq_data(config, "0111")
    complex_samples = decode_single_fdbaq_packet(data, 123)

    assert len(complex_samples) == 123 * 2
    num_blocks = math.ceil(123 / 128)
    sample_codes = [SampleCode(0, 3)] * 123
    expected_vals = reconstruct_channel_vals(sample_codes, [0] * num_blocks, [3] * num_blocks, 123)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_fdbaq_decoder_brc1() -> None:
    config = PacketConfig(num_quads=1234, const_brc=1, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    complex_samples = decode_single_fdbaq_packet(data, 1234)

    assert len(complex_samples) == 1234 * 2
    num_blocks = math.ceil(1234 / 128)
    sample_codes = [SampleCode(0, 0)] * 1234
    expected_vals = reconstruct_channel_vals(sample_codes, [1] * num_blocks, [0] * num_blocks, 1234)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=42, const_brc=1, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    complex_samples = decode_single_fdbaq_packet(data, 42)

    assert len(complex_samples) == 42 * 2
    num_blocks = math.ceil(42 / 128)
    sample_codes = [SampleCode(0, 1)] * 42
    expected_vals = reconstruct_channel_vals(sample_codes, [1] * num_blocks, [63] * num_blocks, 42)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=1, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "11111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 4)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [1] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=101, const_brc=1, const_thidx=101)
    data = create_synthetic_fdbaq_data(config, "01110")
    complex_samples = decode_single_fdbaq_packet(data, 101)

    assert len(complex_samples) == 101 * 2
    num_blocks = math.ceil(101 / 128)
    sample_codes = [SampleCode(0, 3)] * 101
    expected_vals = reconstruct_channel_vals(sample_codes, [1] * num_blocks, [101] * num_blocks, 101)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_fdbaq_decoder_brc2() -> None:
    config = PacketConfig(num_quads=1234, const_brc=2, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    complex_samples = decode_single_fdbaq_packet(data, 1234)

    assert len(complex_samples) == 1234 * 2
    num_blocks = math.ceil(1234 / 128)
    sample_codes = [SampleCode(0, 0)] * 1234
    expected_vals = reconstruct_channel_vals(sample_codes, [2] * num_blocks, [0] * num_blocks, 1234)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=42, const_brc=2, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "0111111")
    complex_samples = decode_single_fdbaq_packet(data, 42)

    assert len(complex_samples) == 42 * 2
    num_blocks = math.ceil(42 / 128)
    sample_codes = [SampleCode(0, 6)] * 42
    expected_vals = reconstruct_channel_vals(sample_codes, [2] * num_blocks, [63] * num_blocks, 42)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 6)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [2] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111110")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 5)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [2] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_fdbaq_decoder_brc3() -> None:
    config = PacketConfig(num_quads=1234, const_brc=3, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    complex_samples = decode_single_fdbaq_packet(data, 1234)

    assert len(complex_samples) == 1234 * 2
    num_blocks = math.ceil(1234 / 128)
    sample_codes = [SampleCode(0, 0)] * 1234
    expected_vals = reconstruct_channel_vals(sample_codes, [3] * num_blocks, [0] * num_blocks, 1234)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=42, const_brc=3, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "110")
    complex_samples = decode_single_fdbaq_packet(data, 42)

    assert len(complex_samples) == 42 * 2
    num_blocks = math.ceil(42 / 128)
    sample_codes = [SampleCode(1, 2)] * 42
    expected_vals = reconstruct_channel_vals(sample_codes, [3] * num_blocks, [63] * num_blocks, 42)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 9)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [3] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111110")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 8)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [3] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "011111111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(0, 9)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [3] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_fdbaq_decoder_brc4() -> None:
    config = PacketConfig(num_quads=1234, const_brc=4, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    complex_samples = decode_single_fdbaq_packet(data, 1234)

    assert len(complex_samples) == 1234 * 2
    num_blocks = math.ceil(1234 / 128)
    sample_codes = [SampleCode(0, 0)] * 1234
    expected_vals = reconstruct_channel_vals(sample_codes, [4] * num_blocks, [0] * num_blocks, 1234)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=42, const_brc=4, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "1100")
    complex_samples = decode_single_fdbaq_packet(data, 42)

    assert len(complex_samples) == 42 * 2
    num_blocks = math.ceil(42 / 128)
    sample_codes = [SampleCode(1, 3)] * 42
    expected_vals = reconstruct_channel_vals(sample_codes, [4] * num_blocks, [63] * num_blocks, 42)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 15)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [4] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111110")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(1, 14)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [4] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "0111111111")
    complex_samples = decode_single_fdbaq_packet(data, 99)

    assert len(complex_samples) == 99 * 2
    num_blocks = math.ceil(99 / 128)
    sample_codes = [SampleCode(0, 15)] * 99
    expected_vals = reconstruct_channel_vals(sample_codes, [4] * num_blocks, [11] * num_blocks, 99)
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_fdbaq_decoder_variable_brc() -> None:
    ie_bits = pack_bits(
        [
            "000",  # BRC 0
            "0111" * 128,  # 128 HCodes (sign 0, magnitude 3)
            "001",  # BRC 1
            "01111" * 128,  # 128 HCodes (sign 0, magnitude 4)
            "010",  # BRC 2
            "0111111" * 128,  # 128 HCodes (sign 0, magnitude 6)
            "011",  # BRC 3
            "011111111" * 128,  # 128 HCodes (sign 0, magnitude 9)
            "100",  # BRC 4
            "0111111111" * 128,  # 128 HCodes (sign 0, magnitude 15)
        ],
        pack_to_16_bits=True,
    )
    io_bits = pack_bits(
        [
            "0111" * 128,  # 128 HCodes (sign 0, magnitude 3)
            "01111" * 128,  # 128 HCodes (sign 0, magnitude 4)
            "0111111" * 128,  # 128 HCodes (sign 0, magnitude 6)
            "011111111" * 128,  # 128 HCodes (sign 0, magnitude 9)
            "0111111111" * 128,  # 128 HCodes (sign 0, magnitude 15)
        ],
        pack_to_16_bits=True,
    )
    qe_bits = pack_bits(
        [
            "00000000",  # THIDX 0
            "0111" * 128,  # 128 HCodes (sign 0, magnitude 3)
            "00000000",  # THIDX 0
            "01111" * 128,  # 128 HCodes (sign 0, magnitude 4)
            "00000000",  # THIDX 0
            "0111111" * 128,  # 128 HCodes (sign 0, magnitude 6)
            "00000000",  # THIDX 0
            "011111111" * 128,  # 128 HCodes (sign 0, magnitude 9)
            "00000000",  # THIDX 0
            "0111111111" * 128,  # 128 HCodes (sign 0, magnitude 15)
        ],
        pack_to_16_bits=True,
    )
    qo_bits = pack_bits(
        [
            "0111" * 128,  # 128 HCodes (sign 0, magnitude 3)
            "01111" * 128,  # 128 HCodes (sign 0, magnitude 4)
            "0111111" * 128,  # 128 HCodes (sign 0, magnitude 6)
            "011111111" * 128,  # 128 HCodes (sign 0, magnitude 9)
            "0111111111" * 128,  # 128 HCodes (sign 0, magnitude 15)
        ],
        pack_to_16_bits=True,
    )
    data = ie_bits + io_bits + qe_bits + qo_bits

    complex_samples = decode_single_fdbaq_packet(data, 128 * 5)

    # Check array properties
    assert len(complex_samples) == (128 * 5) * 2

    # Build expected array: each block has different BRC but same THIDX=0
    # All channels have same values, interleaved as IE+QE*j, IO+QO*j
    expected_vals_list = []  # type: ignore
    brcs = [0, 1, 2, 3, 4]
    mcodes = [3, 4, 6, 9, 15]
    for brc, mcode in zip(brcs, mcodes):
        sample_codes = [SampleCode(0, mcode)] * 128
        block_vals = reconstruct_channel_vals(sample_codes, [brc], [0], 128)
        expected_vals_list.extend(block_vals)

    # All channels (IE, IO, QE, QO) have the same values
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals_list, expected_vals_list)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals_list, expected_vals_list)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j
    assert_complex_arrays_close(complex_samples, expected_array, rtol=1e-5, atol=1e-6)


def test_batched_fdbaq_decoder_same_config() -> None:
    """Test batched decode with multiple packets of the same configuration."""
    # Create multiple packets with same config
    config = PacketConfig(num_quads=128, const_brc=1, const_thidx=5)
    num_packets = 5
    huffman_pattern = "010"

    # Generate multiple identical packets
    packet_data_list = [create_synthetic_fdbaq_data(config, huffman_pattern) for _ in range(num_packets)]

    # Decode using batched function
    batched_result = decode_batched_fdbaq_packets(packet_data_list, config.num_quads)

    # Check array properties
    assert isinstance(batched_result, np.ndarray)
    assert batched_result.dtype == np.complex64
    assert batched_result.shape == (num_packets, config.num_quads * 2)

    # Decode one packet individually for expected values
    single_result = decode_single_fdbaq_packet(packet_data_list[0], config.num_quads)

    # All packets should decode to the same result
    for i in range(num_packets):
        np.testing.assert_array_equal(
            batched_result[i], single_result, err_msg=f"Packet {i} should match single decode result"
        )

    # Verify expected values match reconstruction
    num_blocks = math.ceil(config.num_quads / 128)
    sample_codes = [SampleCode(0, 1)] * config.num_quads
    expected_vals = reconstruct_channel_vals(
        sample_codes, [config.const_brc] * num_blocks, [config.const_thidx] * num_blocks, config.num_quads
    )
    ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
    io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
    expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
    expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
    expected_array[1::2] = io_qo  # Odd indices: IO+QO*j

    assert_complex_arrays_close(batched_result[0], expected_array, rtol=1e-5, atol=1e-6)


def test_batched_fdbaq_decoder_different_configs() -> None:
    """Test batched decode with multiple packets of different configurations."""
    # The batched function expects all packets to have the same num_quads
    # So we test with packets that have the same num_quads but different BRC/THIDX/patterns
    num_quads = 128
    packet_configs_same_size = [
        PacketConfig(num_quads=num_quads, const_brc=0, const_thidx=0),
        PacketConfig(num_quads=num_quads, const_brc=1, const_thidx=5),
        PacketConfig(num_quads=num_quads, const_brc=2, const_thidx=10),
        PacketConfig(num_quads=num_quads, const_brc=3, const_thidx=20),
        PacketConfig(num_quads=num_quads, const_brc=4, const_thidx=30),
    ]

    huffman_patterns_same_size = [
        "00",  # BRC 0: sign=0, magnitude=0
        "010",  # BRC 1: sign=0, magnitude=1
        "0111111",  # BRC 2: sign=0, magnitude=6
        "111111111",  # BRC 3: sign=1, magnitude=9
        "1111111111",  # BRC 4: sign=1, magnitude=15
    ]

    # Map huffman patterns to their documented magnitudes
    pattern_to_magnitude = {
        "00": 0,
        "010": 1,
        "0111111": 6,
        "111111111": 9,
        "1111111111": 15,
    }

    # Create packet data for each configuration
    packet_data_list = []
    expected_results = []

    for config, huffman_pattern in zip(packet_configs_same_size, huffman_patterns_same_size):
        packet_data = create_synthetic_fdbaq_data(config, huffman_pattern)
        packet_data_list.append(packet_data)

        # Decode individually to get expected result
        single_result = decode_single_fdbaq_packet(packet_data, num_quads)
        expected_results.append(single_result)

    # Decode using batched function
    batched_result = decode_batched_fdbaq_packets(packet_data_list, num_quads)

    # Check array properties
    assert isinstance(batched_result, np.ndarray)
    assert batched_result.dtype == np.complex64
    assert batched_result.shape == (len(packet_configs_same_size), num_quads * 2)

    # Verify each packet decodes correctly
    for i, (packet_data, expected) in enumerate(zip(packet_data_list, expected_results)):
        # Batched result should match single decode
        try:
            assert_complex_arrays_close(batched_result[i], expected, rtol=1e-5, atol=1e-6)
        except AssertionError as e:
            # Add diagnostic information about packet ordering
            error_msg = [f"Packet {i} batched result should match single decode result: {e}"]
            error_msg.append("\nFirst 10 values of each packet (in returned order):")
            for j in range(len(packet_configs_same_size)):
                packet_vals = batched_result[j][:10]
                error_msg.append(f"  Packet {j}: {packet_vals}")
            error_msg.append("\nFirst 10 values of expected result for this packet:")
            error_msg.append(f"  Expected: {expected[:10]}")
            error_msg.append(f"  Actual:   {batched_result[i][:10]}")
            raise AssertionError("\n".join(error_msg)) from e

        # Verify expected values match reconstruction
        config = packet_configs_same_size[i]
        num_blocks = math.ceil(config.num_quads / 128)

        # Extract sign and magnitude from huffman pattern
        huffman_pattern = huffman_patterns_same_size[i]
        sign = int(huffman_pattern[0])
        magnitude = pattern_to_magnitude[huffman_pattern]

        sample_codes = [SampleCode(sign, magnitude)] * config.num_quads
        expected_vals = reconstruct_channel_vals(
            sample_codes, [config.const_brc] * num_blocks, [config.const_thidx] * num_blocks, config.num_quads
        )
        ie_qe = np.array([complex(ie, qe) for ie, qe in zip(expected_vals, expected_vals)], dtype=np.complex64)
        io_qo = np.array([complex(io, qo) for io, qo in zip(expected_vals, expected_vals)], dtype=np.complex64)
        expected_array = np.empty(len(ie_qe) * 2, dtype=np.complex64)
        expected_array[0::2] = ie_qe  # Even indices: IE+QE*j
        expected_array[1::2] = io_qo  # Odd indices: IO+QO*j

        try:
            assert_complex_arrays_close(batched_result[i], expected_array, rtol=1e-5, atol=1e-6)
        except AssertionError as e:
            # Add diagnostic information about packet ordering
            error_msg = [f"Packet {i} should match expected reconstructed values: {e}"]
            error_msg.append("\nFirst 10 values of each packet (in returned order):")
            for j in range(len(packet_configs_same_size)):
                packet_vals = batched_result[j][:10]
                error_msg.append(f"  Packet {j}: {packet_vals}")
            error_msg.append("\nFirst 10 values of expected reconstructed result for this packet:")
            error_msg.append(f"  Expected: {expected_array[:10]}")
            error_msg.append(f"  Actual:   {batched_result[i][:10]}")
            raise AssertionError("\n".join(error_msg)) from e
