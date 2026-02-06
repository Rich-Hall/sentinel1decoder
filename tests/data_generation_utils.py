import struct
from dataclasses import dataclass
from math import ceil
from typing import List, Union


@dataclass
class PacketConfig:
    """Configuration for synthetic packet generation"""

    # Primary Header Fields (6 bytes)
    packet_version: int = 0  # 3 bits
    packet_type: int = 0  # 1 bit
    secondary_header_flag: int = 1  # 1 bit
    process_id: int = 0b1000001  # 7 bits
    packet_category: int = 12  # 4 bits
    sequence_flags: int = 3  # 2 bits
    packet_sequence: int = 0  # 14 bits
    # Packet data length varies depending on what's in the packet (2 bytes)

    # Secondary Header Fields (62 bytes)
    # Datation Service (6 bytes)
    coarse_time: int = 0  # 4 bytes
    fine_time: int = 0  # 2 bytes

    # Fixed Ancillary Data (14 bytes)
    # sync marker is fixed at 0x352EF853 (4 bytes)
    data_take_id: int = 1  # 4 bytes
    ecc_number: int = 0  # 1 byte
    test_mode: int = 0  # 3 bits
    rx_channel_id: int = 0  # 4 bits
    instrument_config_id: int = 0  # 4 bytes

    # Sub-commutated Ancillary Data (3 bytes)
    subcom_data_word_ind: int = 0  # 1 byte
    subcom_data_word: int = 0  # 2 bytes

    # Counters Service (8 bytes)
    space_packet_count: int = 0  # 4 bytes
    pri_count: int = 0  # 4 bytes

    # Radar Configuration (27 bytes)
    error_flag: int = 0  # 1 bit
    baq_mode: int = 12  # 5 bits
    baq_block_length: int = 128  # 1 byte
    # One unused byte here
    range_decimation: int = 0  # 1 byte
    rx_gain: int = 0  # 1 byte
    txprr: int = 0  # 2 bytes
    txpsf: int = 0  # 2 bytes
    tx_pulse_length: int = 0  # 3 bytes
    rank: int = 0  # 5 bits
    pri: int = 1000  # 3 bytes
    sampling_window_start_time: int = 0  # 3 bytes
    sampling_window_length: int = 0  # 3 bytes
    sas_ssbflag: int = 0  # 1 bit
    polarisation: int = 0  # 3 bits
    temperature_comp: int = 0  # 2 bits
    calibration_mode: int = 0  # 2 bits
    tx_pulse_number: int = 1  # 5 bits
    signal_type: int = 0  # 4 bits
    swap_flag: int = 0  # 1 bit
    swath_num: int = 1  # 1 byte

    # Number of quads (2 bytes)
    num_quads: int = 128

    # Additional fields for data generation (not part of headers)
    const_brc: int = 0
    const_thidx: int = 0


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


def pack_bits(bit_strings: List[str], pack_to_16_bits: bool = False) -> bytes:
    """Pack a list of binary strings into bytes."""
    all_bits = "".join(bit_strings)
    if pack_to_16_bits:
        padding = (16 - len(all_bits) % 16) % 16
    else:
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
    assert first_word < 0x10000, f"First word exceeds 16 bits: {first_word:#x}"

    # Second 16 bits: sequence_flags(2) + packet_sequence(14)
    second_word = (config.sequence_flags << 14) | (config.packet_sequence & 0x3FFF)
    assert second_word < 0x10000, f"Second word exceeds 16 bits: {second_word:#x}"

    # Third 16 bits: packet data length - 1
    third_word = data_length - 1
    assert third_word < 0x10000, f"Third word exceeds 16 bits: {third_word:#x}"

    return struct.pack(">HHH", first_word, second_word, third_word)


