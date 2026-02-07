"""Physical constants and radar parameters for Sentinel-1 processing.

For packet header field names, see sentinel1decoder._field_names.
"""

# Constant used to scale several data fields
F_REF = 37.53472224 * 1e6

# Useful for processing radar data
SPEED_OF_LIGHT_MPS = 299792458.0
TX_FREQ_HZ = 5.405e9
TX_WAVELENGTH_M = SPEED_OF_LIGHT_MPS / TX_FREQ_HZ
WGS84_SEMI_MAJOR_AXIS_M = 6378137
WGS84_SEMI_MINOR_AXIS_M = 6356752.3142
