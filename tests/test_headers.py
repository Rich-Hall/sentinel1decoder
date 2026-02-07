"""Tests for packet header decoding via Rust decode_packet_headers and metadata parser."""

import pandas as pd
import pytest

from sentinel1decoder import _field_names as fn
from sentinel1decoder._metadata_parser import parse_raw_metadata_columns
from sentinel1decoder._sentinel1decoder import decode_packet_headers

from .data_generation_utils import (
    PacketConfig,
    create_synthetic_level0_packet,
    pack_bits,
)


def _decode_single_packet(packet_bytes: bytes) -> pd.DataFrame:
    """Run Rust decode_packet_headers and parse to decoded DataFrame (one row per packet)."""
    columns, _ = decode_packet_headers(packet_bytes)
    return parse_raw_metadata_columns(columns)


# ---- Rust / Python field name sync ----


def test_rust_output_keys_handled_by_python() -> None:
    """Every key Rust decode_packet_headers outputs must be in RAW_TO_DECODED_NAME.

    This ensures the two sources of truth (Rust lib.rs into_pydict, Python _field_names.py)
    stay in sync. If Rust adds a new field or changes a key, this test fails until Python
    is updated.
    """
    config = PacketConfig(num_quads=1, baq_mode=0)
    packet = create_synthetic_level0_packet(config, 0)
    columns, _ = decode_packet_headers(packet)

    rust_keys = set(columns.keys())
    python_handled = set(fn.RAW_TO_DECODED_NAME.keys())

    unhandled = rust_keys - python_handled
    assert not unhandled, (
        f"Rust outputs {len(unhandled)} key(s) not in Python RAW_TO_DECODED_NAME: {unhandled}. "
        "Add raw->decoded mapping in _field_names.py."
    )


# ---- Primary header: format and values ----


def test_decode_primary_header_too_few_bytes() -> None:
    """Fewer than 6 bytes yields no packets."""
    data = b"\xff"
    columns, bounds = decode_packet_headers(data)
    assert len(bounds) == 0
    assert len(columns[fn.PACKET_VER_NUM_RAW]) == 0


def test_decode_primary_header_values() -> None:
    """Primary header fields decoded correctly from synthetic packet with secondary."""
    config = PacketConfig(
        packet_version=0,
        packet_type=0,
        secondary_header_flag=1,
        process_id=0b1000001,
        packet_category=12,
        sequence_flags=3,
        packet_sequence=0,
        num_quads=1,
        baq_mode=0,
    )
    packet = create_synthetic_level0_packet(config, 0)
    df = _decode_single_packet(packet)

    assert df[fn.PACKET_VER_NUM_DECODED].iloc[0] == 0
    assert df[fn.PACKET_TYPE_DECODED].iloc[0] == 0
    assert df[fn.SECONDARY_HEADER_DECODED].iloc[0] == 1
    assert df[fn.PID_DECODED].iloc[0] == 65
    assert df[fn.PCAT_DECODED].iloc[0] == 12
    assert df[fn.SEQUENCE_FLAGS_DECODED].iloc[0] == 3
    assert df[fn.PACKET_SEQUENCE_COUNT_DECODED].iloc[0] == 0
    # First packet has secondary header: packet data field = 62 (secondary) + 8 (bypass payload)
    assert df[fn.PACKET_DATA_LEN_DECODED].iloc[0] == 62 + 8

    config2 = PacketConfig(
        packet_version=2,
        packet_type=1,
        secondary_header_flag=0,
        process_id=0b1010101,
        packet_category=0,
        sequence_flags=1,
        packet_sequence=100,
    )
    packet2 = create_synthetic_level0_packet(config2, 0, include_secondary=False)
    df2 = _decode_single_packet(packet2)

    assert df2[fn.PACKET_VER_NUM_DECODED].iloc[0] == 2
    assert df2[fn.PACKET_TYPE_DECODED].iloc[0] == 1
    assert df2[fn.SECONDARY_HEADER_DECODED].iloc[0] == 0
    assert df2[fn.PID_DECODED].iloc[0] == 85
    assert df2[fn.PCAT_DECODED].iloc[0] == 0
    assert df2[fn.SEQUENCE_FLAGS_DECODED].iloc[0] == 1
    assert df2[fn.PACKET_SEQUENCE_COUNT_DECODED].iloc[0] == 100
    # Second packet has no secondary header; 62 bytes of user data only (no secondary bytes)
    assert df2[fn.PACKET_DATA_LEN_DECODED].iloc[0] == 62


