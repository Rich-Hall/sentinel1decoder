# sentinel1decoder

A Python decoder for Sentinel-1 Level 0 files. Decodes raw space packets downlinked from the Sentinel-1 spacecraft and produces I/Q sensor output from the SAR instrument.

For a worked example of decoding Level 0 data and forming an image, see the [demo notebook](https://github.com/Rich-Hall/sentinel1Level0DecodingDemo) on GitHub.

## Quick start

```python
import sentinel1decoder

l0file = sentinel1decoder.Level0File(filename)

# Packet metadata (indexed by acquisition chunk and packet number)
l0file.packet_metadata

# Ephemeris from sub-commutated auxiliary data
l0file.ephemeris

# Decode I/Q data for an acquisition chunk
iq_data = l0file.get_acquisition_chunk_data(0)
```

## API reference

- [Classes](api/classes.md) — `Level0File`, `Level0Decoder`
- [Utilities](api/utilities.md) — column renaming, sample rate, ephemeris
- [Enums](api/enums.md) — packet metadata enums (BAQ mode, polarisation, etc.)
- [Constants](api/constants.md) — physical constants and radar parameters

## ESA documentation

- [SentiWiki Document Library](https://sentiwiki.copernicus.eu/web/document-library) — Main hub for Sentinel technical documentation.
- [S1-IF-ASD-PL-0007](https://sentiwiki.copernicus.eu/__attachments/1673968/S1-IF-ASD-PL-0007%20-%20Sentinel-1%20SAR%20Space%20Packet%20Protocol%20Data%20Unit%202014%20-%2013.0.pdf?inst-v=48f4e5b4-21dc-4a3c-b262-15dde094f6bd) — SAR Space Packet Protocol Data Unit (S-1A/B; packet header format, sub-commutated data, decoding).
- [S1CD-IF-ASD-IF01-0005](https://sentiwiki.copernicus.eu/__attachments/1673968/S1CD-IF-ASD-IF01-0005-Sentinel-1C-1D-SAR-Space-Packet-Protocol-Data-Unit-2.0.pdf?inst-v=48f4e5b4-21dc-4a3c-b262-15dde094f6bd) — SAR Space Packet Protocol Data Unit (S-1C/D).
- [Copernicus Sentinel-1](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-1) — Mission overview and data access.

## Planned enhancements

- **BAQ mode C** — Decode BAQ 3/4/5-bit compressed echoes (currently only bypass and FDBAQ are supported).
- **Full sub-commutated data** — Decode the complete 64-word sub-commutated ancillary block (e.g. antenna temperatures and other housekeeping) in addition to ephemeris.
