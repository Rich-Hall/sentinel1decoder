"""Type stubs for sentinel1decoder Rust extension module."""

from typing import List, Tuple

def decode_fdbaq(
    data: bytes,
    num_quads: int,
) -> Tuple[
    List[int], List[int], List[Tuple[bool, int]], List[Tuple[bool, int]], List[Tuple[bool, int]], List[Tuple[bool, int]]
]:
    """Decode FDBAQ (Flexible Dynamic Block Adaptive Quantization) data from Sentinel-1 packets.

    Args:
        data: Raw bytes containing the encoded data
        num_quads: Number of quad samples to decode

    Returns:
        A tuple containing (brcs, thidxs, s_ie, s_io, s_qe, s_qo) where:
        - brcs: Bit Rate Codes for each block (list of int)
        - thidxs: Threshold Index codes for each block (list of int)
        - s_ie: Even-indexed I channel sample codes (list of (sign: bool, magnitude: int) tuples)
        - s_io: Odd-indexed I channel sample codes (list of (sign: bool, magnitude: int) tuples)
        - s_qe: Even-indexed Q channel sample codes (list of (sign: bool, magnitude: int) tuples)
        - s_qo: Odd-indexed Q channel sample codes (list of (sign: bool, magnitude: int) tuples)
    """
    ...
