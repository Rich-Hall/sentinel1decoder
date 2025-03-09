import pytest

from .data_generation_utils import (
    PacketConfig,
    create_primary_header,
    create_secondary_header,
    create_synthetic_bypass_data,
    create_synthetic_fdbaq_data,
    pack_10bit_samples,
    pack_bits,
)


@pytest.fixture  # type: ignore
def single_quad_packet_config() -> PacketConfig:
    return PacketConfig(num_quads=1)


@pytest.fixture  # type: ignore
def two_quad_packet_config() -> PacketConfig:
    return PacketConfig(num_quads=2)


@pytest.fixture  # type: ignore
def default_packet_config() -> PacketConfig:
    return PacketConfig()


def test_pack_bits() -> None:
    # Basic case
    data = ["0"] * 8
    expected = (0b00000000).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Different length strings
    data = ["0", "00", "000", "0", "0"]
    expected = (0b00000000).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # One string only
    data = ["00000000"]
    expected = (0b00000000).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Basic case 2
    data = ["1"] * 8
    expected = (0b11111111).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Basic case 3
    data = ["1010"] * 2
    expected = (0b10101010).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Padding required
    data = ["0"]
    expected = (0b00000000).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Padding required 2
    data = ["1"]
    expected = (0b10000000).to_bytes(1, "big")
    assert pack_bits(data) == expected

    # Complex case: 1000001001000000 in binary = 32840 in decimal = 0x8240 in hex
    data = ["1", "00000", "10", "01"]
    expected = (0b1000001001000000).to_bytes(2, "big")
    assert pack_bits(data) == expected


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


def test_create_primary_header(default_packet_config: PacketConfig) -> None:
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


def test_create_secondary_header(default_packet_config: PacketConfig) -> None:
    coarse_time = 1
    fine_time = 1
    header = create_secondary_header(default_packet_config, coarse_time, fine_time)
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


def test_create_synthetic_fdbaq_data(
    single_quad_packet_config: PacketConfig, two_quad_packet_config: PacketConfig
) -> None:
    # All zeros
    huffman_pattern = "0"
    brc = 0
    thidx = 0
    data = create_synthetic_fdbaq_data(
        single_quad_packet_config, huffman_pattern, brc, thidx
    )
    ie = pack_bits(["000", "0", "000000000000"])
    io = pack_bits(["0", "000000000000000"])
    qe = pack_bits(["00000000", "0", "0000000"])
    qo = pack_bits(["0", "000000000000000"])
    expected = ie + io + qe + qo
    assert data == expected

    # Test normal case
    huffman_pattern = "1010"
    brc = 2
    thidx = 128
    data = create_synthetic_fdbaq_data(
        single_quad_packet_config, huffman_pattern, brc, thidx
    )
    ie = pack_bits(["010", "1010", "000000000"])
    io = pack_bits(["1010", "000000000000"])
    qe = pack_bits(["10000000", "1010", "0000"])
    qo = pack_bits(["1010", "000000000000"])
    expected = ie + io + qe + qo
    assert data == expected

    # Test normal case 2
    huffman_pattern = "1010"
    brc = 2
    thidx = 128
    data = create_synthetic_fdbaq_data(
        two_quad_packet_config, huffman_pattern, brc, thidx
    )
    ie = pack_bits(["010", "1010", "1010", "00000"])
    io = pack_bits(["1010", "1010", "00000000"])
    qe = pack_bits(["10000000", "1010", "1010"])
    qo = pack_bits(["1010", "1010", "00000000"])
    expected = ie + io + qe + qo
    assert data == expected


def test_create_synthetic_fdbaq_data_word_boundary(
    single_quad_packet_config: PacketConfig, two_quad_packet_config: PacketConfig
) -> None:
    # Test word boundary case, single quad
    huffman_pattern = "111111111"  # Nine 1s
    brc = 2
    thidx = 128
    data = create_synthetic_fdbaq_data(
        single_quad_packet_config, huffman_pattern, brc, thidx
    )
    ie = pack_bits(["010", "111111111", "0000"])  # One 16-bit word
    io = pack_bits(["111111111", "0000000"])  # One 16-bit word
    qe = pack_bits(["10000000", "111111111", "000000000000000"])  # Two 16-bit words
    qo = pack_bits(["111111111", "0000000"])  # One 16-bit word
    expected = ie + io + qe + qo
    assert data == expected

    # Test word boundary case 2, two quad
    huffman_pattern = "11111111"  # Eight 1s
    brc = 2
    thidx = 128
    data = create_synthetic_fdbaq_data(
        two_quad_packet_config, huffman_pattern, brc, thidx
    )
    ie = pack_bits(["010", "11111111", "11111111", "0000000000000"])  # Two 16-bit words
    io = pack_bits(["11111111", "11111111"])  # One 16-bit word
    qe = pack_bits(["10000000", "11111111", "11111111", "00000000"])  # Two 16-bit words
    qo = pack_bits(["11111111", "11111111"])  # One 16-bit word
    expected = ie + io + qe + qo
    assert data == expected


def test_create_synthetic_bypass_data(
    single_quad_packet_config: PacketConfig, two_quad_packet_config: PacketConfig
) -> None:
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
