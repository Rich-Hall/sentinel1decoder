import logging
from typing import List, Tuple

import numpy as np

from sentinel1decoder._bypass_decoder import BypassDecoder
from sentinel1decoder._sample_code import SampleCode
from sentinel1decoder._sentinel1decoder import decode_fdbaq


def to_sample_codes(tuples: List[Tuple[bool, int]]) -> List[SampleCode]:
    """Convert (bool, u8) tuples to SampleCode objects.

    Args:
        tuples: List of (bool, int) tuples

    Returns:
        List of SampleCode objects
    """
    return [SampleCode(1 if sign else 0, mcode) for sign, mcode in tuples]


class UserDataDecoder:
    """Decoder for the user data portion of Sentinel-1 space packets."""

    def __init__(self, data: bytes, baq_mode: int, num_quads: int) -> None:
        if baq_mode not in (0, 3, 4, 5, 12, 13, 14):
            logging.error(f"Unrecognized BAQ mode: {baq_mode}")
            raise Exception(f"Unrecognized BAQ mode: {baq_mode}")

        self.data = data
        self.baq_mode = baq_mode
        self.num_quads = num_quads

    def decode(self) -> np.ndarray:
        """Decode the user data according to the specified encoding mode.

        Refer to SAR Space Protocol Data Unit specification document pg.56.
        Data is encoded in one of four formats:
            - Types A and B (bypass) - samples are encoded as 10-bit words
            - Type C (Block Adaptive Quantization) - samples arranged in blocks
              with an associated 8-bit threshold index. Not expected to be used
              in typical operation.
            - Type D (Flexible Dynamic Block Adaptive Quantization) - similar
              to type C, but the samples are also Huffman encoded. This format
              is the one typically used for radar echo data.

        Returns
        -------
        NumPy array of complex64 decoded samples (interleaved as IE+QE*j, IO+QO*j, ...).
        """

        # The decoding method used depends on the BAQ mode used.
        # The BAQ mode used for this packet is specified in the packet header.
        if self.baq_mode == 0:
            # Bypass data is encoded as a simple list of 10-bit words.
            # No value reconstruction is required in this mode.
            bypass_decoder = BypassDecoder(self.data, self.num_quads)
            IE = bypass_decoder.i_evens
            IO = bypass_decoder.i_odds
            QE = bypass_decoder.q_evens
            QO = bypass_decoder.q_odds

            # Combine channels into interleaved complex samples: IE[i]+QE[i]j, IO[i]+QO[i]j, ...
            # Create flat array with interleaved real/imaginary parts, then view as complex64
            decoded_data = np.zeros(len(IE) * 4, dtype=np.float32)
            decoded_data[0::4] = IE.astype(np.float32)  # real part of even samples
            decoded_data[1::4] = QE.astype(np.float32)  # imag part of even samples
            decoded_data[2::4] = IO.astype(np.float32)  # real part of odd samples
            decoded_data[3::4] = QO.astype(np.float32)  # imag part of odd samples
            decoded_data = decoded_data.view(np.complex64)

        elif self.baq_mode in (3, 4, 5):
            # TODO - Implement Data format type C decoding.
            logging.error("Attempted to decode data format C")
            raise NotImplementedError("Data format C is not implemented yet!")

        elif self.baq_mode in (12, 13, 14):
            # FDBAQ data uses various types of Huffman encoding.
            # Rust implementation returns NumPy array of complex64 directly
            decoded_data = decode_fdbaq(self.data, self.num_quads)

        else:
            logging.error(f"Attempted to decode using invalid BAQ mode: {self.baq_mode}")
            raise ValueError(f"Invalid BAQ mode: {self.baq_mode}")

        return decoded_data
