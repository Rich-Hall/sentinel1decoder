import math

from sentinel1decoder._sentinel1decoder import decode_fdbaq

from .data_generation_utils import PacketConfig, create_synthetic_fdbaq_data, pack_bits


def test_fdbaq_decoder_brc0() -> None:
    config = PacketConfig(num_quads=128, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 128)

    # Check BRCs and THIDXs
    assert brcs == [0]  # One BRC for one block
    assert thidxs == [0]  # One THIDX for one block

    # Check sample codes - should be (sign, magnitude) tuples
    expected_sample = (False, 0)  # sign=False (0), magnitude=0
    assert s_ie == [expected_sample] * 128
    assert s_io == [expected_sample] * 128
    assert s_qe == [expected_sample] * 128
    assert s_qo == [expected_sample] * 128

    config = PacketConfig(num_quads=1234, const_brc=0, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 1234)

    assert brcs == [0] * math.ceil(1234 / 128)
    assert thidxs == [63] * math.ceil(1234 / 128)
    expected_sample = (False, 1)  # sign=False (0), magnitude=1
    assert s_ie == [expected_sample] * 1234
    assert s_io == [expected_sample] * 1234
    assert s_qe == [expected_sample] * 1234
    assert s_qo == [expected_sample] * 1234

    config = PacketConfig(num_quads=37, const_brc=0, const_thidx=2)
    data = create_synthetic_fdbaq_data(config, "1110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 37)

    assert brcs == [0] * math.ceil(37 / 128)
    assert thidxs == [2] * math.ceil(37 / 128)
    expected_sample = (True, 2)  # sign=True (1), magnitude=2
    assert s_ie == [expected_sample] * 37
    assert s_io == [expected_sample] * 37
    assert s_qe == [expected_sample] * 37
    assert s_qo == [expected_sample] * 37

    config = PacketConfig(num_quads=55, const_brc=0, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "1111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 55)

    assert brcs == [0] * math.ceil(55 / 128)
    assert thidxs == [0] * math.ceil(55 / 128)
    expected_sample = (True, 3)  # sign=True (1), magnitude=3
    assert s_ie == [expected_sample] * 55
    assert s_io == [expected_sample] * 55
    assert s_qe == [expected_sample] * 55
    assert s_qo == [expected_sample] * 55

    config = PacketConfig(num_quads=123, const_brc=0, const_thidx=3)
    data = create_synthetic_fdbaq_data(config, "0111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 123)

    assert brcs == [0] * math.ceil(123 / 128)
    assert thidxs == [3] * math.ceil(123 / 128)
    expected_sample = (False, 3)  # sign=False (0), magnitude=3
    assert s_ie == [expected_sample] * 123
    assert s_io == [expected_sample] * 123
    assert s_qe == [expected_sample] * 123
    assert s_qo == [expected_sample] * 123


def test_fdbaq_decoder_brc1() -> None:
    config = PacketConfig(num_quads=1234, const_brc=1, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 1234)

    assert brcs == [1] * math.ceil(1234 / 128)
    assert thidxs == [0] * math.ceil(1234 / 128)
    expected_sample = (False, 0)
    assert s_ie == [expected_sample] * 1234
    assert s_io == [expected_sample] * 1234
    assert s_qe == [expected_sample] * 1234
    assert s_qo == [expected_sample] * 1234

    config = PacketConfig(num_quads=42, const_brc=1, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "010")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 42)

    assert brcs == [1] * math.ceil(42 / 128)
    assert thidxs == [63] * math.ceil(42 / 128)
    expected_sample = (False, 1)
    assert s_ie == [expected_sample] * 42
    assert s_io == [expected_sample] * 42
    assert s_qe == [expected_sample] * 42
    assert s_qo == [expected_sample] * 42

    config = PacketConfig(num_quads=99, const_brc=1, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "11111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [1] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 4)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=101, const_brc=1, const_thidx=101)
    data = create_synthetic_fdbaq_data(config, "01110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 101)

    assert brcs == [1] * math.ceil(101 / 128)
    assert thidxs == [101] * math.ceil(101 / 128)
    expected_sample = (False, 3)
    assert s_ie == [expected_sample] * 101
    assert s_io == [expected_sample] * 101
    assert s_qe == [expected_sample] * 101
    assert s_qo == [expected_sample] * 101


def test_fdbaq_decoder_brc2() -> None:
    config = PacketConfig(num_quads=1234, const_brc=2, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "00")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 1234)

    assert brcs == [2] * math.ceil(1234 / 128)
    assert thidxs == [0] * math.ceil(1234 / 128)
    expected_sample = (False, 0)
    assert s_ie == [expected_sample] * 1234
    assert s_io == [expected_sample] * 1234
    assert s_qe == [expected_sample] * 1234
    assert s_qo == [expected_sample] * 1234

    config = PacketConfig(num_quads=42, const_brc=2, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "0111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 42)

    assert brcs == [2] * math.ceil(42 / 128)
    assert thidxs == [63] * math.ceil(42 / 128)
    expected_sample = (False, 6)
    assert s_ie == [expected_sample] * 42
    assert s_io == [expected_sample] * 42
    assert s_qe == [expected_sample] * 42
    assert s_qo == [expected_sample] * 42

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [2] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 6)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=99, const_brc=2, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [2] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 5)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99


def test_fdbaq_decoder_brc3() -> None:
    config = PacketConfig(num_quads=1234, const_brc=3, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 1234)

    assert brcs == [3] * math.ceil(1234 / 128)
    assert thidxs == [0] * math.ceil(1234 / 128)
    expected_sample = (False, 0)
    assert s_ie == [expected_sample] * 1234
    assert s_io == [expected_sample] * 1234
    assert s_qe == [expected_sample] * 1234
    assert s_qo == [expected_sample] * 1234

    config = PacketConfig(num_quads=42, const_brc=3, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 42)

    assert brcs == [3] * math.ceil(42 / 128)
    assert thidxs == [63] * math.ceil(42 / 128)
    expected_sample = (True, 2)
    assert s_ie == [expected_sample] * 42
    assert s_io == [expected_sample] * 42
    assert s_qe == [expected_sample] * 42
    assert s_qo == [expected_sample] * 42

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [3] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 9)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "111111110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [3] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 8)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=99, const_brc=3, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "011111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [3] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (False, 9)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99


def test_fdbaq_decoder_brc4() -> None:
    config = PacketConfig(num_quads=1234, const_brc=4, const_thidx=0)
    data = create_synthetic_fdbaq_data(config, "000")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 1234)

    assert brcs == [4] * math.ceil(1234 / 128)
    assert thidxs == [0] * math.ceil(1234 / 128)
    expected_sample = (False, 0)
    assert s_ie == [expected_sample] * 1234
    assert s_io == [expected_sample] * 1234
    assert s_qe == [expected_sample] * 1234
    assert s_qo == [expected_sample] * 1234

    config = PacketConfig(num_quads=42, const_brc=4, const_thidx=63)
    data = create_synthetic_fdbaq_data(config, "1100")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 42)

    assert brcs == [4] * math.ceil(42 / 128)
    assert thidxs == [63] * math.ceil(42 / 128)
    expected_sample = (True, 3)
    assert s_ie == [expected_sample] * 42
    assert s_io == [expected_sample] * 42
    assert s_qe == [expected_sample] * 42
    assert s_qo == [expected_sample] * 42

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [4] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 15)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "1111111110")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [4] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (True, 14)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99

    config = PacketConfig(num_quads=99, const_brc=4, const_thidx=11)
    data = create_synthetic_fdbaq_data(config, "0111111111")
    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 99)

    assert brcs == [4] * math.ceil(99 / 128)
    assert thidxs == [11] * math.ceil(99 / 128)
    expected_sample = (False, 15)
    assert s_ie == [expected_sample] * 99
    assert s_io == [expected_sample] * 99
    assert s_qe == [expected_sample] * 99
    assert s_qo == [expected_sample] * 99


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

    brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(data, 128 * 5)

    # Check BRCs and THIDXs
    assert brcs == [0, 1, 2, 3, 4]  # 5 blocks with different BRCs
    assert thidxs == [0, 0, 0, 0, 0]  # All THIDXs are 0

    # Check sample codes
    expected = [
        *[(False, 3)] * 128,  # BRC 0: magnitude 3
        *[(False, 4)] * 128,  # BRC 1: magnitude 4
        *[(False, 6)] * 128,  # BRC 2: magnitude 6
        *[(False, 9)] * 128,  # BRC 3: magnitude 9
        *[(False, 15)] * 128,  # BRC 4: magnitude 15
    ]
    assert s_ie == expected
    assert s_io == expected
    assert s_qe == expected
    assert s_qo == expected
