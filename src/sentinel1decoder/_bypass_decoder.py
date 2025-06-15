import math

import numpy as np


def _ten_bit_unsigned_to_signed_int(ten_bit: int) -> int:
    """
    Convert a ten-bit unsigned int to a standard signed int.

    Args:
        ten_bit: Raw ten-bit int extracted from packet.

    Returns:
        A standard signed integer
    """
    # First bit is the sign, remaining 9 encode the number
    sign = int((-1) ** ((ten_bit >> 9) & 0x1))
    return sign * (ten_bit & 0x1FF)


class BypassDecoder:
    """Decode user data format type A and B (“Bypass” or “Decimation Only”)."""

    def __init__(self, data: bytes, num_quads: int) -> None:
        self._data = data
        self._num_quads = num_quads

        _num_words = math.ceil((10 / 16) * num_quads)  # No. of 16-bit words per channel
        self._num_bytes = 2 * _num_words  # No. of 8-bit bytes per channel

        self._i_evens = self._process_channel(0)
        self._i_odds = self._process_channel(self._num_bytes)
        self._q_evens = self._process_channel(2 * self._num_bytes)
        self._q_odds = self._process_channel(3 * self._num_bytes)

    @property
    def i_evens(self) -> np.ndarray:
        return self._i_evens

    @property
    def i_odds(self) -> np.ndarray:
        return self._i_odds

    @property
    def q_evens(self) -> np.ndarray:
        return self._q_evens

    @property
    def q_odds(self) -> np.ndarray:
        return self._q_odds

    def _process_channel(self, start_8bit_index: int) -> np.ndarray:
        """Process a single channel's data.

        Python doesn't have an easy way of extracting 10-bit integers.
        We're going to read in sets of five normal 8-bit bytes, and extract four
        10-bit words per set. We'll need to track the indexing separately and
        check for the end of the file each time.

        Args:
            channel_name: The name of the channel to process.
            output_array: The array to store the processed data.
            start_8bit_index: The starting index of the 8-bit bytes to process.
        """
        index_8bit = start_8bit_index
        index_10bit = 0
        output_array = np.zeros(self._num_quads, dtype=int)

        while index_10bit < self._num_quads:
            if index_10bit < self._num_quads:
                s_code = (self._data[index_8bit] << 2 | self._data[index_8bit + 1] >> 6) & 1023
                output_array[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
                index_10bit += 1
            else:
                break

            if index_10bit < self._num_quads:
                s_code = (self._data[index_8bit + 1] << 4 | self._data[index_8bit + 2] >> 4) & 1023
                output_array[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
                index_10bit += 1
            else:
                break

            if index_10bit < self._num_quads:
                s_code = (self._data[index_8bit + 2] << 6 | self._data[index_8bit + 3] >> 2) & 1023
                output_array[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
                index_10bit += 1
            else:
                break

            if index_10bit < self._num_quads:
                s_code = (self._data[index_8bit + 3] << 8 | self._data[index_8bit + 4] >> 0) & 1023
                output_array[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
                index_10bit += 1
            else:
                break

            index_8bit += 5

        return output_array
