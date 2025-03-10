import pytest

from sentinel1decoder._headers import decode_primary_header, decode_secondary_header

from .data_generation_utils import (
    PacketConfig,
    create_primary_header,
    create_secondary_header,
    pack_bits,
)


def test_decode_primary_header_format() -> None:
    # Supply too few bytes
    with pytest.raises(Exception):
        decode_primary_header(b"\xFF")
    # Supply too many bytes
    with pytest.raises(Exception):
        decode_primary_header(b"\xFF" * 100)


def test_decode_primary_header_values() -> None:

    test_header = create_primary_header(
        PacketConfig(
            packet_version=0,
            packet_type=0,
            secondary_header_flag=1,
            process_id=0b1000001,
            packet_category=12,
            sequence_flags=3,
            packet_sequence=0,
        ),
        62,
    )
    decoded_header = decode_primary_header(test_header)
    assert decoded_header["Packet Version Number"] == 0
    assert decoded_header["Packet Type"] == 0
    assert decoded_header["Secondary Header Flag"] == 1
    assert decoded_header["PID"] == 65
    assert decoded_header["PCAT"] == 12
    assert decoded_header["Sequence Flags"] == 3
    assert decoded_header["Packet Sequence Count"] == 0
    assert decoded_header["Packet Data Length"] == 62

    test_header = create_primary_header(
        PacketConfig(
            packet_version=2,
            packet_type=1,
            secondary_header_flag=0,
            process_id=0b1010101,
            packet_category=0,
            sequence_flags=1,
            packet_sequence=100,
        ),
        1234,
    )
    decoded_header = decode_primary_header(test_header)
    assert decoded_header["Packet Version Number"] == 2
    assert decoded_header["Packet Type"] == 1
    assert decoded_header["Secondary Header Flag"] == 0
    assert decoded_header["PID"] == 85
    assert decoded_header["PCAT"] == 0
    assert decoded_header["Sequence Flags"] == 1
    assert decoded_header["Packet Sequence Count"] == 100
    assert decoded_header["Packet Data Length"] == 1234


def test_primary_header_from_bits_directly() -> None:
    test_header = pack_bits(
        [
            "000",  # version
            "0",  # type
            "1",  # secondary header flag
            "1000001",  # process id
            "1100",  # packet category
            "11",  # sequence flags
            "11111111111100",  # packet sequence
            "1111111111111100",  # packet data length
        ]
    )
    decoded_header = decode_primary_header(test_header)
    assert decoded_header["Packet Version Number"] == 0
    assert decoded_header["Packet Type"] == 0
    assert decoded_header["Secondary Header Flag"] == 1
    assert decoded_header["PID"] == 65
    assert decoded_header["PCAT"] == 12
    assert decoded_header["Sequence Flags"] == 3
    assert decoded_header["Packet Sequence Count"] == 16380
    assert decoded_header["Packet Data Length"] == 65533


def test_decode_secondary_header_format() -> None:
    # Supply too few bytes
    with pytest.raises(Exception):
        decode_secondary_header(b"\xFF")
    # Supply too many bytes
    with pytest.raises(Exception):
        decode_secondary_header(b"\xFF" * 63)


