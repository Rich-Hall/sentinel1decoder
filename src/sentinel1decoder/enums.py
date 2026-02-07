"""Enums for Sentinel-1 packet metadata fields.

Values are sourced from the SAR Space Protocol Data Unit specification
(S1-IF-ASD-PL-0007, Issue 13, 22.06.2015).
"""

from __future__ import annotations

from enum import Enum

from sentinel1decoder import constants as cnst

# -----------------------------------------------------------------------------
# ECCNumber
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 ECC code / Measurement Mode table (p.19-20)
_ECC_LABELS: dict[int, str] = {
    0: "contingency",
    1: "Stripmap 1",
    2: "Stripmap 2",
    3: "Stripmap 3",
    4: "Stripmap 4",
    5: "Stripmap 5-N",
    6: "Stripmap 6",
    7: "contingency",
    8: "Interferometric Wide Swath",
    9: "Wave Mode",
    10: "Stripmap 5-S",
    11: "Stripmap 1 w/o interl.Cal",
    12: "Stripmap 2 w/o interl.Cal",
    13: "Stripmap 3 w/o interl.Cal",
    14: "Stripmap 4 w/o interl.Cal",
    15: "RFC mode",
    16: "Test Mode Oper / Test Mode Bypass",
    17: "Elevation Notch S3",
    18: "Azimuth Notch S1",
    19: "Azimuth Notch S2",
    20: "Azimuth Notch S3",
    21: "Azimuth Notch S4",
    22: "Azimuth Notch S5-N",
    23: "Azimuth Notch S5-S",
    24: "Azimuth Notch S6",
    25: "Stripmap 5-N w/o interl.Cal",
    26: "Stripmap 5-S w/o interl.Cal",
    27: "Stripmap 6 w/o interl.Cal",
    28: "contingency",
    29: "contingency",
    30: "contingency",
    31: "Elevation Notch S3 w/o interl.Cal",
    32: "Extra Wide Swath",
    33: "Azimuth Notch S1 w/o interl.Cal",
    34: "Azimuth Notch S3 w/o interl.Cal",
    35: "Azimuth Notch S6 w/o interl.Cal",
    36: "contingency",
    37: "Noise Characterisation S1",
    38: "Noise Characterisation S2",
    39: "Noise Characterisation S3",
    40: "Noise Characterisation S4",
    41: "Noise Characterisation S5-N",
    42: "Noise Characterisation S5-S",
    43: "Noise Characterisation S6",
    44: "Noise Characterisation EWS",
    45: "Noise Characterisation IWS",
    46: "Noise Characterisation Wave",
    47: "contingency",
}


class ECCNumber(Enum):
    """ECC number / measurement mode.

    Maps the 8-bit ECC number field in the radar configuration.
    Use .value to get the raw integer code.
    """

    CONTINGENCY_0 = 0  # reserved for ground testing or mode upgrading
    STRIPMAP_1 = 1
    STRIPMAP_2 = 2
    STRIPMAP_3 = 3
    STRIPMAP_4 = 4
    STRIPMAP_5_N = 5  # Stripmap 5 imaging on northern hemisphere
    STRIPMAP_6 = 6
    CONTINGENCY_7 = 7  # reserved for ground testing or mode upgrading
    INTERFEROMETRIC_WIDE_SWATH = 8
    WAVE_MODE = 9  # Leapfrog mode using alternating vignettes at different incidence angles
    STRIPMAP_5_S = 10  # Stripmap 5 imaging on southern hemisphere
    STRIPMAP_1_WO_INTERL_CAL = 11
    STRIPMAP_2_WO_INTERL_CAL = 12
    STRIPMAP_3_WO_INTERL_CAL = 13
    STRIPMAP_4_WO_INTERL_CAL = 14
    RFC_MODE = 15  # RF characterisation mode based on PCC sequences
    TEST_MODE = 16  # Test Mode Oper / Test Mode Bypass (variant defined by TSTMOD)
    ELEVATION_NOTCH_S3 = 17  # Elevation Notch in centre of S3 swath
    AZIMUTH_NOTCH_S1 = 18
    AZIMUTH_NOTCH_S2 = 19
    AZIMUTH_NOTCH_S3 = 20
    AZIMUTH_NOTCH_S4 = 21
    AZIMUTH_NOTCH_S5_N = 22  # Az. Notch Mode in Stripmap 5 on northern hemisphere
    AZIMUTH_NOTCH_S5_S = 23  # Az. Notch Mode in Stripmap 5 on southern hemisphere
    AZIMUTH_NOTCH_S6 = 24
    STRIPMAP_5_N_WO_INTERL_CAL = 25
    STRIPMAP_5_S_WO_INTERL_CAL = 26
    STRIPMAP_6_WO_INTERL_CAL = 27
    CONTINGENCY_28 = 28  # reserved for ground testing or mode upgrading
    CONTINGENCY_29 = 29
    CONTINGENCY_30 = 30
    ELEVATION_NOTCH_S3_WO_INTERL_CAL = 31
    EXTRA_WIDE_SWATH = 32
    AZIMUTH_NOTCH_S1_WO_INTERL_CAL = 33
    AZIMUTH_NOTCH_S3_WO_INTERL_CAL = 34
    AZIMUTH_NOTCH_S6_WO_INTERL_CAL = 35
    CONTINGENCY_36 = 36  # reserved for ground testing or mode upgrading
    NOISE_CHARACTERISATION_S1 = 37
    NOISE_CHARACTERISATION_S2 = 38
    NOISE_CHARACTERISATION_S3 = 39
    NOISE_CHARACTERISATION_S4 = 40
    NOISE_CHARACTERISATION_S5_N = 41
    NOISE_CHARACTERISATION_S5_S = 42
    NOISE_CHARACTERISATION_S6 = 43
    NOISE_CHARACTERISATION_EWS = 44
    NOISE_CHARACTERISATION_IWS = 45
    NOISE_CHARACTERISATION_WAVE = 46
    CONTINGENCY_47 = 47  # reserved for ground testing or mode upgrading

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _ECC_LABELS[self._value_]


