import logging
import math

from sentinel1decoder._sample_code import SampleCode

_TREE_BRC_ZERO = (0, (1, (2, 3)))
_TREE_BRC_ONE = (0, (1, (2, (3, 4))))
_TREE_BRC_TWO = (0, (1, (2, (3, (4, (5, 6))))))
_TREE_BRC_THREE = ((0, 1), (2, (3, (4, (5, (6, (7, (8, 9))))))))
_TREE_BRC_FOUR = (
    (0, (1, 2)),
    ((3, 4), ((5, 6), (7, (8, (9, ((10, 11), ((12, 13), (14, 15)))))))),
)


class FDBAQDecoder:
    """Extracts sample codes from Sentinel-1 packets."""

    def __init__(self, data, num_quads):
        # TODO: Convert to proper Huffman implementation
        self._bit_counter = 0
        self._byte_counter = 0
        self._data = data
        self._num_quads = num_quads

        self._num_baq_blocks = math.ceil(num_quads / 128)
        self._brc = []
        self._thidx = []

        self._i_evens_scodes = []
        self._i_odds_scodes = []
        self._q_evens_scodes = []
        self._q_odds_scodes = []

        logging.debug(
            (
                f"Created FDBAQ decoder. "
                f"Numquads={num_quads} "
                f"NumBAQblocks={self._num_baq_blocks}"
            )
        )

        # TODO: Lots of repetition here, break into function(s)
        # Channel 1 - IE
        values_processed_count = 0
        for block_index in range(self._num_baq_blocks):
            logging.debug(
                (
                    f"Starting IE block {block_index+1} of "
                    f"{self._num_baq_blocks}, processing "
                    f"{min(128, self._num_quads-values_processed_count)} vals"
                )
            )

            # Each Bit Rate Code is in the first three bits of each IE block
            brc = self._read_brc()
            self._brc.append(brc)

            # The BRC determines which type of Huffman encoding we're using
            # Ref. SAR Space Protocol Data Unit p.71
            if self._brc[block_index] == 0:
                this_huffman_tree = _TREE_BRC_ZERO
            elif self._brc[block_index] == 1:
                this_huffman_tree = _TREE_BRC_ONE
            elif self._brc[block_index] == 2:
                this_huffman_tree = _TREE_BRC_TWO
            elif self._brc[block_index] == 3:
                this_huffman_tree = _TREE_BRC_THREE
            elif self._brc[block_index] == 4:
                this_huffman_tree = _TREE_BRC_FOUR
            else:
                logging.error(f"Unrecognized BAQ mode code {self._brc[block_index]}")

            # Each baq block contains 128 hcodes, except the last
            for i in range(min(128, self._num_quads - values_processed_count)):
                sign = self._next_bit()

                # Recursively step through our Huffman tree.
                # We know we've reached the end when our current node is an
                # integer rather than a tuple.
                current_node = this_huffman_tree
                while not isinstance(current_node, int):
                    current_node = current_node[self._next_bit()]
                    if current_node is None:
                        raise ValueError
                self._i_evens_scodes.append(SampleCode(sign, current_node))
                values_processed_count = values_processed_count + 1

        # Channel 2 - IO
        # Move counters to next 16-bit word boundary
        logging.debug(
            (
                f"Finished block: "
                f"bit_counter={self._bit_counter} "
                f"byte_counter={self._byte_counter}"
            )
        )
        if not self._bit_counter == 0:
            self._bit_counter = 0
            self._byte_counter += 1
        self._byte_counter = math.ceil(self._byte_counter / 2) * 2
        logging.debug(
            f"Moved counters: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )

        values_processed_count = 0
        for block_index in range(self._num_baq_blocks):
            logging.debug(
                (
                    f"Starting IO block {block_index+1} of "
                    f"{self._num_baq_blocks}, processing "
                    f"{min(128, self._num_quads-values_processed_count)} vals"
                )
            )

            # The BRC determines which type of Huffman encoding we're using
            # Ref. SAR Space Protocol Data Unit p.71
            if self._brc[block_index] == 0:
                this_huffman_tree = _TREE_BRC_ZERO
            elif self._brc[block_index] == 1:
                this_huffman_tree = _TREE_BRC_ONE
            elif self._brc[block_index] == 2:
                this_huffman_tree = _TREE_BRC_TWO
            elif self._brc[block_index] == 3:
                this_huffman_tree = _TREE_BRC_THREE
            elif self._brc[block_index] == 4:
                this_huffman_tree = _TREE_BRC_FOUR
            else:
                logging.error(f"Unrecognized BAQ mode code {self._brc[block_index]}")

            # Each baq block contains 128 hcodes, except the last
            for i in range(min(128, self._num_quads - values_processed_count)):
                sign = self._next_bit()

                # Recursively step through our Huffman tree.
                # We know we've reached the end when our current node is an
                # integer rather than a tuple.
                current_node = this_huffman_tree
                while not isinstance(current_node, int):
                    current_node = current_node[self._next_bit()]
                    if current_node is None:
                        raise ValueError
                self._i_odds_scodes.append(SampleCode(sign, current_node))
                values_processed_count = values_processed_count + 1

        # Channel 3 -QE
        # Move counters to next 16-bit word boundary
        logging.debug(
            f"Finished block: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )
        if not self._bit_counter == 0:
            self._bit_counter = 0
            self._byte_counter += 1
        self._byte_counter = math.ceil(self._byte_counter / 2) * 2
        logging.debug(
            f"Moved counters: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )

        values_processed_count = 0
        for block_index in range(self._num_baq_blocks):
            logging.debug(
                (
                    f"Starting QE block {block_index+1} of "
                    f"{self._num_baq_blocks}, processing "
                    f"{min(128, self._num_quads-values_processed_count)} vals"
                )
            )

            # Each THIDX Code is in the first eight bits of each IE block
            this_thidx = self._read_thidx()
            self._thidx.append(this_thidx)

            # The BRC determines which type of Huffman encoding we're using
            # Ref. SAR Space Protocol Data Unit p.71
            if self._brc[block_index] == 0:
                this_huffman_tree = _TREE_BRC_ZERO
            elif self._brc[block_index] == 1:
                this_huffman_tree = _TREE_BRC_ONE
            elif self._brc[block_index] == 2:
                this_huffman_tree = _TREE_BRC_TWO
            elif self._brc[block_index] == 3:
                this_huffman_tree = _TREE_BRC_THREE
            elif self._brc[block_index] == 4:
                this_huffman_tree = _TREE_BRC_FOUR
            else:
                logging.error(f"Unrecognized BAQ mode code {self._brc[block_index]}")

            # Each baq block contains 128 hcodes, except the last
            for i in range(min(128, self._num_quads - values_processed_count)):
                sign = self._next_bit()

                # Recursively step through our Huffman tree.
                # We know we've reached the end when our current node is an
                # integer rather than a tuple.
                current_node = this_huffman_tree
                while not isinstance(current_node, int):
                    current_node = current_node[self._next_bit()]
                    if current_node is None:
                        raise ValueError
                self._q_evens_scodes.append(SampleCode(sign, current_node))
                values_processed_count = values_processed_count + 1

        # Channel 4 - QO
        # Move counters to next 16-bit word boundary
        logging.debug(
            f"Finished block: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )
        if not self._bit_counter == 0:
            self._bit_counter = 0
            self._byte_counter += 1
        self._byte_counter = math.ceil(self._byte_counter / 2) * 2
        logging.debug(
            f"Moved counters: bit_counter={self._bit_counter} byte_counter={self._byte_counter}"
        )

        values_processed_count = 0
        for block_index in range(self._num_baq_blocks):
            logging.debug(
                (
                    f"Starting QO block {block_index+1} of "
                    f"{self._num_baq_blocks}, processing "
                    f"{min(128, self._num_quads-values_processed_count)} vals"
                )
            )

            # The BRC determines which type of Huffman encoding we're using
            # Ref. SAR Space Protocol Data Unit p.71
            if self._brc[block_index] == 0:
                this_huffman_tree = _TREE_BRC_ZERO
            elif self._brc[block_index] == 1:
                this_huffman_tree = _TREE_BRC_ONE
            elif self._brc[block_index] == 2:
                this_huffman_tree = _TREE_BRC_TWO
            elif self._brc[block_index] == 3:
                this_huffman_tree = _TREE_BRC_THREE
            elif self._brc[block_index] == 4:
                this_huffman_tree = _TREE_BRC_FOUR
            else:
                logging.error(f"Unrecognized BAQ mode code {self._brc[block_index]}")

            # Each baq block contains 128 hcodes, except the last
            for i in range(min(128, self._num_quads - values_processed_count)):
                sign = self._next_bit()

                # Recursively step through our Huffman tree.
                # We know we've reached the end when our current node is an
                # integer rather than a tuple.
                current_node = this_huffman_tree
                while not isinstance(current_node, int):
                    current_node = current_node[self._next_bit()]
                    if current_node is None:
                        raise ValueError
                self._q_odds_scodes.append(SampleCode(sign, current_node))
                values_processed_count = values_processed_count + 1

    @property
    def get_brcs(self):
        """Get the extracted list of Bit Rate Codes (BRCs)."""
        return self._brc

    @property
    def get_thidxs(self):
        """Get the extracted list of Threshold Index codes (THIDXs)."""
        return self._thidx

    @property
    def get_s_ie(self):
        """Get the even-indexed I channel data."""
        return self._i_evens_scodes

    @property
    def get_s_io(self):
        """Get the odd-indexed I channel data."""
        return self._i_odds_scodes

    @property
    def get_s_qe(self):
        """Get the even-indexed Q channel data."""
        return self._q_evens_scodes

    @property
    def get_s_qo(self):
        """Get the odd-indexed Q channel data."""
        return self._q_odds_scodes

    def _next_bit(self):
        bit = (self._data[self._byte_counter] >> (7 - self._bit_counter)) & 0x01
        self._bit_counter = (self._bit_counter + 1) % 8
        if self._bit_counter == 0:
            self._byte_counter += 1
        return bit

    def _read_thidx(self):
        residual = 0
        for i in range(8):
            residual = residual << 1
            residual += self._next_bit()
        return residual

    def _read_brc(self):
        residual = 0
        for i in range(3):
            residual = residual << 1
            residual += self._next_bit()
        return residual
