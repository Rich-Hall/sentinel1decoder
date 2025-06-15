import logging

from sentinel1decoder import constants as cnst


def decode_primary_header(header_bytes: bytes) -> dict:
    """Decode the Sentinel-1 Space Packet primary header.

    Refer to SAR Space Protocol Data Unit specification document pg.13
    The primary header consists of exactly 6 bytes.

    Parameters
    ----------
    header_bytes : List
        List of input bytes. Must contain exactly 6 bytes.

    Returns
    -------
    output_dictionary : Dictionary
        Dictionary of primary header fields.

    """
    if not len(header_bytes) == 6:
        logging.error("Primary header must be exactly 6 bytes")
        raise Exception(f"Primary header must be exactly 6 bytes. Received {len(header_bytes)} bytes.")

    tmp16 = int.from_bytes(header_bytes[:2], "big")
    packet_version_number = tmp16 >> 13  # Bit 0-2
    packet_type = (tmp16 >> 12) & 0x01  # Bit 3
    secondary_header_flag = (tmp16 >> 11) & 0x01  # Bit 4
    process_id = (tmp16 >> 4) & 0x7F  # Bit 5-11
    packet_category = tmp16 & 0xF  # Bit 12-15

    tmp16 = int.from_bytes(header_bytes[2:4], "big")
    sequence_flags = tmp16 >> 14  # Bit 0-1
    packet_sequence_count = tmp16 & 0x3FFF  # Bit 2-15

    tmp16 = int.from_bytes(header_bytes[4:], "big")
    packet_data_length = tmp16 + 1  # Bit 0-15

    # Total space packet length must be a multiple of 4 bytes.
    # Packet length = 6 primary header bytes + packet data length
    if not (packet_data_length + 6) % 4 == 0:
        logging.error("Packet length is not a multiple of 4 bytes")

    output_dictionary = {
        cnst.PACKET_VER_NUM_FIELD_NAME: packet_version_number,
        cnst.PACKET_TYPE_FIELD_NAME: packet_type,
        cnst.SECONDARY_HEADER_FIELD_NAME: secondary_header_flag,
        cnst.PID_FIELD_NAME: process_id,
        cnst.PCAT_FIELD_NAME: packet_category,
        cnst.SEQUENCE_FLAGS_FIELD_NAME: sequence_flags,
        cnst.PACKET_SEQUENCE_COUNT_FIELD_NAME: packet_sequence_count,
        cnst.PACKET_DATA_LEN_FIELD_NAME: packet_data_length,
    }

    return output_dictionary


