# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-07

### Acquisition Chunks
- **Acquisition chunk API**: New terminology replaces "burst" with "acquisition chunk", avoiding confusion with ESA's slightly different meaning for the term "burst" and reflecting a more precise grouping of packets (constant signal type, swath, quads, BAQ mode, SWST, SWL, PRI, PRI count increments, azimuth beam, elevation beam).
- Acquisition chunks are calculated with slightly stricter requirements than bursts, fixing an issue where bursts were invalid for decoding due to multiple data types.
- New methods: `get_acquisition_chunk_metadata`, `get_acquisition_chunk_constants`, `get_acquisition_chunk_data`, `save_acquisition_chunk_data`, `iter_chunks_matching`.

### Packet Metadata
- **Header data** is now decoded in rust for better performance.
- We now fully parse header data fields, and make available a separate method for producing the "raw" data containing pure ints. Several new enums have been added to support this.
- New **helper methods** on Level0File for iterating over acquisition chunks with particular qualities use these enums.

### Deprecated
- `get_burst_metadata`, `get_burst_data`, `save_burst_data` — use the acquisition-chunk equivalents. These will be removed in a future version but are included for backward compatibility.

### Documentation
- New `docs/` structure with API reference (classes, utilities, enums, constants).
- ESA spec links (SentiWiki, S-1A/B and S-1C/D SAR Space Packet specs).
- Simplified README with quick start and link to full documentation.

## [1.1.1] - 2026-01-03
- Fixed an issue where the version number shown by `pip show` did not match `sentinel1decoder.__version__`

## [1.1.0] - 2025-12-21

### Features
- *Significant* optimization of the core decoding functions
    - Notional decoding time for a burst down to ~30 seconds (was ~40 mins)

### Technical Details
- FDBAQ and Bypass decoding functions moved from Python to Rust
- We now batch multiple packets together and multithread their decoding
- Improved FDBAQ decoding logic based upon constructed lookup tables
- We now explicitly return complex64 (i.e. float32s) type data

### Documentation
- Rewrote main readme

## [1.0.0] - 2025-06-25

### Added
- **Initial PyPI release**: First official release available via `pip install sentinel1decoder`
- This baseline features:
    - **Level0File class**: High-level interface for processing Sentinel-1 Level 0 files
        - Automatic burst detection and organization of packet metadata
        - Caching support for burst data using `.npy` files
        - Lazy loading of ephemeris data
        - Burst-based data access methods
    - **Level0Decoder class**: Core decoding functionality
        - Decode Sentinel-1 Level 0 space packet metadata
        - Extract I/Q data from SAR instrument packets
        - Selective packet decoding capabilities
    - **Utilities module**:
        - Sub-commutated data extraction for satellite ephemeris
        - Helper functions for data processing
    - **Constants module**: Centralized constants and field names
    - **Rust backend**: Basic PyO3 integration for future performance optimizations


### Features
- Support for Sentinel-1 Level 0 file format processing
- Automatic burst detection based on swath number and quad count consistency
- Packet metadata extraction
- Satellite ephemeris data extraction
- Complex I/Q data output for SAR image formation

### Technical Details
- Python 3.8+ compatibility
- NumPy and Pandas dependencies
- Comprehensive test suite
- Pre-commit hooks for code quality
- Automated CI/CD pipeline for PyPI publishing

### Documentation
- Comprehensive README with usage examples
- Jupyter notebook demonstration available
- Type annotations for all public APIs
- Inline documentation for all classes and methods

---

## [Unreleased]

### Planned
- BAQ mode C (3/4/5-bit) decoding
- Full sub-commutated data decoding

[2.0.0]: https://github.com/Rich-Hall/sentinel1decoder/releases/tag/v2.0.0
[1.1.1]: https://github.com/Rich-Hall/sentinel1decoder/releases/tag/v1.1.1
[1.1.0]: https://github.com/Rich-Hall/sentinel1decoder/releases/tag/v1.1.0
[1.0.0]: https://github.com/Rich-Hall/sentinel1decoder/releases/tag/v1.0.0