# -----------------------------------------------------------------------------
# RxChannelId
# -----------------------------------------------------------------------------
_RX_CHAN_ID_LABELS: dict[int, str] = {
    0: "RxV-Pol Channel",
    1: "RxH-Pol Channel",
}


class RxChannelId(Enum):
    """Rx channel ID."""

    RXV_POL_CHANNEL = 0
    RXH_POL_CHANNEL = 1

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _RX_CHAN_ID_LABELS[self._value_]


# -----------------------------------------------------------------------------
# TestMode
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 TSTMOD (Test Mode) table (3 bits)
# Values 1–3 are invalid per the spec.
_TEST_MODE_LABELS: dict[int, str] = {
    0: "Default (no Test Mode)",
    4: "contingency (ground testing, RxM operational)",
    5: "contingency (ground testing, RxM bypassed)",
    6: "Test Mode Oper",
    7: "Test Mode Bypass",
}


class TestMode(Enum):
    """TSTMOD - Test Mode configuration.

    Maps the 3-bit Test Mode field (Byte 15, bits 1-3).
    Values 1-3 are invalid per the spec; TestMode(1/2/3) will raise ValueError.
    Use .value to get the raw integer code.
    """

    DEFAULT = 0  # no Test Mode
    CONTINGENCY_OPER = 4  # ground testing, RxM operational
    CONTINGENCY_BYPASS = 5  # ground testing, RxM bypassed
    TEST_MODE_OPER = 6
    TEST_MODE_BYPASS = 7

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _TEST_MODE_LABELS[self._value_]


# -----------------------------------------------------------------------------
# BaqMode
# -----------------------------------------------------------------------------
_BAQ_MODE_LABELS: dict[int, str] = {
    0: "BYPASS MODE",
    3: "BAQ 3-BIT MODE",
    4: "BAQ 4-BIT MODE",
    5: "BAQ 5-BIT MODE",
    12: "FDBAQ MODE 0",
    13: "FDBAQ MODE 1",
    14: "FDBAQ MODE 2",
}


class BaqMode(Enum):
    """BAQ Mode."""

    BYPASS_MODE = 0
    BAQ_3_BIT_MODE = 3
    BAQ_4_BIT_MODE = 4
    BAQ_5_BIT_MODE = 5
    FDBAQ_MODE_0 = 12
    FDBAQ_MODE_1 = 13
    FDBAQ_MODE_2 = 14

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _BAQ_MODE_LABELS[self._value_]


# -----------------------------------------------------------------------------
# RangeDecimation
# -----------------------------------------------------------------------------
_RANGE_DEC_LABELS: dict[int, str] = {
    0: "RGDEC 0",
    1: "RGDEC 1",
    3: "RGDEC 3",
    4: "RGDEC 4",
    5: "RGDEC 5",
    6: "RGDEC 6",
    7: "RGDEC 7",
    8: "RGDEC 8",
    9: "RGDEC 9",
    10: "RGDEC 10",
    11: "RGDEC 11",
}

