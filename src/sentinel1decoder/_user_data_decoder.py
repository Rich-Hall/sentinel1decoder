import logging
from typing import List, Tuple

from sentinel1decoder._bypass_decoder import BypassDecoder
from sentinel1decoder._sample_code import SampleCode
from sentinel1decoder._sample_value_reconstruction import reconstruct_channel_vals
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

    def decode(self) -> List[complex]:
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
        Complex array of decoded samples.
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

        elif self.baq_mode in (3, 4, 5):
            # TODO - Implement Data format type C decoding.
            logging.error("Attempted to decode data format C")
            raise NotImplementedError("Data format C is not implemented yet!")

        elif self.baq_mode in (12, 13, 14):
            # FDBAQ data uses various types of Huffman encoding.

            # Rust implementation of FDBAQ decoder
            # Returns BRCs, THIDXs, and sample codes as tuples of (bool, u8)
            brcs, thidxs, s_ie, s_io, s_qe, s_qo = decode_fdbaq(self.data, self.num_quads)

            logging.debug(f"Read BRCs: {brcs}")
            logging.debug(f"Read THIDXs: {thidxs}")

            # Huffman-decoded sample codes are grouped into blocks, and can be
            # reconstructed using various lookup tables which cross-reference
            # that Block's Bit-Rate Code (BRC) and Threshold Index (THIDX)
            IE = reconstruct_channel_vals(to_sample_codes(s_ie), brcs, thidxs, self.num_quads)
            IO = reconstruct_channel_vals(to_sample_codes(s_io), brcs, thidxs, self.num_quads)
            QE = reconstruct_channel_vals(to_sample_codes(s_qe), brcs, thidxs, self.num_quads)
            QO = reconstruct_channel_vals(to_sample_codes(s_qo), brcs, thidxs, self.num_quads)

        else:
            logging.error(f"Attempted to decode using invalid BAQ mode: {self.baq_mode}")

        # Re-order the even-indexed and odd-indexed sample channels here.
        decoded_data = []
        for i in range(len(IE)):
            decoded_data.append(complex(IE[i], QE[i]))
            decoded_data.append(complex(IO[i], QO[i]))

        return decoded_data
