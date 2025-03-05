# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 10:51:14 2022.

@author: richa
"""
import math
import numpy as np

from typing import Tuple

def _ten_bit_unsigned_to_signed_int(ten_bit: int) -> int:
    """
    Convert a ten-bit unsigned int to a standard signed int.
    
    Args:
        ten_bit: Raw ten-bit int extracted from packet.
    
    Returns:
        A standard signed integer
    """
    # First bit is the sign, remaining 9 encoide the number
    sign = (-1) ** ((ten_bit >> 9) & 0x1)
    return sign * (ten_bit & 0x1ff)

def decode_bypass_data(data: bytes, num_quads: int) -> Tuple[float, float, float, float]:
    """Decode user data format type A and B (“Bypass” or “Decimation Only”).

    Data is simply encoded in a series of 10-bit words.

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.
    num_quads : int
        Number of quads in the file.

    Returns
    -------
    i_evens : TYPE
        DESCRIPTION.
    i_odds : TYPE
        DESCRIPTION.
    q_evens : TYPE
        DESCRIPTION.
    q_odds : TYPE
        DESCRIPTION.

    """
    num_words = math.ceil((10/16)*num_quads)  # No. of 16-bit words per channel
    num_bytes = 2*num_words  # No. of 8-bit bytes per channel

    i_evens = np.zeros(num_quads)
    i_odds = np.zeros(num_quads)
    q_evens = np.zeros(num_quads)
    q_odds = np.zeros(num_quads)

    # Python doesn't have an easy way of extracting 10-bit integers.
    # Five 8-bit bytes = 40 bits = four 10-bit words

    # We're going to read in sets of five normal 8-bit bytes, and extract four
    # 10-bit words per set. We'll need to track the indexing separately and
    # check for the end of the file each time.
    # TODO: There is some repetition here which could be moved into function(s)

    # Channel 1 - IE
    index_8bit = 0
    index_10bit = 0
    while index_10bit < num_quads:
        if index_10bit < num_quads:
            s_code = (data[index_8bit] << 2 | data[index_8bit+1] >> 6) & 1023
            i_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+1] << 4 | data[index_8bit+2] >> 4) & 1023
            i_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+2] << 6 | data[index_8bit+3] >> 2) & 1023
            i_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+3] << 8 | data[index_8bit+4] >> 0) & 1023
            i_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        index_8bit += 5

    # Channel 2 - IO
    index_8bit = num_bytes
    index_10bit = 0
    while index_10bit < num_quads:
        if index_10bit < num_quads:
            s_code = (data[index_8bit] << 2 | data[index_8bit+1] >> 6) & 1023
            i_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+1] << 4 | data[index_8bit+2] >> 4) & 1023
            i_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+2] << 6 | data[index_8bit+3] >> 2) & 1023
            i_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+3] << 8 | data[index_8bit+4] >> 0) & 1023
            i_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        index_8bit += 5

    # Channel 3 - QE
    index_8bit = 2 * num_bytes
    index_10bit = 0
    while index_10bit < num_quads:
        if index_10bit < num_quads:
            s_code = (data[index_8bit] << 2 | data[index_8bit+1] >> 6) & 1023
            q_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+1] << 4 | data[index_8bit+2] >> 4) & 1023
            q_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+2] << 6 | data[index_8bit+3] >> 2) & 1023
            q_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+3] << 8 | data[index_8bit+4] >> 0) & 1023
            q_evens[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        index_8bit += 5

    # Channel 4 - QO
    index_8bit = 3 * num_bytes
    index_10bit = 0
    while index_10bit < num_quads:
        if index_10bit < num_quads:
            s_code = (data[index_8bit] << 2 | data[index_8bit+1] >> 6) & 1023
            q_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+1] << 4 | data[index_8bit+2] >> 4) & 1023
            q_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+2] << 6 | data[index_8bit+3] >> 2) & 1023
            q_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        if index_10bit < num_quads:
            s_code = (data[index_8bit+3] << 8 | data[index_8bit+4] >> 0) & 1023
            q_odds[index_10bit] = _ten_bit_unsigned_to_signed_int(s_code)
            index_10bit += 1
        else:
            break
        index_8bit += 5

    return i_evens, i_odds, q_evens, q_odds