_RANGE_DEC_FILTER_BANDWIDTHS_HZ: dict[int, float] = {
    0: 100e6,
    1: 87.71e6,
    3: 74.25e6,
    4: 59.44e6,
    5: 50.62e6,
    6: 44.89e6,
    7: 22.2e6,
    8: 56.59e6,
    9: 42.86e6,
    10: 15.1e6,
    11: 48.35e6,
}

_RANGE_DEC_FILTER_LENGTHS_SAMPLES: dict[int, int] = {
    0: 28,
    1: 28,
    3: 32,
    4: 40,
    5: 48,
    6: 52,
    7: 92,
    8: 36,
    9: 68,
    10: 120,
    11: 44,
}

_RANGE_DEC_DECIMATION_RATIOS: dict[int, tuple[int, int]] = {
    0: (3, 4),
    1: (2, 3),
    3: (5, 9),
    4: (4, 9),
    5: (3, 8),
    6: (1, 3),
    7: (1, 6),
    8: (3, 7),
    9: (5, 16),
    10: (3, 26),
    11: (4, 11),
}


class RangeDecimation(Enum):
    """RGDEC - Range Decimation."""

    RGDEC_0 = 0
    RGDEC_1 = 1
    RGDEC_3 = 3
    RGDEC_4 = 4
    RGDEC_5 = 5
    RGDEC_6 = 6
    RGDEC_7 = 7
    RGDEC_8 = 8
    RGDEC_9 = 9
    RGDEC_10 = 10
    RGDEC_11 = 11

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _RANGE_DEC_LABELS[self._value_]

    @property
    def sample_rate_hz(self) -> float:
        """Return the sample frequency after decimation in Hz."""
        L, M = _RANGE_DEC_DECIMATION_RATIOS[self._value_]
        return (L / M) * 4 * cnst.F_REF

    @property
    def filter_bandwidth_hz(self) -> float:
        """Return the filter bandwidth in Hz."""
        return _RANGE_DEC_FILTER_BANDWIDTHS_HZ[self._value_]

    @property
    def filter_length_samples(self) -> int:
        """Return the filter length NF in samples."""
        return _RANGE_DEC_FILTER_LENGTHS_SAMPLES[self._value_]

    @property
    def decimation_ratio(self) -> tuple[int, int]:
        """Return the decimation ratio L/M; sample rate = (L/M) * (4 * F_REF)."""
        return _RANGE_DEC_DECIMATION_RATIOS[self._value_]


# -----------------------------------------------------------------------------
# SASSSBFlag
# -----------------------------------------------------------------------------
_SAS_SSB_FLAG_LABELS: dict[int, str] = {
    0: "Imaging or Noise Operation",
    1: "Calibration",
}


class SASSSBFlag(Enum):
    """SAS SSB Flag."""

    IMAGING_OR_NOISE_OPERATION = 0
    CALIBRATION = 1

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _SAS_SSB_FLAG_LABELS[self._value_]


# -----------------------------------------------------------------------------
# Polarisation
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 POLcode (Polarisation) table (3 bits)
_POLARISATION_LABELS: dict[int, str] = {
    0: "Tx H Only",
    1: "Tx H, Rx H",
    2: "Tx H, Rx V",
    3: "Tx H, Rx V+H",
    4: "Tx V Only",
    5: "Tx V, Rx H",
    6: "Tx V, Rx V",
    7: "Tx V, Rx V+H",
}


class Polarisation(Enum):
    """POLcode - polarization configuration.

    Maps the 3-bit Polarisation field (Byte 53, bits 1-3).
    Use .value to get the raw integer code.
    """

    TX_H = 0
    TX_H_RX_H = 1
    TX_H_RX_V = 2
    TX_H_RX_VH = 3
    TX_V = 4
    TX_V_RX_H = 5
    TX_V_RX_V = 6
    TX_V_RX_VH = 7

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _POLARISATION_LABELS[self._value_]


# -----------------------------------------------------------------------------
# TemperatureCompensation
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 TCMPcode (Temperature Compensation) table (2 bits)
_TEMP_COMP_LABELS: dict[int, str] = {
    0: "FE: OFF, TA: OFF",
    1: "FE: ON, TA: OFF",
    2: "FE: OFF, TA: ON",
    3: "FE: ON, TA: ON",
}


