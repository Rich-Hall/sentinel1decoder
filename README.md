# sentinel1decoder

[![PyPI version](https://badge.fury.io/py/sentinel1decoder.svg)](https://badge.fury.io/py/sentinel1decoder)
[![PyPI](https://img.shields.io/pypi/v/sentinel1decoder)](https://pypi.org/project/sentinel1decoder/)
[![Documentation](https://readthedocs.org/projects/sentinel1decoder/badge/?version=latest)](https://sentinel1decoder.readthedocs.io)

A Python decoder for Sentinel-1 Level 0 files. The Level 0 format consists of the raw space packets downlinked from the Sentinel-1 spacecraft. This package decodes these packets and produces the raw I/Q sensor output from the SAR instrument, which can then be further processed to focus a SAR image.

An example Jupyter notebook demonstrating the process of decoding Level 0 data and forming an image is available on GitHub [here](https://github.com/Rich-Hall/sentinel1Level0DecodingDemo) or on nbviewer.org [here](https://nbviewer.org/github/Rich-Hall/sentinel1Level0DecodingDemo/blob/main/sentinel1Level0DecodingDemo.ipynb).

This code is based on an implementation in C by jmfriedt, which can be found [here](https://github.com/jmfriedt/sentinel1_level0).

The core decoding functions are implemented in Rust and run multithreaded, so I/Q extraction is quite fast.

## Documentation

**[Full documentation](https://sentinel1decoder.readthedocs.io)** — API reference, ESA spec links, and usage details.

## Installation

```bash
pip install sentinel1decoder
```

Requires Python 3.8+, NumPy, and Pandas.

## Quick start

```python
import sentinel1decoder

l0file = sentinel1decoder.Level0File(filename)
l0file.packet_metadata   # packet metadata
l0file.ephemeris        # satellite ephemeris
iq_data = l0file.get_acquisition_chunk_data(0)  # decode I/Q for acquisition chunk 0
```

## Resources

- [Demo notebook](https://github.com/Rich-Hall/sentinel1Level0DecodingDemo) — decoding Level 0 data and forming an image
