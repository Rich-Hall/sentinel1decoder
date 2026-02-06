"""Sentinel-1 decoder package."""

from . import constants, utilities
from .enums import (
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
from .l0decoder import Level0Decoder
from .l0file import Level0File

__version__ = "1.1.1"

__all__ = [
    # Decoders
    "Level0Decoder",
    "Level0File",
    # Utilities
    "utilities",
    # Constants
    "constants",
    # Enums
    "ECCNumber",
    "RxChannelId",
    "TestMode",
    "BaqMode",
    "RangeDecimation",
    "SASSSBFlag",
    "Polarisation",
    "TemperatureCompensation",
    "SasTestMode",
    "CalType",
    "CalibrationMode",
    "SignalType",
]
