# Classes

## Level0File

High-level interface to a Sentinel-1 Level 0 file. Automatically decodes packet metadata on construction and groups packets into acquisition chunks.

### Acquisition chunks

An **acquisition chunk** is a concept we introduce representing a contiguous block of space packets within a Level 0 file that share the same acquisition parameters. Consecutive packets are grouped into the same chunk only when all of the following remain constant from packet to packet:

- Signal type
- Swath number
- Number of quads
- BAQ mode
- SWST (Synthetic Window Start Time)
- SWL (Synthetic Window Length)
- PRI (Pulse Repetition Interval)
- PRI count increments by 1 (wrapping at 2³²−1)
- Azimuth beam address increases monotonically
- Elevation beam address remains constant

When any of these change, a new acquisition chunk begins.

### Raw vs parsed metadata

Packet metadata can use two representations. **Raw** uses spec-style column names (`ECC`, `TSTMOD`, `BAQMOD`, etc.) and keeps integer codes as stored in the packet. **Parsed** uses human-readable column names (`ECC Number`, `Test Mode`, `BAQ Mode`, etc.) and parses the values into enums, scaled floats (e.g. times in seconds), and other physical quantities. Use raw when interfacing with spec-based tools or when you need the unmodified codes; use parsed for readable, physics-ready values. `packet_metadata` and `Level0Decoder.decode_metadata(return_raw=False)` return parsed; `raw_packet_metadata` and `decode_metadata(return_raw=True)` return raw.