def decode_secondary_header(header_bytes: bytes) -> dict:
    """Decode the Sentinel-1 Space Packet secondary header.

    Refer to SAR Space Protocol Data Unit specification document pg.14
    The secondary header consists of exactly 62 bytes.

    Args:
        header_bytes: Set of input bytes. Must contain exactly 62 bytes.

    Returns:
        A dictionary of secondary header fields.
    """
    if not len(header_bytes) == 62:
        logging.error("Secondary header must be exactly 62 bytes")
        raise Exception(f"Secondary header must be exactly 62 bytes. Received {len(header_bytes)} bytes.")

    # ---------------------------------------------------------
    # Datation service (6 bytes)
    # ---------------------------------------------------------
    coarse_time = int.from_bytes(header_bytes[:4], "big")

    fine_time = (int.from_bytes(header_bytes[4:6], "big") + 0.5) * (2 ** (-16))

    output_dictionary = {
        cnst.COARSE_TIME_FIELD_NAME: coarse_time,
        cnst.FINE_TIME_FIELD_NAME: fine_time,
    }

    # ---------------------------------------------------------
    # Fixed ancillary data field (14 bytes)
    # ---------------------------------------------------------
    sync = int.from_bytes(header_bytes[6:10], "big")

    data_take_id = int.from_bytes(header_bytes[10:14], "big")

    ecc_number = header_bytes[14]

    # Byte 15 bit 1 is unused
    test_mode = (header_bytes[15] >> 4) & 0x07  # Byte 15 Bits 1-3
    rx_channel_id = header_bytes[15] & 0x0F  # Byte 15 Bits 4-7

    instrument_config_id = int.from_bytes(header_bytes[16:20], "big")

    output_dictionary.update(
        {
            cnst.SYNC_FIELD_NAME: sync,
            cnst.DATA_TAKE_ID_FIELD_NAME: data_take_id,
            cnst.ECC_NUM_FIELD_NAME: ecc_number,
            cnst.TEST_MODE_FIELD_NAME: test_mode,
            cnst.RX_CHAN_ID_FIELD_NAME: rx_channel_id,
            cnst.INSTRUMENT_CONFIG_ID_FIELD_NAME: instrument_config_id,
        }
    )

    if sync != 0x352EF853:
        logging.error("Sync marker != 352EF853")

    # ---------------------------------------------------------
    # Sub-commutated ancillary data service (3 bytes)
    # ---------------------------------------------------------
    # The update rate of satellite ephemeris data is much lower
    # than the space packet generation rate (up to 1Hz). Data is
    # thus subcommed in portions of 2 bytes per space packet.
    # The full data frame is 42 bytes long.
    subcom_data_word_ind = header_bytes[20]

    subcom_data_word = int.from_bytes(header_bytes[21:23], "big")

    output_dictionary.update(
        {
            cnst.SUBCOM_ANC_DATA_WORD_INDEX_FIELD_NAME: subcom_data_word_ind,
            cnst.SUBCOM_ANC_DATA_WORD_FIELD_NAME: subcom_data_word,
        }
    )

    # ---------------------------------------------------------
    # Counters Service (8 bytes)
    # ---------------------------------------------------------
    space_packet_count = int.from_bytes(header_bytes[23:27], "big")

    pri_count = int.from_bytes(header_bytes[27:31], "big")

    output_dictionary.update(
        {
            cnst.SPACE_PACKET_COUNT_FIELD_NAME: space_packet_count,
            cnst.PRI_COUNT_FIELD_NAME: pri_count,
        }
    )

    # ---------------------------------------------------------
    # Radar configuration support service (27 bytes)
    # ---------------------------------------------------------
    error_flag = header_bytes[31] >> 7  # Byte 31 Bit 0
    # Byte 31 Bits 1-2 are unused.
    baq_mode = header_bytes[31] & 0x1F  # Byte 31 Bits 3-7

    baq_block_length = header_bytes[32]

    # The byte at packet_data[33] is unused

    range_decimation = header_bytes[34]

    rx_gain = header_bytes[35] * -0.5

    tmp16 = int.from_bytes(header_bytes[36:38], "big")
    txprr_sign = (-1) ** (1 - (tmp16 >> 15))
    txprr = txprr_sign * (tmp16 & 0x7FFF) * (cnst.F_REF**2) / (2**21)

    tmp16 = int.from_bytes(header_bytes[38:40], "big")
    txpsf_additive = txprr / (4 * cnst.F_REF)
    txpsf_sign = (-1) ** (1 - (tmp16 >> 15))
    txpsf = txpsf_additive + txpsf_sign * (tmp16 & 0x7FFF) * cnst.F_REF / (2**14)

    tmp24 = int.from_bytes(header_bytes[40:43], "big")
    tx_pulse_length = tmp24 / cnst.F_REF

    # Byte 43 bits 0-2 are unused
    rank = header_bytes[43] & 0x1F  # Byte 43 bits 3-7

    tmp24 = int.from_bytes(header_bytes[44:47], "big")
    pri = tmp24 / cnst.F_REF

    tmp24 = int.from_bytes(header_bytes[47:50], "big")
    sampling_window_start_time = tmp24 / cnst.F_REF

    tmp24 = int.from_bytes(header_bytes[50:53], "big")
    sampling_window_length = tmp24 / cnst.F_REF

    sas_ssbflag = header_bytes[53] >> 7  # Byte 53 Bit 0
    polarisation = (header_bytes[53] >> 4) & 0x07  # Byte 53 Bits 1-3
    temperature_comp = (header_bytes[53] >> 2) & 0x03  # Byte 53 Bits 4-5
    # Byte 53 Bits 6-7 are unused

    # Some extra unimplemented stuff here.
    # Exact fields used depends on the value of sas_ssbflag
    # TODO: Implement sas_ssb_message decoding

    calibration_mode = header_bytes[56] >> 6  # Byte 56 Bits 0-1
    # Byte 56 Bit 2 is unused
    tx_pulse_number = header_bytes[56] & 0x1F  # Byte 56 Bits 3-7

    signal_type = header_bytes[57] >> 4  # Byte 57 Bits 0-3
    # Byte 57 Bits 4-6 are unused
    swap_flag = header_bytes[57] & 0x01  # Byte 57 Bit 7

    swath_number = header_bytes[58]

    output_dictionary.update(
        {
            cnst.ERROR_FLAG_FIELD_NAME: error_flag,
            cnst.BAQ_MODE_FIELD_NAME: baq_mode,
            cnst.BAQ_BLOCK_LEN_FIELD_NAME: baq_block_length,
            cnst.RANGE_DEC_FIELD_NAME: range_decimation,
            cnst.RX_GAIN_FIELD_NAME: rx_gain,
            cnst.TX_RAMP_RATE_FIELD_NAME: txprr,
            cnst.TX_PULSE_START_FREQ_FIELD_NAME: txpsf,
            cnst.TX_PULSE_LEN_FIELD_NAME: tx_pulse_length,
            cnst.RANK_FIELD_NAME: rank,
            cnst.PRI_FIELD_NAME: pri,
            cnst.SWST_FIELD_NAME: sampling_window_start_time,
            cnst.SWL_FIELD_NAME: sampling_window_length,
            cnst.SAS_SSB_FLAG_FIELD_NAME: sas_ssbflag,
            cnst.POLARIZATION_FIELD_NAME: polarisation,
            cnst.TEMP_COMP_FIELD_NAME: temperature_comp,
            cnst.CAL_MODE_FIELD_NAME: calibration_mode,
            cnst.TX_PULSE_NUM_FIELD_NAME: tx_pulse_number,
            cnst.SIGNAL_TYPE_FIELD_NAME: signal_type,
            cnst.SWAP_FLAG_FIELD_NAME: swap_flag,
            cnst.SWATH_NUM_FIELD_NAME: swath_number,
        }
    )

    # ---------------------------------------------------------
    # Radar sample count service (3 bytes)
    # ---------------------------------------------------------
    number_of_quads = int.from_bytes(header_bytes[59:61], "big")

    # The byte at packet_data[61] is unused

    output_dictionary.update({cnst.NUM_QUADS_FIELD_NAME: number_of_quads})

    # ---------------------------------------------------------
    # End of secondary header information
    # ---------------------------------------------------------

    return output_dictionary
