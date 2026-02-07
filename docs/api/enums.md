# Enums

Enum values map to fields in the Sentinel-1 Space Packet secondary header per the SAR Space Protocol Data Unit specification (S1-IF-ASD-PL-0007). Use `.value` for the raw integer; `str(enum_member)` for the spec label.

## ECCNumber

8-bit ECC number / measurement mode identifying the SAR acquisition mode.

| Member | Value |
|--------|-------|
| `CONTINGENCY_0` | 0 |
| `STRIPMAP_1` | 1 |
| `STRIPMAP_2` | 2 |
| `STRIPMAP_3` | 3 |
| `STRIPMAP_4` | 4 |
| `STRIPMAP_5_N` | 5 |
| `STRIPMAP_6` | 6 |
| `CONTINGENCY_7` | 7 |
| `INTERFEROMETRIC_WIDE_SWATH` | 8 |
| `WAVE_MODE` | 9 |
| `STRIPMAP_5_S` | 10 |
| `STRIPMAP_1_WO_INTERL_CAL` | 11 |
| `STRIPMAP_2_WO_INTERL_CAL` | 12 |
| `STRIPMAP_3_WO_INTERL_CAL` | 13 |
| `STRIPMAP_4_WO_INTERL_CAL` | 14 |
| `RFC_MODE` | 15 |
| `TEST_MODE` | 16 |
| `ELEVATION_NOTCH_S3` | 17 |
| `AZIMUTH_NOTCH_S1` | 18 |
| `AZIMUTH_NOTCH_S2` | 19 |
| `AZIMUTH_NOTCH_S3` | 20 |
| `AZIMUTH_NOTCH_S4` | 21 |
| `AZIMUTH_NOTCH_S5_N` | 22 |
| `AZIMUTH_NOTCH_S5_S` | 23 |
| `AZIMUTH_NOTCH_S6` | 24 |
| `STRIPMAP_5_N_WO_INTERL_CAL` | 25 |
| `STRIPMAP_5_S_WO_INTERL_CAL` | 26 |
| `STRIPMAP_6_WO_INTERL_CAL` | 27 |
| `CONTINGENCY_28` | 28 |
| `CONTINGENCY_29` | 29 |
| `CONTINGENCY_30` | 30 |
| `ELEVATION_NOTCH_S3_WO_INTERL_CAL` | 31 |
| `EXTRA_WIDE_SWATH` | 32 |
| `AZIMUTH_NOTCH_S1_WO_INTERL_CAL` | 33 |
| `AZIMUTH_NOTCH_S3_WO_INTERL_CAL` | 34 |
| `AZIMUTH_NOTCH_S6_WO_INTERL_CAL` | 35 |
| `CONTINGENCY_36` | 36 |
| `NOISE_CHARACTERISATION_S1` | 37 |
| `NOISE_CHARACTERISATION_S2` | 38 |
| `NOISE_CHARACTERISATION_S3` | 39 |
| `NOISE_CHARACTERISATION_S4` | 40 |
| `NOISE_CHARACTERISATION_S5_N` | 41 |
| `NOISE_CHARACTERISATION_S5_S` | 42 |
| `NOISE_CHARACTERISATION_S6` | 43 |
| `NOISE_CHARACTERISATION_EWS` | 44 |
| `NOISE_CHARACTERISATION_IWS` | 45 |
| `NOISE_CHARACTERISATION_WAVE` | 46 |
| `CONTINGENCY_47` | 47 |

## RxChannelId

Receive channel ID (vertical or horizontal polarisation).

| Member | Value |
|--------|-------|
| `RXV_POL_CHANNEL` | 0 |
| `RXH_POL_CHANNEL` | 1 |

## TestMode

3-bit TSTMOD field indicating test mode configuration.

| Member | Value |
|--------|-------|
| `DEFAULT` | 0 |
| `CONTINGENCY_OPER` | 4 |
| `CONTINGENCY_BYPASS` | 5 |
| `TEST_MODE_OPER` | 6 |
| `TEST_MODE_BYPASS` | 7 |

## BaqMode

Block Adaptive Quantisation mode used for echo compression.

| Member | Value |
|--------|-------|
| `BYPASS_MODE` | 0 |
| `BAQ_3_BIT_MODE` | 3 |
| `BAQ_4_BIT_MODE` | 4 |
| `BAQ_5_BIT_MODE` | 5 |
| `FDBAQ_MODE_0` | 12 |
| `FDBAQ_MODE_1` | 13 |
| `FDBAQ_MODE_2` | 14 |

