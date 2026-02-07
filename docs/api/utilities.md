# Utilities

Access via `sentinel1decoder.utilities`.

## Column renaming

Convert between raw and parsed metadata column names (see [Raw vs parsed metadata](classes.md#raw-vs-parsed-metadata)):

- **`rename_packet_metadata_columns_to_raw(df: pd.DataFrame)`** → `pd.DataFrame`
  Rename parsed column names to raw (spec-style) names. Only renames columns that are present and have a raw counterpart. No-op if already raw. Does not convert any column data types, *only* renames the columns.

- **`rename_packet_metadata_columns_to_parsed(df: pd.DataFrame)`** → `pd.DataFrame`
  Rename raw column names to human-readable parsed names. Only renames columns that are present and have a parsed counterpart. No-op if already parsed. Does not convert any column data types, only renames the columns.

## Sample rate

- **`range_dec_to_sample_rate(rgdec: int | RangeDecimation)`** → `float`
  Convert a range decimation code (integer or `RangeDecimation` enum) to the sample rate in Hz.

## Ephemeris

- **`read_subcommed_data(df: pd.DataFrame)`** → `pd.DataFrame`
  Decode the ephemeris portion of the sub-commutated ancillary data from the packet headers. Does not decode the full 64-word sub-commutated block; only position, velocity, quaternions, angular rates, and timestamps are extracted. Expects a DataFrame of packet metadata (e.g. from `decode_metadata()` or `Level0File.packet_metadata`).
