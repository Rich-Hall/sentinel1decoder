from sentinel1decoder._fdbaq_decoder import FDBAQDecoder
from sentinel1decoder._sample_code import SampleCode

from .data_generation_utils import PacketConfig, create_synthetic_fdbaq_data, pack_bits


def test_fdbaq_decoder_brc0() -> None:
    config = PacketConfig(num_quads=128, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    decoder = FDBAQDecoder(data, 128)
    assert decoder.s_ie == [SampleCode(0, 0)] * 128
    assert decoder.s_io == [SampleCode(0, 0)] * 128
    assert decoder.s_qe == [SampleCode(0, 0)] * 128
    assert decoder.s_qo == [SampleCode(0, 0)] * 128

    config = PacketConfig(num_quads=1234, const_brc=0, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    decoder = FDBAQDecoder(data, 1234)
    assert decoder.s_ie == [SampleCode(0, 1)] * 1234
    assert decoder.s_io == [SampleCode(0, 1)] * 1234
    assert decoder.s_qe == [SampleCode(0, 1)] * 1234
    assert decoder.s_qo == [SampleCode(0, 1)] * 1234

    config = PacketConfig(num_quads=37, const_brc=0, const_thidx=2)
    data = create_synthetic_fdbaq_data(config, "1110")
    decoder = FDBAQDecoder(data, 37)
    assert decoder.s_ie == [SampleCode(1, 2)] * 37
    assert decoder.s_io == [SampleCode(1, 2)] * 37
    assert decoder.s_qe == [SampleCode(1, 2)] * 37
    assert decoder.s_qo == [SampleCode(1, 2)] * 37

    config = PacketConfig(num_quads=55, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "1111")
    decoder = FDBAQDecoder(data, 55)
    assert decoder.s_ie == [SampleCode(1, 3)] * 55
    assert decoder.s_io == [SampleCode(1, 3)] * 55
    assert decoder.s_qe == [SampleCode(1, 3)] * 55
    assert decoder.s_qo == [SampleCode(1, 3)] * 55

    config = PacketConfig(num_quads=123, const_brc=0, const_thidx=3)
    data = create_synthetic_fdbaq_data(config, "0111")
    decoder = FDBAQDecoder(data, 123)
    assert decoder.s_ie == [SampleCode(0, 3)] * 123
    assert decoder.s_io == [SampleCode(0, 3)] * 123
    assert decoder.s_qe == [SampleCode(0, 3)] * 123
    assert decoder.s_qo == [SampleCode(0, 3)] * 123


def test_fdbaq_decoder_brc1() -> None:
    config = PacketConfig(num_quads=1234, const_brc=1, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    decoder = FDBAQDecoder(data, 1234)
    assert decoder.s_ie == [SampleCode(0, 0)] * 1234
    assert decoder.s_io == [SampleCode(0, 0)] * 1234
    assert decoder.s_qe == [SampleCode(0, 0)] * 1234
    assert decoder.s_qo == [SampleCode(0, 0)] * 1234

    config = PacketConfig(num_quads=42, const_brc=1, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    decoder = FDBAQDecoder(data, 42)
    assert decoder.s_ie == [SampleCode(0, 1)] * 42
    assert decoder.s_io == [SampleCode(0, 1)] * 42
    assert decoder.s_qe == [SampleCode(0, 1)] * 42
    assert decoder.s_qo == [SampleCode(0, 1)] * 42

    config = PacketConfig(num_quads=99, const_brc=1, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "11111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 4)] * 99
    assert decoder.s_io == [SampleCode(1, 4)] * 99
    assert decoder.s_qe == [SampleCode(1, 4)] * 99
    assert decoder.s_qo == [SampleCode(1, 4)] * 99

    config = PacketConfig(num_quads=101, const_brc=1, const_thidx=101)
    data = create_synthetic_fdbaq_data(config, "01110")
    decoder = FDBAQDecoder(data, 101)
    assert decoder.s_ie == [SampleCode(0, 3)] * 101
    assert decoder.s_io == [SampleCode(0, 3)] * 101
    assert decoder.s_qe == [SampleCode(0, 3)] * 101
    assert decoder.s_qo == [SampleCode(0, 3)] * 101


def test_fdbaq_decoder_brc2() -> None:
    config = PacketConfig(num_quads=1234, const_brc=2, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    decoder = FDBAQDecoder(data, 1234)
    assert decoder.s_ie == [SampleCode(0, 0)] * 1234
    assert decoder.s_io == [SampleCode(0, 0)] * 1234
    assert decoder.s_qe == [SampleCode(0, 0)] * 1234
    assert decoder.s_qo == [SampleCode(0, 0)] * 1234

    config = PacketConfig(num_quads=42, const_brc=2, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "0111111")
    decoder = FDBAQDecoder(data, 42)
    assert decoder.s_ie == [SampleCode(0, 6)] * 42
    assert decoder.s_io == [SampleCode(0, 6)] * 42
    assert decoder.s_qe == [SampleCode(0, 6)] * 42
    assert decoder.s_qo == [SampleCode(0, 6)] * 42

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 6)] * 99
    assert decoder.s_io == [SampleCode(1, 6)] * 99
    assert decoder.s_qe == [SampleCode(1, 6)] * 99
    assert decoder.s_qo == [SampleCode(1, 6)] * 99

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111110")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 5)] * 99
    assert decoder.s_io == [SampleCode(1, 5)] * 99
    assert decoder.s_qe == [SampleCode(1, 5)] * 99
    assert decoder.s_qo == [SampleCode(1, 5)] * 99


def test_fdbaq_decoder_brc3() -> None:
    config = PacketConfig(num_quads=1234, const_brc=3, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    decoder = FDBAQDecoder(data, 1234)
    assert decoder.s_ie == [SampleCode(0, 0)] * 1234
    assert decoder.s_io == [SampleCode(0, 0)] * 1234
    assert decoder.s_qe == [SampleCode(0, 0)] * 1234
    assert decoder.s_qo == [SampleCode(0, 0)] * 1234

    config = PacketConfig(num_quads=42, const_brc=3, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "110")
    decoder = FDBAQDecoder(data, 42)
    assert decoder.s_ie == [SampleCode(1, 2)] * 42
    assert decoder.s_io == [SampleCode(1, 2)] * 42
    assert decoder.s_qe == [SampleCode(1, 2)] * 42
    assert decoder.s_qo == [SampleCode(1, 2)] * 42

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 9)] * 99
    assert decoder.s_io == [SampleCode(1, 9)] * 99
    assert decoder.s_qe == [SampleCode(1, 9)] * 99
    assert decoder.s_qo == [SampleCode(1, 9)] * 99

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111110")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 8)] * 99
    assert decoder.s_io == [SampleCode(1, 8)] * 99
    assert decoder.s_qe == [SampleCode(1, 8)] * 99
    assert decoder.s_qo == [SampleCode(1, 8)] * 99

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "011111111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(0, 9)] * 99
    assert decoder.s_io == [SampleCode(0, 9)] * 99
    assert decoder.s_qe == [SampleCode(0, 9)] * 99
    assert decoder.s_qo == [SampleCode(0, 9)] * 99


def test_fdbaq_decoder_brc4() -> None:
    config = PacketConfig(num_quads=1234, const_brc=4, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    decoder = FDBAQDecoder(data, 1234)
    assert decoder.s_ie == [SampleCode(0, 0)] * 1234
    assert decoder.s_io == [SampleCode(0, 0)] * 1234
    assert decoder.s_qe == [SampleCode(0, 0)] * 1234
    assert decoder.s_qo == [SampleCode(0, 0)] * 1234

    config = PacketConfig(num_quads=42, const_brc=4, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "1100")
    decoder = FDBAQDecoder(data, 42)
    assert decoder.s_ie == [SampleCode(1, 3)] * 42
    assert decoder.s_io == [SampleCode(1, 3)] * 42
    assert decoder.s_qe == [SampleCode(1, 3)] * 42
    assert decoder.s_qo == [SampleCode(1, 3)] * 42

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 15)] * 99
    assert decoder.s_io == [SampleCode(1, 15)] * 99
    assert decoder.s_qe == [SampleCode(1, 15)] * 99
    assert decoder.s_qo == [SampleCode(1, 15)] * 99

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111110")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(1, 14)] * 99
    assert decoder.s_io == [SampleCode(1, 14)] * 99
    assert decoder.s_qe == [SampleCode(1, 14)] * 99
    assert decoder.s_qo == [SampleCode(1, 14)] * 99

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "0111111111")
    decoder = FDBAQDecoder(data, 99)
    assert decoder.s_ie == [SampleCode(0, 15)] * 99
    assert decoder.s_io == [SampleCode(0, 15)] * 99
    assert decoder.s_qe == [SampleCode(0, 15)] * 99
    assert decoder.s_qo == [SampleCode(0, 15)] * 99


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
    expected = [
        *[SampleCode(0, 3)] * 128,
        *[SampleCode(0, 4)] * 128,
        *[SampleCode(0, 6)] * 128,
        *[SampleCode(0, 9)] * 128,
        *[SampleCode(0, 15)] * 128,
    ]
    decoder = FDBAQDecoder(data, 128 * 5)
    assert decoder.s_ie == expected
    assert decoder.s_io == expected
    assert decoder.s_qe == expected
    assert decoder.s_qo == expected
