# sentinel1decoder
Python decoder for Sentinel-1 level0 files. The level0 format consists of the raw space packets downlinked from the Sentinel-1 spacecraft. This package decodes these and produces the raw I/Q sensor output from the SAR instrument, which can then be further processed to focus a SAR image. An example Jupyter notebook which runs through the process of decoding Level 0 data and forming an image is available on github [here](https://github.com/Rich-Hall/sentinel1Level0DecodingDemo) or nbviewer.org [here](https://nbviewer.org/github/Rich-Hall/sentinel1Level0DecodingDemo/blob/main/sentinel1Level0DecodingDemo.ipynb).

This code is heavily based on an implementation in C by jmfriedt which can be found [here](https://github.com/jmfriedt/sentinel1_level0).

## Installation

In a terminal window:
```
pip install sentinel1decoder
```
[Numpy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/) are also required.

## Usage

Import the package:
```
import sentinel1decoder
```

The Level0File class wraps most of the below functionality, while also breaking the file into bursts of constant swath number/number of quads, to allow for easy handling.

Initialize a Level0File object:
```
l0file = sentinel1decoder.Level0File( filename )
```

This class contains: a dataframe containing the packet metadata:
```
l0file.packet_metadata
```

A dataframe containing the ephemeris:
```
l0file.ephemeris
```

The metadata is indexed by burst as well as packet number. Metadata on individual bursts can be accessed via:
```
l0file.get_burst_metadata( burst )
```

The I/Q array for each burst can be generated via:
```
l0file.get_burst_data( burst )
```

Importantly, this data can now be cached in an `.npy` file using:
```
l0file.save_burst_data( burst )
```

--------------------------------------------

The individual decoding functions can still be used:

Initialize a Level0Decoder object:
```
decoder = sentinel1decoder.Level0Decoder( filename )
```

Generate a Pandas dataframe containing the header information associated with the Sentinel-1 downlink packets contained in the file:
```
df = decoder.decode_metadata()
```

Further decode the satellite ephemeris data from the information in the packet headers:
```
ephemeris = sentinel1decoder.utilities.read_subcommed_data(df)
```

Extract the data payload from the data packets in the file. Takes a Pandas dataframe as an input, and only decodes packets whose header is present in the input dataframe. The intended usage of this is to allow the user to select which packets to decode, rather than having to always decode the full file. For example, to decode the first 100 packets only:
```
selection = df.iloc[0:100]
iq_array = decoder.decode_packets(selection)
```