class TemperatureCompensation(Enum):
    """TCMPcode - temperature compensation configuration.

    Maps the 2-bit Temperature Compensation field (Byte 53, bits 4-5).
    FE = (Antenna) Front End, TA = Tile Amplifier.
    Use .value to get the raw integer code.
    """

    FE_OFF_TA_OFF = 0
    FE_ON_TA_OFF = 1
    FE_OFF_TA_ON = 2
    FE_ON_TA_ON = 3

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _TEMP_COMP_LABELS[self._value_]


# -----------------------------------------------------------------------------
# SasTestMode
# -----------------------------------------------------------------------------
_SAS_TEST_MODE_LABELS: dict[int, str] = {
    0: "SAS Test Mode active",
    1: "Normal calibration mode",
}


class SasTestMode(Enum):
    """SAS Test Mode."""

    SAS_TEST_MODE_ACTIVE = 0
    NORMAL_CALIBRATION_MODE = 1

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _SAS_TEST_MODE_LABELS[self._value_]


# -----------------------------------------------------------------------------
# CalType
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 CALTYPcode table (3 bits).
# This is a shared enum for S-1A/B and S-1C/D.
_CAL_TYPE_LABELS: dict[int, str] = {
    0: "Tx Cal",
    1: "Rx Cal",
    2: "EPDN Cal",
    3: "Tx Cal Iso (S-1A/B only); TA Cal (S-1C/D only)",
    4: "APDN Cal (S-1A/B only)",
    7: "TxH Cal Iso (S-1A/B only)",
}


class CalType(Enum):
    """CALTYPcode - calibration type (only present when sas_ssbflag == 1).

    Maps the 3-bit Cal Type field (Byte 54-55, bits 12-14).

    Some values are only valid for S-1A/B or S-1C/D.
    """

    TX_CAL = 0
    RX_CAL = 1
    EPDN_CAL = 2
    TX_CAL_ISO_OR_TA_CAL = 3
    APDN_CAL_S1AB_ONLY = 4
    TXH_CAL_ISO_S1AB_ONLY = 7

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _CAL_TYPE_LABELS[self._value_]


# -----------------------------------------------------------------------------
# CalibrationMode
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 CALMODcode table (2 bits)
_CALIBRATION_MODE_LABELS: dict[int, str] = {
    0: "Interleaved Internal Calibration (PCC2)",
    1: "Internal Calibration in Preamble/Postamble (PCC2)",
    2: "Phase Coded Characterisation (PCC32)",
    3: "Phase Coded Characterisation (RF672)",
}


class CalibrationMode(Enum):
    """CALMODcode - calibration mode.

    Maps the 2-bit Calibration Mode field (Byte 56, bits 6-7).
    Use .value to get the raw integer code.
    """

    INTERLEAVED_INTERNAL = 0
    INTERNAL_PREAMBLE_POSTAMBLE = 1
    PHASE_CODED_CHAR_PCC32 = 2
    PHASE_CODED_CHAR_RF672 = 3

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _CALIBRATION_MODE_LABELS[self._value_]


# -----------------------------------------------------------------------------
# SignalType
# -----------------------------------------------------------------------------
# Labels from S1-IF-ASD-PL-0007 SIGTYPcode table (4 bits).
# Values 2-7 and 13-14 are invalid per the spec.
# Some values differ or apply only to S-1A/B or S-1C/D.
_SIGNAL_TYPE_LABELS: dict[int, str] = {
    0: "Echo",
    1: "Noise",
    8: "Tx Cal",
    9: "Rx Cal",
    10: "EPDN Cal",
    11: "TA Cal (S-1A/B only); Tx Cal Iso (S-1C/D only)",
    12: "APDN Cal (S-1A/B only)",
    15: "TxH Cal Iso (S-1A/B only)",
}


class SignalType(Enum):
    """SIGTYPcode - signal type.

    Maps the 4-bit Signal Type field (Byte 57, bits 0-3).
    Values 2-7 and 13-14 are invalid per the spec.
    Some values apply only to S-1A/B or S-1C/D; value 11 has different
    meanings (TA Cal vs Tx Cal Iso).
    Use .value to get the raw integer code.
    """

    ECHO = 0
    NOISE = 1
    TX_CAL = 8
    RX_CAL = 9
    EPDN_CAL = 10
    TA_CAL_OR_TX_CAL_ISO = 11  # TA Cal S-1A/B, Tx Cal Iso S-1C/D
    APDN_CAL_S1AB_ONLY = 12
    TXH_CAL_ISO_S1AB_ONLY = 15

    def __str__(self) -> str:
        """Return the label from the S1-IF-ASD-PL-0007 manual."""
        return _SIGNAL_TYPE_LABELS[self._value_]
