import struct
from dataclasses import dataclass
from math import ceil
from typing import List, Optional


@dataclass
class PacketConfig:
    """Configuration for synthetic packet generation"""

    packet_version: int = 0
    packet_type: int = 0
    secondary_header_flag: int = 1
    process_id: int = 0b1000001
    packet_category: int = 12
    sequence_flags: int = 3
    packet_sequence: int = 0
    error_flag: int = 0
    baq_mode: int = 12  # FDBAQ
    baq_block_length: int = 128
    range_decimation: int = 0
    rx_gain: int = 0
    tx_pulse_number: int = 1
    rank: int = 0
    pri: int = 1000
    swath_num: int = 1
    num_quads: int = 128


def signed_int_to_ten_bit_unsigned(value: int) -> int:
    """
    Convert a standard signed int to a ten-bit unsigned int.

    The output format uses the first bit as sign (1 for negative)
    and the remaining 9 bits as magnitude.

    Args:
        value: Standard signed integer to convert.

    Returns:
        A ten-bit unsigned integer with sign-magnitude encoding
    """
    # Ensure value is within valid range for 9-bit magnitude
    if not -511 <= value <= 511:
        raise ValueError("Value must be between -511 and 511")

    # Get magnitude (absolute value) and mask to 9 bits
    magnitude = abs(value) & 0x1FF

    # Set sign bit (bit 9) if negative
    if value < 0:
        return magnitude | 0x200  # 0x200 is binary 1000000000
    return magnitude


def pack_bits(bit_strings: List[str]) -> bytes:
    """Pack a list of binary strings into bytes."""
    all_bits = "".join(bit_strings)
    padding = (8 - len(all_bits) % 8) % 8
    all_bits = all_bits + "0" * padding
    num_bytes = len(all_bits) // 8
    result = bytearray(num_bytes)
    for i in range(num_bytes):
        result[i] = int(all_bits[i * 8 : (i + 1) * 8], 2)
    return bytes(result)


def pack_10bit_samples(samples: List[int]) -> bytes:
    """Pack 10-bit samples into bytes.
    Creates a continuous bit stream where each sample occupies 10 bits.
    Multiple samples are packed together without gaps.
    Pads the final word to 16-bit boundary."""
    result = bytearray()
    current_word = 0
    bits_in_word = 0

    for sample in samples:
        # Ensure value is within 10-bit range
        sample = signed_int_to_ten_bit_unsigned(sample)

        # Add this 10-bit sample to current_word
        current_word = (current_word << 10) | sample
        bits_in_word += 10

        # When we have 16 bits or more, output bytes
        while bits_in_word >= 16:
            # Extract the top 16 bits
            two_bytes = (current_word >> (bits_in_word - 16)) & 0xFFFF
            result.extend(two_bytes.to_bytes(2, "big"))
            bits_in_word -= 16

        # Keep remaining bits for next iteration
        current_word &= (1 << bits_in_word) - 1

    # Handle any remaining bits by padding to 16-bit boundary
    if bits_in_word > 0:
        # Pad to next 16-bit boundary
        padding_bits = 16 - bits_in_word
        two_bytes = (current_word << padding_bits) & 0xFFFF
        result.extend(two_bytes.to_bytes(2, "big"))

    return bytes(result)


def create_primary_header(config: PacketConfig, data_length: int) -> bytes:
    """Create 6-byte primary header"""
    # First 16 bits: version(3) + type(1) + secondary_flag(1) + process_id(7) + category(4)
    first_word = (
        (config.packet_version << 13)
        | (config.packet_type << 12)
        | (config.secondary_header_flag << 11)
        | (config.process_id << 4)
        | config.packet_category
    )

    # Second 16 bits: sequence_flags(2) + packet_sequence(14)
    second_word = (config.sequence_flags << 14) | (config.packet_sequence & 0x3FFF)

    # Third 16 bits: packet data length - 1
    third_word = data_length - 1

    return struct.pack(">HHH", first_word, second_word, third_word)


def create_secondary_header(
    config: PacketConfig, coarse_time: int, fine_time: int
) -> bytes:
    """Create 62-byte secondary header"""
    header = bytearray(62)

    # Coarse time (4 bytes)
    struct.pack_into(">I", header, 0, coarse_time)

    # Fine time (2 bytes)
    struct.pack_into(">H", header, 4, fine_time)

    # Sync marker (4 bytes)
    struct.pack_into(">I", header, 6, 0x352EF853)

    # Data take ID (4 bytes)
    struct.pack_into(">I", header, 10, 1)

    # ECC number (2 bytes)
    struct.pack_into(">H", header, 14, 0)

    # Various 1-byte fields
    header[16] = config.error_flag
    header[20] = config.baq_mode
    header[21] = config.baq_block_length
    header[22] = config.range_decimation
    header[23] = config.rx_gain
    header[32] = config.rank
    header[45] = config.swath_num

    # Number of quads (2 bytes, near end of header)
    struct.pack_into(">H", header, 59, config.num_quads)

    return bytes(header)


def _create_synthetic_fdbaq_block_group(
    config: PacketConfig,
    huffman_pattern: str,
    brc: Optional[int] = None,
    thidx: Optional[int] = None,
) -> bytes:
    """Create a synthetic FDBAQ block group"""
    all_bit_strings = []

    num_blocks = ceil(config.num_quads / 128)

    if brc is not None:
        block_prefix = format(brc, "03b")
    elif thidx is not None:
        block_prefix = format(thidx, "08b")
    else:
        block_prefix = ""

    for block_idx in range(num_blocks):
        if block_prefix:
            all_bit_strings.append(block_prefix)
        patterns_left = config.num_quads - (block_idx * 128)
        patterns_this_block = min(128, patterns_left)
        all_bit_strings.extend([huffman_pattern] * patterns_this_block)

    # Pack all bits together
    block_group = bytearray(pack_bits(all_bit_strings))

    # Pad to 16-bit boundary if needed
    if len(block_group) % 2 != 0:
        block_group.extend(b"\x00")

    return bytes(block_group)


def create_synthetic_fdbaq_data(
    config: PacketConfig, huffman_pattern: str, brc: int, thidx: int
) -> bytes:
    """Create synthetic FDBAQ compressed data"""

    ie = _create_synthetic_fdbaq_block_group(config, huffman_pattern, brc)
    io = _create_synthetic_fdbaq_block_group(config, huffman_pattern)
    qe = _create_synthetic_fdbaq_block_group(config, huffman_pattern, thidx)
    qo = _create_synthetic_fdbaq_block_group(config, huffman_pattern)

    return ie + io + qe + qo


def create_synthetic_bypass_data(config: PacketConfig, const_value: int = 0) -> bytes:
    """Create synthetic bypass mode (BAQ=0) data"""
    # In bypass mode, we just need to create 10-bit samples
    ie_samples = [const_value] * config.num_quads
    io_samples = [const_value] * config.num_quads
    qe_samples = [const_value] * config.num_quads
    qo_samples = [const_value] * config.num_quads

    ie_data = pack_10bit_samples(ie_samples)
    io_data = pack_10bit_samples(io_samples)
    qe_data = pack_10bit_samples(qe_samples)
    qo_data = pack_10bit_samples(qo_samples)

    return ie_data + io_data + qe_data + qo_data
