"""Header field name definitions for Sentinel-1 packet metadata.

This module defines raw (spec-style) and decoded (human-readable) column names
as constants, with derived mappings for renaming DataFrames.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Packet metadata dataframe indices (not part of headers)
# -----------------------------------------------------------------------------
PACKET_NUM_DECODED = "Packet Number"
ACQUISITION_CHUNK_NUM_DECODED = "Acquisition Chunk"

# -----------------------------------------------------------------------------
# Primary header fields (Rust uses snake_case keys; we map to decoded names)
# -----------------------------------------------------------------------------
PACKET_VER_NUM_RAW = "packet_ver_num"
PACKET_VER_NUM_DECODED = "Packet Version Number"
PACKET_TYPE_RAW = "packet_type"
PACKET_TYPE_DECODED = "Packet Type"
SECONDARY_HEADER_RAW = "secondary_header"
SECONDARY_HEADER_DECODED = "Secondary Header Flag"
PID_RAW = "pid"
PID_DECODED = "PID"
PCAT_RAW = "pcat"
PCAT_DECODED = "PCAT"
SEQUENCE_FLAGS_RAW = "sequence_flags"
SEQUENCE_FLAGS_DECODED = "Sequence Flags"
PACKET_SEQUENCE_COUNT_RAW = "packet_sequence_count"
PACKET_SEQUENCE_COUNT_DECODED = "Packet Sequence Count"
PACKET_DATA_LEN_RAW = "packet_data_len"
PACKET_DATA_LEN_DECODED = "Packet Data Length"

# -----------------------------------------------------------------------------
# Secondary header fields - Datation service
# -----------------------------------------------------------------------------
COARSE_TIME_RAW = "TCOAR"
COARSE_TIME_DECODED = "Coarse Time"
FINE_TIME_RAW = "TFINE"
FINE_TIME_DECODED = "Fine Time"

# -----------------------------------------------------------------------------
# Secondary header fields - Fixed ancillary data
# -----------------------------------------------------------------------------
SYNC_RAW = "SYNC"
SYNC_DECODED = "Sync"
DATA_TAKE_ID_RAW = "DTID"
DATA_TAKE_ID_DECODED = "Data Take ID"
ECC_NUM_RAW = "ECC"
ECC_NUM_DECODED = "ECC Number"
TEST_MODE_RAW = "TSTMOD"
TEST_MODE_DECODED = "Test Mode"
RX_CHAN_ID_RAW = "RXCHID"
RX_CHAN_ID_DECODED = "Rx Channel ID"
INSTRUMENT_CONFIG_ID_RAW = "ICID"
INSTRUMENT_CONFIG_ID_DECODED = "Instrument Configuration ID"

# -----------------------------------------------------------------------------
# Secondary header fields - Sub-commutated ancillary data
# -----------------------------------------------------------------------------
SUBCOM_ANC_DATA_WORD_INDEX_RAW = "ADWIDX"
SUBCOM_ANC_DATA_WORD_INDEX_DECODED = "Sub-commutated Ancilliary Data Word Index"
SUBCOM_ANC_DATA_WORD_RAW = "ADW"
SUBCOM_ANC_DATA_WORD_DECODED = "Sub-commutated Ancilliary Data Word"

# -----------------------------------------------------------------------------
# Secondary header fields - Counters service
# -----------------------------------------------------------------------------
SPACE_PACKET_COUNT_RAW = "SPCT"
SPACE_PACKET_COUNT_DECODED = "Space Packet Count"
PRI_COUNT_RAW = "PRICT"
PRI_COUNT_DECODED = "PRI Count"

# -----------------------------------------------------------------------------
# Secondary header fields - Radar configuration support service
# -----------------------------------------------------------------------------
ERROR_FLAG_RAW = "ERRFLG"
ERROR_FLAG_DECODED = "Error Flag"
BAQ_MODE_RAW = "BAQMOD"
BAQ_MODE_DECODED = "BAQ Mode"
BAQ_BLOCK_LEN_RAW = "BAQBL"
BAQ_BLOCK_LEN_DECODED = "BAQ Block Length"
RANGE_DEC_RAW = "RGDEC"
RANGE_DEC_DECODED = "Range Decimation"
RX_GAIN_RAW = "RXG"
RX_GAIN_DECODED = "Rx Gain"
TX_RAMP_RATE_RAW = "TXPRR"
TX_RAMP_RATE_DECODED = "Tx Ramp Rate"
TX_PULSE_START_FREQ_RAW = "TXPSF"
TX_PULSE_START_FREQ_DECODED = "Tx Pulse Start Frequency"
TX_PULSE_LEN_RAW = "TXPL"
TX_PULSE_LEN_DECODED = "Tx Pulse Length"
RANK_RAW = "RANK"
RANK_DECODED = "Rank"
PRI_RAW = "PRI"
PRI_DECODED = "PRI"
SWST_RAW = "SWST"
SWST_DECODED = "SWST"
SWL_RAW = "SWL"
SWL_DECODED = "SWL"
SAS_SSB_FLAG_RAW = "SSBFLAG"
SAS_SSB_FLAG_DECODED = "SAS SSB Flag"
POLARIZATION_RAW = "POL"
POLARIZATION_DECODED = "Polarisation"
TEMP_COMP_RAW = "TCMP"
TEMP_COMP_DECODED = "Temperature Compensation"
EBADR_RAW = "EBADR"
EBADR_DECODED = "Elevation Beam Address"
ABADR_RAW = "ABADR"
ABADR_DECODED = "Azimuth Beam Address"
SASTM_RAW = "SASTM"
SASTM_DECODED = "SAS Test Mode"
CALTYP_RAW = "CALTYP"
CALTYP_DECODED = "Cal Type"
CBADR_RAW = "CBADR"
CBADR_DECODED = "Calibration Beam Address"
CAL_MODE_RAW = "CALMOD"
CAL_MODE_DECODED = "Calibration Mode"
TX_PULSE_NUM_RAW = "TXPNO"
TX_PULSE_NUM_DECODED = "Tx Pulse Number"
SIGNAL_TYPE_RAW = "SIGTYP"
SIGNAL_TYPE_DECODED = "Signal Type"
SWAP_FLAG_RAW = "SWAP"
SWAP_FLAG_DECODED = "Swap Flag"
SWATH_NUM_RAW = "SWATH"
SWATH_NUM_DECODED = "Swath Number"

# -----------------------------------------------------------------------------
# Secondary header fields - Radar sample count service
# -----------------------------------------------------------------------------
NUM_QUADS_RAW = "NQ"
NUM_QUADS_DECODED = "Number of Quads"

# -----------------------------------------------------------------------------
# Subcommutated data fields (ephemeris/attitude) - decoded only
# -----------------------------------------------------------------------------
X_POS_DECODED = "X-axis position ECEF"
Y_POS_DECODED = "Y-axis position ECEF"
Z_POS_DECODED = "Z-axis position ECEF"
X_VEL_DECODED = "X-axis velocity ECEF"
Y_VEL_DECODED = "Y-axis velocity ECEF"
Z_VEL_DECODED = "Z-axis velocity ECEF"
POD_SOLN_DATA_TIMESTAMP_DECODED = "POD Solution Data Timestamp"
Q0_DECODED = "Q0 Attitude Quaternion"
Q1_DECODED = "Q1 Attitude Quaternion"
Q2_DECODED = "Q2 Attitude Quaternion"
Q3_DECODED = "Q3 Attitude Quaternion"
X_ANG_RATE_DECODED = "Omega-X Angular Rate"
Y_ANG_RATE_DECODED = "Omega-Y Angular Rate"
Z_ANG_RATE_DECODED = "Omega-Z Angular Rate"
ATTITUDE_DATA_TIMESTAMP_DECODED = "Attitude Data Timestamp"

# -----------------------------------------------------------------------------
# Raw <-> decoded mappings for all header fields (used for DataFrame rename)
# -----------------------------------------------------------------------------
_RAW_DECODED_PAIRS: list[tuple[str, str]] = [
    # Primary header (Rust snake_case -> decoded)
    (PACKET_VER_NUM_RAW, PACKET_VER_NUM_DECODED),
    (PACKET_TYPE_RAW, PACKET_TYPE_DECODED),
    (SECONDARY_HEADER_RAW, SECONDARY_HEADER_DECODED),
    (PID_RAW, PID_DECODED),
    (PCAT_RAW, PCAT_DECODED),
    (SEQUENCE_FLAGS_RAW, SEQUENCE_FLAGS_DECODED),
    (PACKET_SEQUENCE_COUNT_RAW, PACKET_SEQUENCE_COUNT_DECODED),
    (PACKET_DATA_LEN_RAW, PACKET_DATA_LEN_DECODED),
    # Secondary header (spec codes -> decoded)
    (COARSE_TIME_RAW, COARSE_TIME_DECODED),
    (FINE_TIME_RAW, FINE_TIME_DECODED),
    (SYNC_RAW, SYNC_DECODED),
    (DATA_TAKE_ID_RAW, DATA_TAKE_ID_DECODED),
    (ECC_NUM_RAW, ECC_NUM_DECODED),
    (TEST_MODE_RAW, TEST_MODE_DECODED),
    (RX_CHAN_ID_RAW, RX_CHAN_ID_DECODED),
    (INSTRUMENT_CONFIG_ID_RAW, INSTRUMENT_CONFIG_ID_DECODED),
    (SUBCOM_ANC_DATA_WORD_INDEX_RAW, SUBCOM_ANC_DATA_WORD_INDEX_DECODED),
    (SUBCOM_ANC_DATA_WORD_RAW, SUBCOM_ANC_DATA_WORD_DECODED),
    (SPACE_PACKET_COUNT_RAW, SPACE_PACKET_COUNT_DECODED),
    (PRI_COUNT_RAW, PRI_COUNT_DECODED),
    (ERROR_FLAG_RAW, ERROR_FLAG_DECODED),
    (BAQ_MODE_RAW, BAQ_MODE_DECODED),
    (BAQ_BLOCK_LEN_RAW, BAQ_BLOCK_LEN_DECODED),
    (RANGE_DEC_RAW, RANGE_DEC_DECODED),
    (RX_GAIN_RAW, RX_GAIN_DECODED),
    (TX_RAMP_RATE_RAW, TX_RAMP_RATE_DECODED),
    (TX_PULSE_START_FREQ_RAW, TX_PULSE_START_FREQ_DECODED),
    (TX_PULSE_LEN_RAW, TX_PULSE_LEN_DECODED),
    (RANK_RAW, RANK_DECODED),
    (PRI_RAW, PRI_DECODED),
    (SWST_RAW, SWST_DECODED),
    (SWL_RAW, SWL_DECODED),
    (SAS_SSB_FLAG_RAW, SAS_SSB_FLAG_DECODED),
    (POLARIZATION_RAW, POLARIZATION_DECODED),
    (TEMP_COMP_RAW, TEMP_COMP_DECODED),
    (EBADR_RAW, EBADR_DECODED),
    (ABADR_RAW, ABADR_DECODED),
    (SASTM_RAW, SASTM_DECODED),
    (CALTYP_RAW, CALTYP_DECODED),
    (CBADR_RAW, CBADR_DECODED),
    (CAL_MODE_RAW, CAL_MODE_DECODED),
    (TX_PULSE_NUM_RAW, TX_PULSE_NUM_DECODED),
    (SIGNAL_TYPE_RAW, SIGNAL_TYPE_DECODED),
    (SWAP_FLAG_RAW, SWAP_FLAG_DECODED),
    (SWATH_NUM_RAW, SWATH_NUM_DECODED),
    (NUM_QUADS_RAW, NUM_QUADS_DECODED),
]

RAW_TO_DECODED_NAME: dict[str, str] = {raw: decoded for raw, decoded in _RAW_DECODED_PAIRS}
DECODED_TO_RAW_NAME: dict[str, str] = {
    decoded: raw for raw, decoded in RAW_TO_DECODED_NAME.items()
}
