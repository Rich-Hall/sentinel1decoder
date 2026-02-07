# Constants

Access via `sentinel1decoder.constants`. Physical constants and radar parameters used in Sentinel-1 processing.

| Constant | Value | Description |
|----------|-------|-------------|
| `F_REF` | 37.53472224 × 10⁶ | Reference frequency (Hz) used to scale several data fields |
| `SPEED_OF_LIGHT_MPS` | 299792458.0 | Speed of light in m/s |
| `TX_FREQ_HZ` | 5.405 × 10⁹ | Transmit frequency in Hz |
| `TX_WAVELENGTH_M` | c / TX_FREQ_HZ | Transmit wavelength in metres |
| `WGS84_SEMI_MAJOR_AXIS_M` | 6378137 | WGS84 ellipsoid semi-major axis in m |
| `WGS84_SEMI_MINOR_AXIS_M` | 6356752.3142 | WGS84 ellipsoid semi-minor axis in m |

For packet header field names (raw and parsed column identifiers), see `sentinel1decoder._field_names`. That module is considered internal and may change.
