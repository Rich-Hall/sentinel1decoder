import logging

from . import _sample_value_reconstruction as rec
from ._fdbaq_decoder import FDBAQDecoder
from ._sample_code_bypass import decode_bypass_data


class user_data_decoder:
    """Decoder for the user data portion of Sentinel-1 space packets."""

    # Facade design pattern. This class is intended as an interface for the
    # SCode extraction and reconstruction classes. It decodes and reconstructs
    # the IE, IO, QE, QO values from a single space packet.

    def __init__(self, data, baq_mode, num_quads):
        if baq_mode not in (0, 3, 4, 5, 12, 13, 14):
            # TODO: Throw a proper error here
            logging.error(f"Unrecognized BAQ mode: {baq_mode}")

        self.data = data
        self.baq_mode = baq_mode
        self.num_quads = num_quads

    def decode(self):
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
        IE : TYPE
            DESCRIPTION.
        IO : TYPE
            DESCRIPTION.
        QE : TYPE
            DESCRIPTION.
        QO : TYPE
            DESCRIPTION.

        """
        # TODO: Finish docstrings

        # The decoding method used depends on the BAQ mode used.
        # The BAQ mode used for this packet is specified in the packet header.
        if self.baq_mode == 0:
            # Bypass data is encoded as a simple list of 10-bit words.
            # No value reconstruction is required in this mode.

            IE, IO, QE, QO = decode_bypass_data(self.data, self.num_quads)

        elif self.baq_mode in (3, 4, 5):
            # TODO - Implement Data format type C decoding.
            logging.error("Attempted to decode data format C")
            raise NotImplementedError("Data format C is not implemented yet!")

        elif self.baq_mode in (12, 13, 14):
            # FDBAQ data uses various types of Huffman encoding.

            # Sample code extraction happens in FDBAQDedcoder __init__ function
            # The extracted channel SCodes are properties of FDBAQDedcoder
            scode_extractor = FDBAQDecoder(self.data, self.num_quads)
            brcs = scode_extractor.get_brcs
            thidxs = scode_extractor.get_thidxs

            logging.debug(f"Read BRCs: {brcs}")
            logging.debug(f"Read THIDXs: {thidxs}")

            # Huffman-decoded sample codes are grouped into blocks, and can be
            # reconstructed using various lookup tables which cross-reference
            # that Block's Bit-Rate Code (BRC) and Threshold Index (THIDX)
            IE = rec.reconstruct_channel_vals(
                scode_extractor.get_s_ie, brcs, thidxs, self.num_quads
            )
            IO = rec.reconstruct_channel_vals(
                scode_extractor.get_s_io, brcs, thidxs, self.num_quads
            )
            QE = rec.reconstruct_channel_vals(
                scode_extractor.get_s_qe, brcs, thidxs, self.num_quads
            )
            QO = rec.reconstruct_channel_vals(
                scode_extractor.get_s_qo, brcs, thidxs, self.num_quads
            )

        else:
            logging.error(f"Attempted to decode using invalid BAQ mode: {self.baq_mode}")

        # Re-order the even-indexed and odd-indexed sample channels here.
        decoded_data = []
        for i in range(len(IE)):
            decoded_data.append(complex(IE[i], QE[i]))
            decoded_data.append(complex(IO[i], QO[i]))

        return decoded_data
