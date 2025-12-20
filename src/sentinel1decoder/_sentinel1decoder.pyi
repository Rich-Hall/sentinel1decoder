"""Type stubs for sentinel1decoder Rust extension module."""

import numpy as np

def decode_fdbaq(
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