## RangeDecimation

RGDEC – range decimation code controlling sample rate and filter parameters.

| Member | Value |
|--------|-------|
| `RGDEC_0` | 0 |
| `RGDEC_1` | 1 |
| `RGDEC_3` | 3 |
| `RGDEC_4` | 4 |
| `RGDEC_5` | 5 |
| `RGDEC_6` | 6 |
| `RGDEC_7` | 7 |
| `RGDEC_8` | 8 |
| `RGDEC_9` | 9 |
| `RGDEC_10` | 10 |
| `RGDEC_11` | 11 |

Each member exposes these properties:

| Property | Type | Description |
|----------|------|-------------|
| `sample_rate_hz` | `float` | Sample frequency after decimation in Hz. Computed as (L/M) × 4 × F_REF where (L, M) is the decimation ratio. Values range from ~15.1 MHz (RGDEC_10) to 100 MHz (RGDEC_0). |
| `filter_bandwidth_hz` | `float` | 3 dB filter bandwidth in Hz (e.g. 100e6 for RGDEC_0, 15.1e6 for RGDEC_10). |
| `filter_length_samples` | `int` | Filter length NF in samples (e.g. 28 for RGDEC_0/1, 120 for RGDEC_10). |
| `decimation_ratio` | `tuple[int, int]` | (L, M) ratio; sample rate = (L/M) × (4 × F_REF). Examples: RGDEC_0 → (3, 4), RGDEC_6 → (1, 3), RGDEC_10 → (3, 26). |

## SASSSBFlag

SAS SSB flag indicating imaging/noise operation vs calibration.

| Member | Value |
|--------|-------|
| `IMAGING_OR_NOISE_OPERATION` | 0 |
| `CALIBRATION` | 1 |

## Polarisation

3-bit POLcode describing transmit and receive polarisation configuration.

| Member | Value |
|--------|-------|
| `TX_H` | 0 |
| `TX_H_RX_H` | 1 |
| `TX_H_RX_V` | 2 |
| `TX_H_RX_VH` | 3 |
| `TX_V` | 4 |
| `TX_V_RX_H` | 5 |
| `TX_V_RX_V` | 6 |
| `TX_V_RX_VH` | 7 |

## TemperatureCompensation

2-bit TCMPcode for Front End (FE) and Tile Amplifier (TA) temperature compensation.

| Member | Value |
|--------|-------|
| `FE_OFF_TA_OFF` | 0 |
| `FE_ON_TA_OFF` | 1 |
| `FE_OFF_TA_ON` | 2 |
| `FE_ON_TA_ON` | 3 |

## SasTestMode

SAS test mode active vs normal calibration mode.

| Member | Value |
|--------|-------|
| `SAS_TEST_MODE_ACTIVE` | 0 |
| `NORMAL_CALIBRATION_MODE` | 1 |

## CalType

3-bit CALTYPcode for calibration type; present when SAS SSB flag indicates calibration. Some members have different meanings depending on whether the data comes from Sentinel-1A/B or Sentinel-1C/D (e.g. value 3 is Tx Cal Iso for S-1A/B and TA Cal for S-1C/D).

| Member | Value |
|--------|-------|
| `TX_CAL` | 0 |
| `RX_CAL` | 1 |
| `EPDN_CAL` | 2 |
| `TX_CAL_ISO_OR_TA_CAL` | 3 |
| `APDN_CAL_S1AB_ONLY` | 4 |
| `TXH_CAL_ISO_S1AB_ONLY` | 7 |

## CalibrationMode

2-bit CALMODcode for calibration mode (interleaved, preamble/postamble, or phase-coded characterisation).

| Member | Value |
|--------|-------|
| `INTERLEAVED_INTERNAL` | 0 |
| `INTERNAL_PREAMBLE_POSTAMBLE` | 1 |
| `PHASE_CODED_CHAR_PCC32` | 2 |
| `PHASE_CODED_CHAR_RF672` | 3 |

## SignalType

4-bit SIGTYPcode for signal type (echo, noise, or calibration variant).

| Member | Value |
|--------|-------|
| `ECHO` | 0 |
| `NOISE` | 1 |
| `TX_CAL` | 8 |
| `RX_CAL` | 9 |
| `EPDN_CAL` | 10 |
| `TA_CAL_OR_TX_CAL_ISO` | 11 |
| `APDN_CAL_S1AB_ONLY` | 12 |
| `TXH_CAL_ISO_S1AB_ONLY` | 15 |