def test_decode_secondary_header_values() -> None:
    # Test case 1: Default values
    config = PacketConfig()
    test_header = create_secondary_header(config)
    decoded_header = decode_secondary_header(test_header)

    assert decoded_header["Coarse Time"] == 0
    assert decoded_header["Fine Time"] == 0.5 * (2**-16)  # Decoder adds this offset
    assert decoded_header["Sync"] == 0x352EF853
    assert decoded_header["Data Take ID"] == 1
    assert decoded_header["ECC Number"] == 0
    assert decoded_header["Test Mode"] == 0
    assert decoded_header["Rx Channel ID"] == 0
    assert decoded_header["Instrument Configuration ID"] == 0
    assert decoded_header["Sub-commutated Ancilliary Data Word Index"] == 0
    assert decoded_header["Sub-commutated Ancilliary Data Word"] == 0
    assert decoded_header["Space Packet Count"] == 0
    assert decoded_header["PRI Count"] == 0
    assert decoded_header["Error Flag"] == 0
    assert decoded_header["BAQ Mode"] == 12
    assert decoded_header["BAQ Block Length"] == 128
    assert decoded_header["Range Decimation"] == 0
    assert decoded_header["Rx Gain"] == 0
    assert decoded_header["Rank"] == 0

    # Test case 2: Non-default values
    config = PacketConfig(
        # Datation Service
        coarse_time=1234567,
        fine_time=65535,  # Will result in 1.0 after decoder transformation
        # Fixed Ancillary Data
        data_take_id=42,
        ecc_number=123,
        test_mode=5,
        rx_channel_id=7,
        instrument_config_id=0xABCDEF,
        # Sub-commutated Ancillary Data
        subcom_data_word_ind=45,
        subcom_data_word=12345,
        # Counters Service
        space_packet_count=9876543,
        pri_count=8765432,
        # Radar Configuration
        error_flag=1,
        baq_mode=11,
        baq_block_length=64,
        range_decimation=7,
        rx_gain=20,  # Will result in -10.0 after decoder transformation
        txprr=12345,  # Needs transformation in decoder
        txpsf=54321,  # Needs transformation in decoder
        tx_pulse_length=123456,  # Needs transformation with F_REF
        rank=17,
        pri=2000,  # Needs transformation with F_REF
        sampling_window_start_time=3000,  # Needs transformation with F_REF
        sampling_window_length=4000,  # Needs transformation with F_REF
        sas_ssbflag=1,
        polarisation=5,
        temperature_comp=2,
        calibration_mode=2,
        tx_pulse_number=17,
        signal_type=9,
        swap_flag=1,
        swath_num=3,
    )
    test_header = create_secondary_header(config)
    decoded_header = decode_secondary_header(test_header)

    F_REF = 37.53472224 * 1e6  # Reference frequency in Hz

    # Datation Service
    assert decoded_header["Coarse Time"] == 1234567
    assert decoded_header["Fine Time"] == pytest.approx(1.0, abs=1e-5)

    # Fixed Ancillary Data
    assert decoded_header["Sync"] == 0x352EF853
    assert decoded_header["Data Take ID"] == 42
    assert decoded_header["ECC Number"] == 123
    assert decoded_header["Test Mode"] == 5
    assert decoded_header["Rx Channel ID"] == 7
    assert decoded_header["Instrument Configuration ID"] == 0xABCDEF

    # Sub-commutated Ancillary Data
    assert decoded_header["Sub-commutated Ancilliary Data Word Index"] == 45
    assert decoded_header["Sub-commutated Ancilliary Data Word"] == 12345

    # Counters Service
    assert decoded_header["Space Packet Count"] == 9876543
    assert decoded_header["PRI Count"] == 8765432

    # Radar Configuration
    assert decoded_header["Error Flag"] == 1
    assert decoded_header["BAQ Mode"] == 11
    assert decoded_header["BAQ Block Length"] == 64
    assert decoded_header["Range Decimation"] == 7
    assert decoded_header["Rx Gain"] == -10.0

    # Complex transformations from decoder
    txprr_sign = (-1) ** (1 - (config.txprr >> 15))
    expected_txprr = txprr_sign * (config.txprr & 0x7FFF) * (F_REF**2) / (2**21)
    assert decoded_header["Tx Ramp Rate"] == pytest.approx(expected_txprr)

    txpsf_additive = expected_txprr / (4 * F_REF)
    txpsf_sign = (-1) ** (1 - (config.txpsf >> 15))
    expected_txpsf = txpsf_additive + txpsf_sign * (config.txpsf & 0x7FFF) * F_REF / (
        2**14
    )
    assert decoded_header["Tx Pulse Start Frequency"] == pytest.approx(expected_txpsf)

    assert decoded_header["Tx Pulse Length"] == pytest.approx(
        config.tx_pulse_length / F_REF
    )
    assert decoded_header["Rank"] == 17
    assert decoded_header["PRI"] == pytest.approx(config.pri / F_REF)
    assert decoded_header["SWST"] == pytest.approx(
        config.sampling_window_start_time / F_REF
    )
    assert decoded_header["SWL"] == pytest.approx(config.sampling_window_length / F_REF)

    assert decoded_header["SAS SSB Flag"] == 1
    assert decoded_header["Polarisation"] == 5
    assert decoded_header["Temperature Compensation"] == 2
    assert decoded_header["Calibration Mode"] == 2
    assert decoded_header["Tx Pulse Number"] == 17
    assert decoded_header["Signal Type"] == 9
    assert decoded_header["Swap Flag"] == 1
    assert decoded_header["Swath Number"] == 3
