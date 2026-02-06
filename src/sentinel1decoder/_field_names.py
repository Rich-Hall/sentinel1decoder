"""Header field name definitions for Sentinel-1 packet metadata.

This module defines the mapping between raw (spec-style) and decoded (human-readable)
field names for primary and secondary header fields.

Field definitions are stored in a dict-of-dicts structure (FIELDS), with a helper
function `field_name()` for convenient access.
"""

from typing import Dict, Literal, overload

# -----------------------------------------------------------------------------
# Field definitions as dict-of-dicts
# Format: "KEY": {"decoded": "Human Readable Name", "raw": "SPECNAME"}
# Primary/subcommed fields only have "decoded", secondary fields have both
# -----------------------------------------------------------------------------

FIELDS: Dict[str, Dict[str, str]] = {
    # -------------------------------------------------------------------------
    # Packet metadata dataframe indices (not part of headers)
    # -------------------------------------------------------------------------
    "PACKET_NUM": {"decoded": "Packet Number"},
    "ACQUISITION_CHUNK_NUM": {"decoded": "Acquisition Chunk"},
    # -------------------------------------------------------------------------
    # Primary header fields
    # -------------------------------------------------------------------------
    "PACKET_VER_NUM": {"decoded": "Packet Version Number"},
    "PACKET_TYPE": {"decoded": "Packet Type"},
    "SECONDARY_HEADER": {"decoded": "Secondary Header Flag"},
    "PID": {"decoded": "PID"},
    "PCAT": {"decoded": "PCAT"},
    "SEQUENCE_FLAGS": {"decoded": "Sequence Flags"},
    "PACKET_SEQUENCE_COUNT": {"decoded": "Packet Sequence Count"},
    "PACKET_DATA_LEN": {"decoded": "Packet Data Length"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Datation service
    # -------------------------------------------------------------------------
    "COARSE_TIME": {"raw": "TCOAR", "decoded": "Coarse Time"},
    "FINE_TIME": {"raw": "TFINE", "decoded": "Fine Time"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Fixed ancillary data
    # -------------------------------------------------------------------------
    "SYNC": {"raw": "SYNC", "decoded": "Sync"},
    "DATA_TAKE_ID": {"raw": "DTID", "decoded": "Data Take ID"},
    "ECC_NUM": {"raw": "ECC", "decoded": "ECC Number"},
    "TEST_MODE": {"raw": "TSTMOD", "decoded": "Test Mode"},
    "RX_CHAN_ID": {"raw": "RXCHID", "decoded": "Rx Channel ID"},
    "INSTRUMENT_CONFIG_ID": {"raw": "ICID", "decoded": "Instrument Configuration ID"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Sub-commutated ancillary data
    # -------------------------------------------------------------------------
    "SUBCOM_ANC_DATA_WORD_INDEX": {"raw": "ADWIDX", "decoded": "Sub-commutated Ancilliary Data Word Index"},
    "SUBCOM_ANC_DATA_WORD": {"raw": "ADW", "decoded": "Sub-commutated Ancilliary Data Word"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Counters service
    # -------------------------------------------------------------------------
    "SPACE_PACKET_COUNT": {"raw": "SPCT", "decoded": "Space Packet Count"},
    "PRI_COUNT": {"raw": "PRICT", "decoded": "PRI Count"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Radar configuration support service
    # -------------------------------------------------------------------------
    "ERROR_FLAG": {"raw": "ERRFLG", "decoded": "Error Flag"},
    "BAQ_MODE": {"raw": "BAQMOD", "decoded": "BAQ Mode"},
    "BAQ_BLOCK_LEN": {"raw": "BAQBL", "decoded": "BAQ Block Length"},
    "RANGE_DEC": {"raw": "RGDEC", "decoded": "Range Decimation"},
    "RX_GAIN": {"raw": "RXG", "decoded": "Rx Gain"},
    "TX_RAMP_RATE": {"raw": "TXPRR", "decoded": "Tx Ramp Rate"},
    "TX_PULSE_START_FREQ": {"raw": "TXPSF", "decoded": "Tx Pulse Start Frequency"},
    "TX_PULSE_LEN": {"raw": "TXPL", "decoded": "Tx Pulse Length"},
    "RANK": {"raw": "RANK", "decoded": "Rank"},
    "PRI": {"raw": "PRI", "decoded": "PRI"},
    "SWST": {"raw": "SWST", "decoded": "SWST"},
    "SWL": {"raw": "SWL", "decoded": "SWL"},
    "SAS_SSB_FLAG": {"raw": "SSBFLAG", "decoded": "SAS SSB Flag"},
    "POLARIZATION": {"raw": "POL", "decoded": "Polarisation"},
    "TEMP_COMP": {"raw": "TCMP", "decoded": "Temperature Compensation"},
    "EBADR": {"raw": "EBADR", "decoded": "Elevation Beam Address"},
    "ABADR": {"raw": "ABADR", "decoded": "Azimuth Beam Address"},
    "SASTM": {"raw": "SASTM", "decoded": "SAS Test Mode"},
    "CALTYP": {"raw": "CALTYP", "decoded": "Cal Type"},
    "CBADR": {"raw": "CBADR", "decoded": "Calibration Beam Address"},
    "CAL_MODE": {"raw": "CALMOD", "decoded": "Calibration Mode"},
    "TX_PULSE_NUM": {"raw": "TXPNO", "decoded": "Tx Pulse Number"},
    "SIGNAL_TYPE": {"raw": "SIGTYP", "decoded": "Signal Type"},
    "SWAP_FLAG": {"raw": "SWAP", "decoded": "Swap Flag"},
    "SWATH_NUM": {"raw": "SWATH", "decoded": "Swath Number"},
    # -------------------------------------------------------------------------
    # Secondary header fields - Radar sample count service
    # -------------------------------------------------------------------------
    "NUM_QUADS": {"raw": "NQ", "decoded": "Number of Quads"},
    # -------------------------------------------------------------------------
    # Subcommutated data fields (ephemeris/attitude)
    # -------------------------------------------------------------------------
    "X_POS": {"decoded": "X-axis position ECEF"},
    "Y_POS": {"decoded": "Y-axis position ECEF"},
    "Z_POS": {"decoded": "Z-axis position ECEF"},
    "X_VEL": {"decoded": "X-axis velocity ECEF"},
    "Y_VEL": {"decoded": "Y-axis velocity ECEF"},
    "Z_VEL": {"decoded": "Z-axis velocity ECEF"},
    "POD_SOLN_DATA_TIMESTAMP": {"decoded": "POD Solution Data Timestamp"},
    "Q0": {"decoded": "Q0 Attitude Quaternion"},
    "Q1": {"decoded": "Q1 Attitude Quaternion"},
    "Q2": {"decoded": "Q2 Attitude Quaternion"},
    "Q3": {"decoded": "Q3 Attitude Quaternion"},
    "X_ANG_RATE": {"decoded": "Omega-X Angular Rate"},
    "Y_ANG_RATE": {"decoded": "Omega-Y Angular Rate"},
    "Z_ANG_RATE": {"decoded": "Omega-Z Angular Rate"},
    "ATTITUDE_DATA_TIMESTAMP": {"decoded": "Attitude Data Timestamp"},
}


# -----------------------------------------------------------------------------
# Helper function to access field names
# -----------------------------------------------------------------------------
@overload
def field_name(key: str) -> str: ...
@overload
def field_name(key: str, variant: Literal["decoded"]) -> str: ...
@overload
def field_name(key: str, variant: Literal["raw"]) -> str: ...


def field_name(key: str, variant: str = "decoded") -> str:
    """Get a field name by key and variant.

    Args:
        key: The field key (e.g., "ECC_NUM", "BAQ_MODE").
        variant: Either "decoded" (human-readable, default) or "raw" (spec-style).

    Returns:
        The field name string.

    Raises:
        KeyError: If the key doesn't exist or the variant isn't available for that key.

    Examples:
        >>> field_name("ECC_NUM")
        'ECC Number'
        >>> field_name("ECC_NUM", "raw")
        'ECC'
    """
    return FIELDS[key][variant]


# Short alias for convenience
f = field_name


# -----------------------------------------------------------------------------
# Primary header keys (for splitting raw vs secondary in packet metadata DataFrame)
# -----------------------------------------------------------------------------
PRIMARY_HEADER_KEYS: tuple = (
    "PACKET_VER_NUM",
    "PACKET_TYPE",
    "SECONDARY_HEADER",
    "PID",
    "PCAT",
    "SEQUENCE_FLAGS",
    "PACKET_SEQUENCE_COUNT",
    "PACKET_DATA_LEN",
)

# -----------------------------------------------------------------------------
# Derived mappings for column renaming
# -----------------------------------------------------------------------------
DECODED_TO_RAW_NAME: Dict[str, str] = {entry["decoded"]: entry["raw"] for entry in FIELDS.values() if "raw" in entry}

RAW_TO_DECODED_NAME: Dict[str, str] = {entry["raw"]: entry["decoded"] for entry in FIELDS.values() if "raw" in entry}
