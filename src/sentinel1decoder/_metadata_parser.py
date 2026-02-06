"""Column-wise conversion of raw packet header columns to decoded (human-readable) form."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from sentinel1decoder import _field_names as fn
from sentinel1decoder import constants as cnst
from sentinel1decoder.enums import (
    BaqMode,
    CalibrationMode,
    CalType,
    ECCNumber,
    Polarisation,
    RangeDecimation,
    RxChannelId,
    SASSSBFlag,
    SasTestMode,
    SignalType,
    TemperatureCompensation,
    TestMode,
)


def _to_float_arr(col: Any) -> np.ndarray:
    """Convert column to float64 array, NaN where None/NA."""
    arr = np.asarray(col, dtype=object)
    out = np.empty(len(arr), dtype=np.float64)
    mask = pd.notna(arr)
    out[mask] = np.asarray(arr[mask], dtype=np.float64)
    out[~mask] = np.nan
    return out


def _enum_column(col: Any, enum_cls: type) -> np.ndarray:
    """Convert column to array of enum values, object dtype with pd.NA where missing."""
    arr = np.asarray(col, dtype=object)
    out = np.empty(len(arr), dtype=object)
    mask = pd.notna(arr)
    int_vals = np.asarray(arr[mask], dtype=np.float64).astype(np.intp)
    out[mask] = [enum_cls(v) for v in int_vals]
    out[~mask] = pd.NA
    return out


def _txprr(col: Any) -> np.ndarray:
    """Decode Tx Ramp Rate."""
    arr = np.asarray(col, dtype=object)
    mask = pd.notna(arr)
    vals = np.where(mask, np.asarray(arr, dtype=np.float64).astype(np.intp), 0)
    sign = (-1) ** (1 - (vals >> 15))
    return np.where(mask, sign * (vals & 0x7FFF) * (cnst.F_REF**2) / (2**21), np.nan)


def _txpsf(col: Any, txprr: np.ndarray) -> np.ndarray:
    """Decode Tx Pulse Start Freq."""
    arr = np.asarray(col, dtype=object)
    mask = pd.notna(arr)
    vals = np.where(mask, np.asarray(arr, dtype=np.float64).astype(np.intp), 0)
    sign = (-1) ** (1 - (vals >> 15))
    additive = np.asarray(txprr, dtype=np.float64) / (4 * cnst.F_REF)
    return np.where(mask, additive + sign * (vals & 0x7FFF) * cnst.F_REF / (2**14), np.nan)


def parse_raw_metadata_columns(columns: dict[str, Any]) -> pd.DataFrame:
    """Parse raw column dict (from Rust decoder) into human-readable decoded DataFrame.

    Converts secondary header columns vectorized: enums, scaled numerics, conditional
    fields. Primary header columns are renamed to decoded names. Preserves row order.

    Args:
        columns: Dict mapping raw column names to list/array of values (one per packet).
                 Keys: primary (e.g. packet_ver_num) and secondary (e.g. TCOAR, BAQMOD).

    Returns:
        DataFrame with decoded column names and appropriate dtypes (enums, float, bool).
    """

    def raw(k: str) -> str:
        return fn.f(k, "raw")

    # ---------------------------------------------------------
    # Datation service
    # ---------------------------------------------------------
    columns[raw("COARSE_TIME")] = pd.array(columns[raw("COARSE_TIME")], dtype="UInt32")
    columns[raw("FINE_TIME")] = (_to_float_arr(columns[raw("FINE_TIME")]) + 0.5) * (2**-16)

    # ---------------------------------------------------------
    # Fixed ancillary data service
    # ---------------------------------------------------------
    columns[raw("SYNC")] = pd.array(columns[raw("SYNC")], dtype="UInt32")
    columns[raw("DATA_TAKE_ID")] = pd.array(columns[raw("DATA_TAKE_ID")], dtype="UInt32")
    columns[raw("ECC_NUM")] = _enum_column(columns[raw("ECC_NUM")], ECCNumber)
    columns[raw("TEST_MODE")] = _enum_column(columns[raw("TEST_MODE")], TestMode)
    columns[raw("RX_CHAN_ID")] = _enum_column(columns[raw("RX_CHAN_ID")], RxChannelId)
    columns[raw("INSTRUMENT_CONFIG_ID")] = pd.array(columns[raw("INSTRUMENT_CONFIG_ID")], dtype="UInt32")

    # ---------------------------------------------------------
    # Sub-commutated ancillary data service
    # ---------------------------------------------------------
    columns[raw("SUBCOM_ANC_DATA_WORD_INDEX")] = pd.array(columns[raw("SUBCOM_ANC_DATA_WORD_INDEX")], dtype="UInt8")
    columns[raw("SUBCOM_ANC_DATA_WORD")] = pd.array(columns[raw("SUBCOM_ANC_DATA_WORD")], dtype="UInt16")

    # ---------------------------------------------------------
    # Counters service
    # ---------------------------------------------------------
    columns[raw("SPACE_PACKET_COUNT")] = pd.array(columns[raw("SPACE_PACKET_COUNT")], dtype="UInt32")
    columns[raw("PRI_COUNT")] = pd.array(columns[raw("PRI_COUNT")], dtype="UInt32")

    # ---------------------------------------------------------
    # Radar configuration support service
    # ---------------------------------------------------------
    columns[raw("ERROR_FLAG")] = _to_float_arr(columns[raw("ERROR_FLAG")]) != 0.0
    columns[raw("BAQ_MODE")] = _enum_column(columns[raw("BAQ_MODE")], BaqMode)
    columns[raw("RANGE_DEC")] = _enum_column(columns[raw("RANGE_DEC")], RangeDecimation)
    columns[raw("RX_GAIN")] = _to_float_arr(columns[raw("RX_GAIN")]) * -0.5
    columns[raw("TX_RAMP_RATE")] = _txprr(columns[raw("TX_RAMP_RATE")])
    columns[raw("TX_PULSE_START_FREQ")] = _txpsf(columns[raw("TX_PULSE_START_FREQ")], columns[raw("TX_RAMP_RATE")])
    columns[raw("TX_PULSE_LEN")] = _to_float_arr(columns[raw("TX_PULSE_LEN")]) / cnst.F_REF
    columns[raw("RANK")] = pd.array(columns[raw("RANK")], dtype="UInt8")
    columns[raw("PRI")] = _to_float_arr(columns[raw("PRI")]) / cnst.F_REF
    columns[raw("SWST")] = _to_float_arr(columns[raw("SWST")]) / cnst.F_REF
    columns[raw("SWL")] = _to_float_arr(columns[raw("SWL")]) / cnst.F_REF

    columns[raw("SAS_SSB_FLAG")] = _enum_column(columns[raw("SAS_SSB_FLAG")], SASSSBFlag)
    columns[raw("POLARIZATION")] = _enum_column(columns[raw("POLARIZATION")], Polarisation)
    columns[raw("TEMP_COMP")] = _enum_column(columns[raw("TEMP_COMP")], TemperatureCompensation)
    columns[raw("EBADR")] = pd.array(columns[raw("EBADR")], dtype="UInt8")
    columns[raw("ABADR")] = pd.array(columns[raw("ABADR")], dtype="UInt16")
    columns[raw("SASTM")] = _enum_column(columns[raw("SASTM")], SasTestMode)
    columns[raw("CALTYP")] = _enum_column(columns[raw("CALTYP")], CalType)
    columns[raw("CBADR")] = pd.array(columns[raw("CBADR")], dtype="UInt16")
    columns[raw("CAL_MODE")] = _enum_column(columns[raw("CAL_MODE")], CalibrationMode)
    columns[raw("TX_PULSE_NUM")] = pd.array(columns[raw("TX_PULSE_NUM")], dtype="UInt8")
    columns[raw("SIGNAL_TYPE")] = _enum_column(columns[raw("SIGNAL_TYPE")], SignalType)
    columns[raw("SWAP_FLAG")] = _to_float_arr(columns[raw("SWAP_FLAG")]) != 0.0

    # Calibration Mode: Don't care when SASSSBFlag==0 and SignalType<2
    columns[raw("CAL_MODE")] = np.where(
        (columns[raw("SAS_SSB_FLAG")] == SASSSBFlag.IMAGING_OR_NOISE_OPERATION)
        & np.isin(columns[raw("SIGNAL_TYPE")], np.array([SignalType.ECHO, SignalType.NOISE])),
        np.full(len(columns[raw("CAL_MODE")]), pd.NA),
        columns[raw("CAL_MODE")],
    )

    # ---------------------------------------------------------
    # Radar sample count service
    # ---------------------------------------------------------
    columns[raw("NUM_QUADS")] = pd.array(columns[raw("NUM_QUADS")], dtype="UInt16")

    # ---------------------------------------------------------
    out_df = pd.DataFrame(columns)
    out_df.rename(columns=fn.RAW_TO_DECODED_NAME, inplace=True)
    return out_df