def create_secondary_header(config: PacketConfig) -> bytes:
    """Create 62-byte secondary header"""
    header = bytearray(62)

    # Datation Service (6 bytes)
    struct.pack_into(">I", header, 0, config.coarse_time)
    struct.pack_into(">H", header, 4, config.fine_time)

    # Fixed Ancillary Data (14 bytes)
    struct.pack_into(">I", header, 6, 0x352EF853)  # Sync marker
    struct.pack_into(">I", header, 10, config.data_take_id)
    header[14] = config.ecc_number
    header[15] = ((config.test_mode & 0x07) << 4) | (config.rx_channel_id & 0x0F)
    struct.pack_into(">I", header, 16, config.instrument_config_id)

    # Sub-commutated Ancillary Data (3 bytes)
    header[20] = config.subcom_data_word_ind
    struct.pack_into(">H", header, 21, config.subcom_data_word)

    # Counters Service (8 bytes)
    struct.pack_into(">I", header, 23, config.space_packet_count)
    struct.pack_into(">I", header, 27, config.pri_count)

    # Radar Configuration (27 bytes)
    header[31] = ((config.error_flag & 0x1) << 7) | (config.baq_mode & 0x1F)
    header[32] = config.baq_block_length
    # header[33] is unused
    header[34] = config.range_decimation
    header[35] = config.rx_gain
    struct.pack_into(">H", header, 36, config.txprr)
    struct.pack_into(">H", header, 38, config.txpsf)
    header[40:43] = config.tx_pulse_length.to_bytes(3, "big")
    header[43] = config.rank & 0x1F
    header[44:47] = config.pri.to_bytes(3, "big")
    header[47:50] = config.sampling_window_start_time.to_bytes(3, "big")
    header[50:53] = config.sampling_window_length.to_bytes(3, "big")
    header[53] = (
        ((config.sas_ssbflag & 0x1) << 7)
        | ((config.polarisation & 0x07) << 4)
        | ((config.temperature_comp & 0x03) << 2)
    )
    # header[54-55] contain SAS SSB message (implementation depends on sas_ssbflag)
    header[56] = ((config.calibration_mode & 0x03) << 6) | (config.tx_pulse_number & 0x1F)
    header[57] = ((config.signal_type & 0x0F) << 4) | (config.swap_flag & 0x01)
    header[58] = config.swath_num

    # Number of quads (2 bytes, near end of header)
    struct.pack_into(">H", header, 59, config.num_quads)

    return bytes(header)


def _create_synthetic_fdbaq_block_group(
    config: PacketConfig,
    huffman_pattern: str,
    write_brc: bool = False,
    write_thidx: bool = False,
) -> bytes:
    """Create a synthetic FDBAQ block group"""
    all_bit_strings = []

    num_blocks = ceil(config.num_quads / 128)

    if write_brc:
        block_prefix = format(config.const_brc, "03b")
    elif write_thidx:
        block_prefix = format(config.const_thidx, "08b")
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


def create_synthetic_fdbaq_data(config: PacketConfig, huffman_pattern: str) -> bytes:
    """Create synthetic FDBAQ compressed data"""

    ie = _create_synthetic_fdbaq_block_group(config, huffman_pattern, write_brc=True)
    io = _create_synthetic_fdbaq_block_group(config, huffman_pattern)
    qe = _create_synthetic_fdbaq_block_group(config, huffman_pattern, write_thidx=True)
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


def create_synthetic_level0_packet(
    config: PacketConfig,
    const_value: Union[int, str] = 0,
    *,
    include_secondary: bool = True,
) -> bytes:
    """Create synthetic level 0 packet bytes.

    A level0 packet consists of a primary header, an optional secondary header,
    and an optional data section. When include_secondary is False (for testing
    packets without a secondary header), the packet data field is 62 zero bytes.
    When True, the packet has a secondary header and a data section (bypass or
    FDBAQ). Use num_quads=1 and baq_mode=0 for a minimal payload when only
    header decoding is needed.
    """
    if not include_secondary:
        return create_primary_header(config, 62) + b"\x00" * 62

    if config.baq_mode == 0 and isinstance(const_value, int):
        data_section = create_synthetic_bypass_data(config, const_value)
    elif config.baq_mode in [11, 12, 13] and isinstance(const_value, str):
        data_section = create_synthetic_fdbaq_data(config, const_value)
    else:
        raise ValueError(f"Unsupported BAQ mode: {config.baq_mode} with const_value: {const_value}")

    # Packet data field = secondary header (62) + user data
    packet_data_len = 62 + len(data_section)
    primary_header = create_primary_header(config, packet_data_len)
    secondary_header = create_secondary_header(config)

    return primary_header + secondary_header + data_section
