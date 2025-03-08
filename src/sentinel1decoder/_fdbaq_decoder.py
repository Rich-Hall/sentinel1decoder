import logging
import math
from typing import List, Tuple, TypeVar, Union

from sentinel1decoder._sample_code import SampleCode

_TREE_BRC_ZERO = (0, (1, (2, 3)))
_TREE_BRC_ONE = (0, (1, (2, (3, 4))))
_TREE_BRC_TWO = (0, (1, (2, (3, (4, (5, 6))))))
_TREE_BRC_THREE = ((0, 1), (2, (3, (4, (5, (6, (7, (8, 9))))))))
_TREE_BRC_FOUR = (
    (0, (1, 2)),
    ((3, 4), ((5, 6), (7, (8, (9, ((10, 11), ((12, 13), (14, 15)))))))),
)

_HUFFMAN_TREES = {
    0: _TREE_BRC_ZERO,
    1: _TREE_BRC_ONE,
    2: _TREE_BRC_TWO,
    3: _TREE_BRC_THREE,
    4: _TREE_BRC_FOUR,
}

T = TypeVar("T", bound="HuffmanNode")
HuffmanNode = Union[int, Tuple[T, T]]


class FDBAQDecoder:
    """Extracts sample codes from Sentinel-1 packets."""

    def __init__(self, data: bytes, num_quads: int) -> None:
        self._bit_counter = 0
        self._byte_counter = 0
        self._data = data
        self._num_quads = num_quads
        self._num_baq_blocks = math.ceil(num_quads / 128)

        self._brc: List[int] = []
        self._thidx: List[int] = []
        self._i_evens_scodes: List[SampleCode] = []
        self._i_odds_scodes: List[SampleCode] = []
        self._q_evens_scodes: List[SampleCode] = []
        self._q_odds_scodes: List[SampleCode] = []

        logging.debug(
            f"Created FDBAQ decoder. Numquads={num_quads} NumBAQblocks={self._num_baq_blocks}"
        )

        # Process all channels
        self._process_channel("IE", self._i_evens_scodes, read_brc=True)
        self._align_word_boundary()
        self._process_channel("IO", self._i_odds_scodes)
        self._align_word_boundary()
        self._process_channel("QE", self._q_evens_scodes, read_thidx=True)
        self._align_word_boundary()
        self._process_channel("QO", self._q_odds_scodes)

    def _process_channel(
        self,
        channel_name: str,
        output_list: List,
        read_brc: bool = False,
        read_thidx: bool = False,
    ) -> None:
        """Process a single channel's data."""
        values_processed_count = 0
        for block_index in range(self._num_baq_blocks):
            logging.debug(
                f"Starting {channel_name} block {block_index+1} of "
                f"{self._num_baq_blocks}, processing "
                f"{min(128, self._num_quads-values_processed_count)} vals"
            )

            if read_brc:
                brc = self._read_brc()
                self._brc.append(brc)

            if read_thidx:
                self._thidx.append(self._read_thidx())

            # Use dictionary lookup instead of if-else chain
            brc_index = self._brc[block_index]
            if brc_index not in _HUFFMAN_TREES:
                logging.error(f"Unrecognized BAQ mode code {brc_index}")
                raise ValueError(f"Invalid BAQ mode code: {brc_index}")

            this_huffman_tree = _HUFFMAN_TREES[brc_index]

            # Process values for this block
            remaining = min(128, self._num_quads - values_processed_count)
            for _ in range(remaining):
                output_list.append(self._decode_sample(this_huffman_tree))
                values_processed_count += 1

    def _decode_sample(self, huffman_tree: HuffmanNode) -> SampleCode:
        """Decode a single sample using the given Huffman tree."""
        sign = self._next_bit()
        current_node = huffman_tree
        while not isinstance(current_node, int):
            current_node = current_node[self._next_bit()]
            if current_node is None:
                raise ValueError("Invalid Huffman encoding")
        return SampleCode(sign, current_node)

    def _align_word_boundary(self) -> None:
        """Align reading position to next 16-bit word boundary."""
        logging.debug(
            f"Finished block: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )
        if self._bit_counter != 0:
            self._bit_counter = 0
            self._byte_counter += 1
        self._byte_counter = math.ceil(self._byte_counter / 2) * 2
        logging.debug(
            f"Moved counters: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )

    @property
    def brcs(self) -> List[int]:
        """Get the extracted list of Bit Rate Codes (BRCs)."""
        return self._brc

    @property
    def thidxs(self) -> List[int]:
        """Get the extracted list of Threshold Index codes (THIDXs)."""
        return self._thidx

    @property
    def s_ie(self) -> List[SampleCode]:
        """Get the even-indexed I channel data."""
        return self._i_evens_scodes

    @property
    def s_io(self) -> List[SampleCode]:
        """Get the odd-indexed I channel data."""
        return self._i_odds_scodes

    @property
    def s_qe(self) -> List[SampleCode]:
        """Get the even-indexed Q channel data."""
        return self._q_evens_scodes

    @property
    def s_qo(self) -> List[SampleCode]:
        """Get the odd-indexed Q channel data."""
        return self._q_odds_scodes

    def _next_bit(self) -> int:
        bit = (self._data[self._byte_counter] >> (7 - self._bit_counter)) & 0x01
        self._bit_counter = (self._bit_counter + 1) % 8
        if self._bit_counter == 0:
            self._byte_counter += 1
        return bit

    def _read_thidx(self) -> int:
        residual = 0
        for i in range(8):
            residual = residual << 1
            residual += self._next_bit()
        return residual

    def _read_brc(self) -> int:
        residual = 0
        for i in range(3):
            residual = residual << 1
            residual += self._next_bit()
        return residual
