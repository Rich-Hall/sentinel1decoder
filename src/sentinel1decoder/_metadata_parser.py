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
    vals = np.zeros(len(arr), dtype=np.intp)
    vals[mask] = np.asarray(arr[mask], dtype=np.float64).astype(np.intp)
    sign = (-1) ** (1 - (vals >> 15))
    return np.where(mask, sign * (vals & 0x7FFF) * (cnst.F_REF**2) / (2**21), np.nan)


def _txpsf(col: Any, txprr: np.ndarray) -> np.ndarray:
    """Decode Tx Pulse Start Freq."""
    arr = np.asarray(col, dtype=object)
    mask = pd.notna(arr)
    vals = np.zeros(len(arr), dtype=np.intp)
    vals[mask] = np.asarray(arr[mask], dtype=np.float64).astype(np.intp)
    sign = (-1) ** (1 - (vals >> 15))
    additive = np.asarray(txprr, dtype=np.float64) / (4 * cnst.F_REF)
    return np.where(mask, additive + sign * (vals & 0x7FFF) * cnst.F_REF / (2**14), np.nan)


def parse_raw_metadata_columns(columns: dict[str, Any]) -> pd.DataFrame:
    """Parse raw column dict (from Rust decoder) into human-readable decoded DataFrame.

    Converts secondary header columns vectorized: enums, scaled numerics, conditional
    fields. Primary header columns are renamed to decoded names. Preserves row order.

    Args:
        columns: Dict mapping raw column names to list/array of values (one per packet).
                 Keys: primary (snake_case, e.g. packet_ver_num) and secondary (spec codes,
                 e.g. TCOAR, BAQMOD). All are renamed to decoded names via RAW_TO_DECODED_NAME.

    Returns:
        DataFrame with decoded column names and appropriate dtypes (enums, float, bool).
    """

    # ---------------------------------------------------------
    # Datation service
    # ---------------------------------------------------------
    columns[fn.COARSE_TIME_RAW] = pd.array(columns[fn.COARSE_TIME_RAW], dtype="UInt32")
    columns[fn.FINE_TIME_RAW] = (_to_float_arr(columns[fn.FINE_TIME_RAW]) + 0.5) * (2**-16)

    # ---------------------------------------------------------
    # Fixed ancillary data service
    # ---------------------------------------------------------
    columns[fn.SYNC_RAW] = pd.array(columns[fn.SYNC_RAW], dtype="UInt32")
    columns[fn.DATA_TAKE_ID_RAW] = pd.array(columns[fn.DATA_TAKE_ID_RAW], dtype="UInt32")
    columns[fn.ECC_NUM_RAW] = _enum_column(columns[fn.ECC_NUM_RAW], ECCNumber)
    columns[fn.TEST_MODE_RAW] = _enum_column(columns[fn.TEST_MODE_RAW], TestMode)
    columns[fn.RX_CHAN_ID_RAW] = _enum_column(columns[fn.RX_CHAN_ID_RAW], RxChannelId)
    columns[fn.INSTRUMENT_CONFIG_ID_RAW] = pd.array(columns[fn.INSTRUMENT_CONFIG_ID_RAW], dtype="UInt32")

    # ---------------------------------------------------------
    # Sub-commutated ancillary data service
    # ---------------------------------------------------------
    columns[fn.SUBCOM_ANC_DATA_WORD_INDEX_RAW] = pd.array(columns[fn.SUBCOM_ANC_DATA_WORD_INDEX_RAW], dtype="UInt8")
    columns[fn.SUBCOM_ANC_DATA_WORD_RAW] = pd.array(columns[fn.SUBCOM_ANC_DATA_WORD_RAW], dtype="UInt16")

    # ---------------------------------------------------------
    # Counters service
    # ---------------------------------------------------------
    columns[fn.SPACE_PACKET_COUNT_RAW] = pd.array(columns[fn.SPACE_PACKET_COUNT_RAW], dtype="UInt32")
    columns[fn.PRI_COUNT_RAW] = pd.array(columns[fn.PRI_COUNT_RAW], dtype="UInt32")

    # ---------------------------------------------------------
    # Radar configuration support service
    # ---------------------------------------------------------
    columns[fn.ERROR_FLAG_RAW] = _to_float_arr(columns[fn.ERROR_FLAG_RAW]) != 0.0
    columns[fn.BAQ_MODE_RAW] = _enum_column(columns[fn.BAQ_MODE_RAW], BaqMode)
    columns[fn.RANGE_DEC_RAW] = _enum_column(columns[fn.RANGE_DEC_RAW], RangeDecimation)
    columns[fn.RX_GAIN_RAW] = _to_float_arr(columns[fn.RX_GAIN_RAW]) * -0.5
    columns[fn.TX_RAMP_RATE_RAW] = _txprr(columns[fn.TX_RAMP_RATE_RAW])
    columns[fn.TX_PULSE_START_FREQ_RAW] = _txpsf(columns[fn.TX_PULSE_START_FREQ_RAW], columns[fn.TX_RAMP_RATE_RAW])
    columns[fn.TX_PULSE_LEN_RAW] = _to_float_arr(columns[fn.TX_PULSE_LEN_RAW]) / cnst.F_REF
    columns[fn.RANK_RAW] = pd.array(columns[fn.RANK_RAW], dtype="UInt8")
    columns[fn.PRI_RAW] = _to_float_arr(columns[fn.PRI_RAW]) / cnst.F_REF
    columns[fn.SWST_RAW] = _to_float_arr(columns[fn.SWST_RAW]) / cnst.F_REF
    columns[fn.SWL_RAW] = _to_float_arr(columns[fn.SWL_RAW]) / cnst.F_REF

    columns[fn.SAS_SSB_FLAG_RAW] = _enum_column(columns[fn.SAS_SSB_FLAG_RAW], SASSSBFlag)
    columns[fn.POLARIZATION_RAW] = _enum_column(columns[fn.POLARIZATION_RAW], Polarisation)
    columns[fn.TEMP_COMP_RAW] = _enum_column(columns[fn.TEMP_COMP_RAW], TemperatureCompensation)
    columns[fn.EBADR_RAW] = pd.array(columns[fn.EBADR_RAW], dtype="UInt8")
    columns[fn.ABADR_RAW] = pd.array(columns[fn.ABADR_RAW], dtype="UInt16")
    columns[fn.SASTM_RAW] = _enum_column(columns[fn.SASTM_RAW], SasTestMode)
    columns[fn.CALTYP_RAW] = _enum_column(columns[fn.CALTYP_RAW], CalType)
    columns[fn.CBADR_RAW] = pd.array(columns[fn.CBADR_RAW], dtype="UInt16")
    columns[fn.CAL_MODE_RAW] = _enum_column(columns[fn.CAL_MODE_RAW], CalibrationMode)
    columns[fn.TX_PULSE_NUM_RAW] = pd.array(columns[fn.TX_PULSE_NUM_RAW], dtype="UInt8")
    columns[fn.SIGNAL_TYPE_RAW] = _enum_column(columns[fn.SIGNAL_TYPE_RAW], SignalType)
    columns[fn.SWAP_FLAG_RAW] = _to_float_arr(columns[fn.SWAP_FLAG_RAW]) != 0.0

    # Calibration Mode: Don't care when SASSSBFlag==0 and SignalType<2
    columns[fn.CAL_MODE_RAW] = np.where(
        (columns[fn.SAS_SSB_FLAG_RAW] == SASSSBFlag.IMAGING_OR_NOISE_OPERATION)
        & np.isin(columns[fn.SIGNAL_TYPE_RAW], np.array([SignalType.ECHO, SignalType.NOISE])),
        np.full(len(columns[fn.CAL_MODE_RAW]), pd.NA),
        columns[fn.CAL_MODE_RAW],
    )

    # ---------------------------------------------------------
    # Radar sample count service
    # ---------------------------------------------------------
    columns[fn.NUM_QUADS_RAW] = pd.array(columns[fn.NUM_QUADS_RAW], dtype="UInt16")

    # ---------------------------------------------------------
    out_df = pd.DataFrame(columns)
    out_df.rename(columns=fn.RAW_TO_DECODED_NAME, inplace=True)
    return out_df
