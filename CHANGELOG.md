# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Rust-based performance-critical components
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
- Performance optimizations
- Additional decoder implementations
- Enhanced error handling
- Extended documentation

[1.0.0]: https://github.com/Rich-Hall/sentinel1decoder/releases/tag/v1.0.0 