def test_primary_header_from_bits_directly() -> None:
    """Primary header decoded from bit-packed bytes (packet data length in last 16 bits)."""
    primary_only = pack_bits(
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
    assert len(primary_only) == 6
    # Append 62 bytes so Rust can consume one full packet (secondary header)
    packet = primary_only + b"\x00" * 62
    columns, bounds = decode_packet_headers(packet)

    assert len(bounds) == 1
    assert columns[fn.PACKET_VER_NUM_RAW][0] == 0
    assert columns[fn.PACKET_TYPE_RAW][0] == 0
    assert columns[fn.SECONDARY_HEADER_RAW][0] == 1
    assert columns[fn.PID_RAW][0] == 65
    assert columns[fn.PCAT_RAW][0] == 12
    assert columns[fn.SEQUENCE_FLAGS_RAW][0] == 3
    assert columns[fn.PACKET_SEQUENCE_COUNT_RAW][0] == 16380
    assert columns[fn.PACKET_DATA_LEN_RAW][0] == 65533


# ---- Secondary header: raw and decoded ----


def test_decode_secondary_header_raw_values() -> None:
    """Rust decode_packet_headers returns raw secondary values; parser keeps them then renames."""
    config = PacketConfig(rx_gain=20, pri=2000, num_quads=1, baq_mode=0)
    packet = create_synthetic_level0_packet(config, 0)
    columns, _ = decode_packet_headers(packet)

    assert columns["RXG"][0] == 20
    assert columns["PRI"][0] == 2000
    assert columns["TFINE"][0] == 0


def test_decode_secondary_header_absent_all_na() -> None:
    """Packet with secondary_header_flag=0 yields one row with secondary columns all NA."""
    config = PacketConfig(secondary_header_flag=0)
    packet = create_synthetic_level0_packet(config, 0, include_secondary=False)
    df = _decode_single_packet(packet)

    assert len(df) == 1
    assert pd.isna(df["Rx Gain"].iloc[0])
    assert pd.isna(df["PRI"].iloc[0])


def test_decode_secondary_header_decoded_values_default() -> None:
    """Decoded metadata (default config): enums, scaled values, renames."""
    config = PacketConfig(num_quads=1, baq_mode=12)  # FDBAQ for minimal payload
    packet = create_synthetic_level0_packet(config, "1010")
    df = _decode_single_packet(packet)
    row = df.iloc[0]

    assert row["Coarse Time"] == 0
    assert row["Fine Time"] == pytest.approx(0.5 * (2**-16), abs=1e-10)
    assert row["Sync"] == 0x352EF853
    assert row["Data Take ID"] == 1
    assert row["ECC Number"].value == 0
    assert row["Test Mode"].value == 0
    assert row["Rx Channel ID"].value == 0
    assert row["Instrument Configuration ID"] == 0
    assert row["Sub-commutated Ancilliary Data Word Index"] == 0
    assert row["Sub-commutated Ancilliary Data Word"] == 0
    assert row["Space Packet Count"] == 0
    assert row["PRI Count"] == 0
    assert row["Error Flag"] == False  # noqa: E712  # numpy bool vs Python bool
    assert row["BAQ Mode"].value == 12
    assert row["BAQ Block Length"] == 128
    assert row["Range Decimation"].value == 0
    assert row["Rx Gain"] == 0
    assert row["Rank"] == 0


def test_decode_secondary_header_decoded_values_non_default() -> None:
    """Decoded metadata with non-default config: datation, ancillary, radar, F_REF scaling."""
    F_REF = 37.53472224 * 1e6

    config = PacketConfig(
        coarse_time=1234567,
        fine_time=65535,
        data_take_id=42,
        ecc_number=8,
        test_mode=5,
        rx_channel_id=1,
        instrument_config_id=0xABCDEF,
        subcom_data_word_ind=45,
        subcom_data_word=12345,
        space_packet_count=9876543,
        pri_count=8765432,
        error_flag=1,
        baq_mode=13,
        baq_block_length=64,
        range_decimation=7,
        rx_gain=20,
        txprr=12345,
        txpsf=54321,
        tx_pulse_length=123456,
        rank=17,
        pri=2000,
        sampling_window_start_time=3000,
        sampling_window_length=4000,
        sas_ssbflag=1,
        polarisation=5,
        temperature_comp=2,
        calibration_mode=2,
        tx_pulse_number=17,
        signal_type=9,
        swap_flag=1,
        swath_num=3,
        num_quads=1,
    )
    packet = create_synthetic_level0_packet(config, "1010")
    df = _decode_single_packet(packet)
    row = df.iloc[0]

    assert row["Coarse Time"] == 1234567
    assert row["Fine Time"] == pytest.approx(1.0, abs=1e-5)

    assert row["Sync"] == 0x352EF853
    assert row["Data Take ID"] == 42
    assert row["ECC Number"].value == 8
    assert row["Test Mode"].value == 5
    assert row["Rx Channel ID"].value == 1
    assert row["Instrument Configuration ID"] == 0xABCDEF

    assert row["Sub-commutated Ancilliary Data Word Index"] == 45
    assert row["Sub-commutated Ancilliary Data Word"] == 12345

    assert row["Space Packet Count"] == 9876543
    assert row["PRI Count"] == 8765432

    assert row["Error Flag"] == True  # noqa: E712
    assert row["BAQ Mode"].value == 13
    assert row["BAQ Block Length"] == 64
    assert row["Range Decimation"].value == 7
    assert row["Rx Gain"] == pytest.approx(-10.0)

    txprr_sign = (-1) ** (1 - (config.txprr >> 15))
    expected_txprr = txprr_sign * (config.txprr & 0x7FFF) * (F_REF**2) / (2**21)
    assert row["Tx Ramp Rate"] == pytest.approx(expected_txprr)

    txpsf_additive = expected_txprr / (4 * F_REF)
    txpsf_sign = (-1) ** (1 - (config.txpsf >> 15))
    expected_txpsf = txpsf_additive + txpsf_sign * (config.txpsf & 0x7FFF) * F_REF / (2**14)
    assert row["Tx Pulse Start Frequency"] == pytest.approx(expected_txpsf)

    assert row["Tx Pulse Length"] == pytest.approx(config.tx_pulse_length / F_REF)
    assert row["Rank"] == 17
    assert row["PRI"] == pytest.approx(config.pri / F_REF)
    assert row["SWST"] == pytest.approx(config.sampling_window_start_time / F_REF)
    assert row["SWL"] == pytest.approx(config.sampling_window_length / F_REF)

    assert row["SAS SSB Flag"].value == 1
    assert row["Polarisation"].value == 5
    assert row["Temperature Compensation"].value == 2
    assert row["Cal Type"].value == 0
    assert row["Calibration Mode"].value == 2
    assert row["Tx Pulse Number"] == 17
    assert row["Signal Type"].value == 9
    assert row["Swap Flag"] == True  # noqa: E712
    assert row["Swath Number"] == 3
