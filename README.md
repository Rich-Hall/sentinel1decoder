# sentinel1decoder

[![PyPI version](https://badge.fury.io/py/sentinel1decoder.svg)](https://badge.fury.io/py/sentinel1decoder)
[![PyPI](https://img.shields.io/pypi/v/sentinel1decoder)](https://pypi.org/project/sentinel1decoder/)

A Python decoder for Sentinel-1 Level 0 files. The Level 0 format consists of the raw space packets downlinked from the Sentinel-1 spacecraft. This package decodes these packets and produces the raw I/Q sensor output from the SAR instrument, which can then be further processed to focus a SAR image.

An example Jupyter notebook demonstrating the process of decoding Level 0 data and forming an image is available on GitHub [here](https://github.com/Rich-Hall/sentinel1Level0DecodingDemo) or on nbviewer.org [here](https://nbviewer.org/github/Rich-Hall/sentinel1Level0DecodingDemo/blob/main/sentinel1Level0DecodingDemo.ipynb).

This code is based on an implementation in C by jmfriedt, which can be found [here](https://github.com/jmfriedt/sentinel1_level0).

## Performance

**Version 1.1.0** features a complete rewrite of the core decoding functions in Rust, delivering dramatic performance improvements:
- **~80x faster decoding**: Typical burst decoding time reduced to ~30 seconds
- **Multithreaded batch processing**: Multiple packets are decoded in parallel for optimal performance
- **Optimized algorithms**: Improved FDBAQ decoding with lookup tables and efficient bit manipulation

The API remains fully backwards compatible - upgrade to enjoy the performance boost without changing your code.

## Installation

This package is available on [PyPI](https://pypi.org/project/sentinel1decoder/).

In a terminal window:
```bash
pip install sentinel1decoder
```

This package requires Python 3.8 or higher. [NumPy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/) are also required.

## Usage

### High-level API

The `Level0File` class provides a high-level interface that automatically breaks the file into "bursts" (consecutive packets with constant swath number and number of quads) for easy handling. For more fine-grained control, see the [Low-level API](#low-level-api) section below.

Import the package:
```python
import sentinel1decoder
```

Initialize a Level0File object:
```python
l0file = sentinel1decoder.Level0File(filename)
```

This class contains a DataFrame with the packet metadata:
```python
l0file.packet_metadata
```

A DataFrame containing the ephemeris:
```python
l0file.ephemeris
```

The metadata is indexed by burst as well as packet number. Metadata on individual bursts can be accessed via:
```python
l0file.get_burst_metadata(burst)
```

The I/Q array for each burst can be generated via:
```python
iq_data = l0file.get_burst_data(burst)
```

Returns a NumPy array of `complex64` with shape `(slow_time, fast_time)` or `(echo_num, sample_num)`. Each row represents one radar echo return; each column represents a sample within that echo.

By default, this method will attempt to load cached data from an `.npy` file if available (created using `save_burst_data`). You can disable this behavior by passing `try_load_from_file=False`.

This data can be cached in an `.npy` file using:
```python
l0file.save_burst_data(burst)
```

### Low-level API

The individual decoding functions can also be used directly:

Initialize a Level0Decoder object:
```python
decoder = sentinel1decoder.Level0Decoder(filename)
```

Generate a Pandas DataFrame containing the header information associated with the Sentinel-1 downlink packets:
```python
df = decoder.decode_metadata()
```

Decode the satellite ephemeris data from the packet headers:
```python
ephemeris = sentinel1decoder.utilities.read_subcommed_data(df)
```

Extract the data payload from specific packets. This method takes a Pandas DataFrame as input and only decodes packets whose headers are present in the input DataFrame. This allows you to select which packets to decode, rather than always decoding the full file.

The method uses multithreaded batch processing for optimal performance. You can control the batch size (default: 256 packets) using the optional `batch_size` parameter.

For example, to decode only the first 100 packets:
```python
selection = df.iloc[0:100]
iq_array = decoder.decode_packets(selection)
```

Or with a custom batch size:
```python
iq_array = decoder.decode_packets(selection, batch_size=512)
```

Returns a NumPy array of `complex64` with shape `(slow_time, fast_time)` or `(echo_num, sample_num)`. Each row represents one radar echo return; each column represents a sample within that echo.