```python
from sentinel1decoder import Level0File

l0file = Level0File(filename)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `filename` | `str` | Path to the Level 0 file |
| `packet_metadata` | `pd.DataFrame` | Metadata for all packets, indexed by acquisition chunk and packet number. Parsed representation; see [Raw vs parsed metadata](#raw-vs-parsed-metadata). |
| `raw_packet_metadata` | `pd.DataFrame` | Same metadata in raw form (spec-style names, integer codes). Computed on first access. See [Raw vs parsed metadata](#raw-vs-parsed-metadata). |
| `ephemeris` | `pd.DataFrame` | Sub-commutated satellite ephemeris; computed on first access |
| `acquisition_chunks` | `list[int]` | List of acquisition chunk IDs (0-indexed) in the file |

### Methods

- **`get_acquisition_chunk_metadata(acquisition_chunk: int)`** → `pd.DataFrame`
  Metadata for all packets in the given acquisition chunk.

- **`get_acquisition_chunk_constants(acquisition_chunk: int)`** → `dict[str, Any]`
  Returns a dict of the parameters that define an acquisition chunk (i.e. those that stay constant within a chunk), plus the chunk length: `signal_type`, `swath_num`, `num_quads`, `baq_mode`, `swst`, `swl`, `pri`, `elevation_beam_address`, `num_packets`. Field values other than `num_packets` are taken from the first packet in the chunk; `num_packets` is the number of packets in the chunk.

- **`iter_chunks_matching(**kwargs)`** → `Iterator[int]`
  Yield acquisition chunk IDs whose constants match all given criteria. Each keyword is one of the keys returned by `get_acquisition_chunk_constants`; the value is compared to that constant for the chunk. Supported keywords and expected types:

  | Keyword | Expected type | Description |
  |---------|---------------|-------------|
  | `signal_type` | `SignalType` | Signal type enum (e.g. `SignalType.ECHO`, `SignalType.NOISE`) |
  | `swath_num` | `int` | Swath number |
  | `num_quads` | `int` | Number of quads |
  | `baq_mode` | `BaqMode` | BAQ mode enum (e.g. `BaqMode.BYPASS_MODE`, `BaqMode.BAQ_4_BIT_MODE`, `BaqMode.FDBAQ_MODE_0`) |
  | `swst` | `float` | Synthetic window start time in seconds |
  | `swl` | `float` | Synthetic window length in seconds |
  | `pri` | `float` | Pulse repetition interval in seconds |
  | `elevation_beam_address` | `int` | Elevation beam address |
  | `num_packets` | `int` | Number of packets in the chunk |

  Example: `for chunk in l0file.iter_chunks_matching(signal_type=SignalType.ECHO): ...`

- **`get_chunks_summary()`** → `dict[str, list[int]]`
  Scan every acquisition chunk once and group chunk IDs by signal type and, for IW, by swath. Keys that appear depend on the file; typical names:

  | Key | Contents |
  |-----|----------|
  | `echo` | Echo chunks whose swath is not 10/11/12 (e.g. stripmap) |
  | `echo_swath_10`, `echo_swath_11`, `echo_swath_12` | IW echo chunks for that swath |
  | `noise` / `noise_swath_10` / `noise_swath_11` / `noise_swath_12` | Same split for noise |
  | `cal_rx`, `cal_tx`, `cal_epdn`, `cal_apdn`, `cal_ta_or_txiso`, `cal_tx_iso` | Calibration types |

  Example: `summary = l0file.get_chunks_summary(); iw1 = summary.get("echo_swath_10", [])`

  IW files often include extra short echo chunks (typically 8 packets) with different azimuth beam steering. They are listed with the other echoes of that swath. To keep only the long bursts:

  ```python
  iw1 = [
      c for c in l0file.get_chunks_summary().get("echo_swath_10", [])
      if l0file.get_acquisition_chunk_constants(c)["num_packets"] != 8
  ]
  ```

- **`get_acquisition_chunk_data(acquisition_chunk: int, try_load_from_file: bool = True)`** → `np.ndarray`
  Complex I/Q samples for the acquisition chunk, shape `(num_packets, num_samples)`, dtype `complex64` (two float32 per sample). By default, attempts to load from a cached `.npy` file if present (see below).

- **`save_acquisition_chunk_data(acquisition_chunk: int)`** → `None`
  Save decoded I/Q data to a `.npy` file for faster subsequent loads. The cache file is written next to the source Level 0 file, with the same base path and the suffix `_acquisition_chunk_{id}.npy` (e.g. `S1A_IW_SLC__1SDH_20230101_*.l0` → `S1A_IW_SLC__1SDH_20230101_*_acquisition_chunk_0.npy`).

### Deprecated aliases

The following methods are deprecated aliases for the acquisition-chunk API and will be removed in a future version. Use the corresponding `get_acquisition_chunk_*` or `save_acquisition_chunk_*` methods instead.

| Deprecated | Use instead |
|------------|-------------|
| `get_burst_metadata(burst)` | `get_acquisition_chunk_metadata(acquisition_chunk)` |
| `get_burst_data(burst, try_load_from_file)` | `get_acquisition_chunk_data(acquisition_chunk, try_load_from_file)` |
| `save_burst_data(burst)` | `save_acquisition_chunk_data(acquisition_chunk)` |

---

## Level0Decoder

Low-level decoder for Sentinel-1 Level 0 files. Use when you need fine-grained control over metadata decoding and packet selection.

```python
from sentinel1decoder import Level0Decoder

decoder = Level0Decoder(filename)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `filename` | `str` | Path to the Level 0 file |

### Methods

- **`decode_metadata(return_raw: bool = False)`** → `pd.DataFrame`
  Decode the secondary header of each packet. When `return_raw=False` (default), integer codes are parsed into enums, scaled floats, etc.; when `return_raw=True`, raw spec-style column names and integer codes are returned unchanged. The packet data field consists of a 62-byte secondary header followed by the payload.

- **`decode_packets(input_header: pd.DataFrame, batch_size: int = 256)`** → `np.ndarray`
  Decode radar echoes from the packets whose headers are in `input_header`. The DataFrame must have the structure returned by `decode_metadata()` or `Level0File.packet_metadata` (same columns and MultiIndex). Returns a complex array of shape `(num_packets, num_samples)` with dtype `complex64` (two float32 per sample). Supports bypass, 3/4/5-bit BAQ, and FDBAQ. All packets in `input_header` must share a single BAQ mode.

  `batch_size` controls how many packets are sent to the Rust decoder at once. Within each batch, packets are decoded in parallel (multithreaded). Larger batches increase parallelism and throughput but use more memory; smaller batches reduce memory at the cost of some efficiency. Default 256 is a reasonable balance.

  Not thread-safe: do not call `decode_packets` on the same `Level0Decoder` instance from multiple threads concurrently. Use a separate decoder per thread if decoding in parallel.
