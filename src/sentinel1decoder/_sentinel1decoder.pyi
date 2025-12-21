"""Type stubs for sentinel1decoder Rust extension module."""

from typing import List

import numpy as np

def decode_single_fdbaq_packet(
    data: bytes,
    num_quads: int,
) -> np.ndarray:
    """Decode FDBAQ (Flexible Dynamic Block Adaptive Quantization) data from Sentinel-1 packets.

    This function extracts sample codes from FDBAQ-encoded data, which uses Huffman
    encoding for efficient compression of radar echo data.

    Args:
        data: Raw bytes containing the encoded data
        num_quads: Number of quad samples to decode

    Returns:
        A NumPy array of complex64 representing the decoded samples. The samples are interleaved:
        - complex(IE[0], QE[0]), complex(IO[0], QO[0]), complex(IE[1], QE[1]), complex(IO[1], QO[1]), ...

        The array has shape (num_quads * 2,) and dtype complex64 (which uses float32 for real and imaginary parts).
    """
    ...

def decode_batched_fdbaq_packets(
    packets: List[bytes],
    num_quads: int,
) -> np.ndarray:
    """Decode multiple FDBAQ packets in parallel.

    This function decodes multiple FDBAQ-encoded packets using multithreading for improved performance.

    Args:
        packets: List of raw bytes, each containing encoded data for one packet
        num_quads: Number of quad samples to decode per packet

    Returns:
        A NumPy array of complex64 with shape (num_packets, num_quads * 2). Each row contains
        the decoded samples for one packet, interleaved as IE+QE*j, IO+QO*j, ...
    """
    ...

def decode_single_bypass_packet(
    data: bytes,
    num_quads: int,
) -> np.ndarray:
    """Decode bypass data from Sentinel-1 packets.

    This function decodes bypass-encoded data, where samples are encoded as simple
    10-bit signed integers (1 sign bit + 9 magnitude bits). This is used for
    user data format types A and B ("Bypass" or "Decimation Only").

    Args:
        data: Raw bytes containing the encoded data
        num_quads: Number of quad samples to decode

    Returns:
        A NumPy array of complex64 representing the decoded samples. The samples are interleaved:
        - complex(IE[0], QE[0]), complex(IO[0], QO[0]), complex(IE[1], QE[1]), complex(IO[1], QO[1]), ...

        The array has shape (num_quads * 2,) and dtype complex64.
    """
    ...

def decode_batched_bypass_packets(
    packets: List[bytes],
    num_quads: int,
) -> np.ndarray:
    """Decode multiple bypass packets in parallel.

    This function decodes multiple bypass-encoded packets using multithreading for improved performance.

    Args:
        packets: List of raw bytes, each containing encoded data for one packet
        num_quads: Number of quad samples to decode per packet

    Returns:
        A NumPy array of complex64 with shape (num_packets, num_quads * 2). Each row contains
        the decoded samples for one packet, interleaved as IE+QE*j, IO+QO*j, ...
    """
    ...
