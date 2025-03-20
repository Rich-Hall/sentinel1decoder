from .data_generation_utils import (
    PacketConfig,
    create_primary_header,
    create_secondary_header,
    create_synthetic_bypass_data,
    create_synthetic_fdbaq_data,
    create_synthetic_level0_packet,
    pack_10bit_samples,
    pack_bits,
)


def test_pack_bits() -> None:
    # Basic case
    data = ["0"] * 8
    expected = (0b00000000).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Different length strings
    data = ["0", "00", "000", "0", "0"]
    expected = (0b00000000).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # One string only
    data = ["00000000"]
    expected = (0b00000000).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Basic case 2
    data = ["1"] * 8
    expected = (0b11111111).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Basic case 3
    data = ["1010"] * 2
    expected = (0b10101010).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Padding required
    data = ["0"]
    expected = (0b00000000).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Padding required 2
    data = ["1"]
    expected = (0b10000000).to_bytes(1, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 1
    assert packed_data == expected

    # Complex case: 1000001001000000 in binary = 32840 in decimal = 0x8240 in hex
    data = ["1", "00000", "10", "01"]
    expected = (0b1000001001000000).to_bytes(2, "big")
    packed_data = pack_bits(data)
    assert len(packed_data) == 2
    assert packed_data == expected


def test_pack_10bit_samples() -> None:
    samples = [0, 1, 2, 3, 4, 5]
    result = pack_10bit_samples(samples)
    expected = pack_bits(
        [
            "0000000000",
            "0000000001",
            "0000000010",
            "0000000011",
            "0000000100",
            "0000000101",
        ]
    )
    assert result == expected

    samples = [-511, 511, -188, 341]
    result = pack_10bit_samples(samples)
    expected = pack_bits(
        ["1111111111", "0111111111", "1010111100", "0101010101", "00000000"]
    )
    assert result == expected


def test_create_primary_header() -> None:
    default_packet_config = PacketConfig()
    data_length = 1
    header = create_primary_header(default_packet_config, data_length)
    assert len(header) == 6

    # First 16 bits: version(3) + type(1) + secondary_flag(1) + process_id(7) + category(4)
    assert header[0] == 0b00001100
    assert header[1] == 0b00011100

    # Second 16 bit word is sequence flags (2) + packet sequence (14)
    assert header[2] == 0b11000000
    assert header[3] == 0b00000000

    # Third 16 bit word is data length - 1
    assert header[4] == 0b00000000
    assert header[5] == 0b00000000

    data_length = 256
    header = create_primary_header(default_packet_config, data_length)
    assert header[4] == 0b00000000
    assert header[5] == 0b11111111


def test_create_secondary_header() -> None:
    packet_config = PacketConfig(coarse_time=1, fine_time=1)
    header = create_secondary_header(packet_config)
    assert len(header) == 62

    # Coarse time (4 bytes)
    assert header[0] == 0b00000000
    assert header[1] == 0b00000000
    assert header[2] == 0b00000000
    assert header[3] == 0b00000001

    # Fine time (2 bytes)
    assert header[4] == 0b00000000
    assert header[5] == 0b00000001

    # Sync marker (4 bytes)
    assert header[6:10] == (0x352EF853).to_bytes(4, "big")


def test_create_synthetic_fdbaq_data() -> None:
    single_quad_packet_config = PacketConfig(num_quads=1, const_brc=0, const_thidx=0)
    # All zeros
    huffman_pattern = "0"
    data = create_synthetic_fdbaq_data(single_quad_packet_config, huffman_pattern)
    ie = pack_bits(["000", "0", "000000000000"])
    io = pack_bits(["0", "000000000000000"])
    qe = pack_bits(["00000000", "0", "0000000"])
    qo = pack_bits(["0", "000000000000000"])
    expected = ie + io + qe + qo
    assert data == expected

    # Test normal case
    single_quad_packet_config = PacketConfig(num_quads=1, const_brc=2, const_thidx=128)
    huffman_pattern = "1010"
    data = create_synthetic_fdbaq_data(single_quad_packet_config, huffman_pattern)
    ie = pack_bits(["010", "1010", "000000000"])
    io = pack_bits(["1010", "000000000000"])
    qe = pack_bits(["10000000", "1010", "0000"])
    qo = pack_bits(["1010", "000000000000"])
    expected = ie + io + qe + qo
    assert data == expected

    # Test normal case 2
    two_quad_packet_config = PacketConfig(num_quads=2, const_brc=2, const_thidx=128)
    huffman_pattern = "1010"
    data = create_synthetic_fdbaq_data(two_quad_packet_config, huffman_pattern)
    ie = pack_bits(["010", "1010", "1010", "00000"])
    io = pack_bits(["1010", "1010", "00000000"])
    qe = pack_bits(["10000000", "1010", "1010"])
    qo = pack_bits(["1010", "1010", "00000000"])
    expected = ie + io + qe + qo
    assert data == expected


def test_create_synthetic_fdbaq_data_word_boundary() -> None:
    # Test word boundary case, single quad
    single_quad_packet_config = PacketConfig(num_quads=1, const_brc=2, const_thidx=128)
    huffman_pattern = "111111111"  # Nine 1s
    data = create_synthetic_fdbaq_data(single_quad_packet_config, huffman_pattern)
    ie = pack_bits(["010", "111111111", "0000"])  # One 16-bit word
    io = pack_bits(["111111111", "0000000"])  # One 16-bit word
    qe = pack_bits(["10000000", "111111111", "000000000000000"])  # Two 16-bit words
    qo = pack_bits(["111111111", "0000000"])  # One 16-bit word
    expected = ie + io + qe + qo
    assert data == expected

    # Test word boundary case 2, two quad
    two_quad_packet_config = PacketConfig(num_quads=2, const_brc=2, const_thidx=128)
    huffman_pattern = "11111111"  # Eight 1s
    data = create_synthetic_fdbaq_data(two_quad_packet_config, huffman_pattern)
    ie = pack_bits(["010", "11111111", "11111111", "0000000000000"])  # Two 16-bit words
    io = pack_bits(["11111111", "11111111"])  # One 16-bit word
    qe = pack_bits(["10000000", "11111111", "11111111", "00000000"])  # Two 16-bit words
    qo = pack_bits(["11111111", "11111111"])  # One 16-bit word
    expected = ie + io + qe + qo
    assert data == expected


def test_create_synthetic_bypass_data() -> None:
    single_quad_packet_config = PacketConfig(num_quads=1, const_brc=0, const_thidx=0)
    data = create_synthetic_bypass_data(single_quad_packet_config, 1)
    expected = pack_bits(
        [
            "0000000001",
            "000000",  # Padding to 16-bit word
            "0000000001",
            "000000",  # Padding to 16-bit word
            "0000000001",
            "000000",  # Padding to 16-bit word
            "0000000001",
            "000000",  # Padding to 16-bit word
        ]
    )
    assert data == expected

    two_quad_packet_config = PacketConfig(num_quads=2, const_brc=0, const_thidx=0)
    data = create_synthetic_bypass_data(two_quad_packet_config, 3)
    expected = pack_bits(
        [
            "0000000011",
            "0000000011",
            "000000000000",  # Padding to 16-bit word
            "0000000011",
            "0000000011",
            "000000000000",  # Padding to 16-bit word
            "0000000011",
            "0000000011",
            "000000000000",  # Padding to 16-bit word
            "0000000011",
            "0000000011",
            "000000000000",  # Padding to 16-bit word
        ]
    )
    assert data == expected


def test_create_synthetic_level0_packet_bypass() -> None:

    # Data contains four sets of 128 10-bit samples, each set padded to 16-bit word boundaries
    # 128 10-bit samples = 1280 bits = 160 bytes, which is already a multiple of 16-bit word boundaries
    packet_config = PacketConfig(baq_mode=0, num_quads=128)
    data = create_synthetic_level0_packet(packet_config, 1)
    assert len(data) == 6 + 62 + (160 * 4)
    assert data[68:] == pack_bits(["0000000001"] * 128 * 4)

    # BAQ Mode
    assert data[37] & 0x1F == 0  # Byte 31 Bits 3-7


def test_create_synthetic_level0_packet_fdbaq() -> None:
    # Data contains four sets of 128 4-bit samples, each set padded to 16-bit word boundaries
    # The first set has an extra three bytes for the brc, and the third has an extra eight bytes for the thidx
    # 128 4-bit samples = 512 bits = 64 bytes, which is a multiple of 16-bits
    # The first and third round up to 66 bytes
    packet_config = PacketConfig(baq_mode=12, num_quads=128)
    data = create_synthetic_level0_packet(packet_config, "1010")
    assert len(data) == 6 + 62 + 66 + 64 + 66 + 64

    # BAQ Mode
    assert data[37] & 0x1F == 12  # Byte 31 Bits 3-7
