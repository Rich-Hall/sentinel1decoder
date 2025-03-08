import logging
from typing import List

import numpy as np

from sentinel1decoder import _lookup_tables as lookup
from sentinel1decoder._sample_code import SampleCode


def reconstruct_channel_vals(
    data: List[SampleCode],
    block_brcs: List[int],
    block_thidxs: List[int],
    vals_to_process: int,
) -> np.ndarray:
    if not len(block_brcs) == len(block_thidxs):
        logging.error("Mismatched lengths of BRC block parameters")
    num_brc_blocks = len(block_brcs)

    out_vals = np.zeros(vals_to_process)
    n = 0
    # For each BRC block
    for block_index in range(num_brc_blocks):

        brc = int(block_brcs[block_index])
        thidx = int(block_thidxs[block_index])

        # For each code in the BRC block
        for i in range(min(128, vals_to_process - n)):

            s_code = data[n]

            if brc == 0:
                if thidx <= 3:
                    if s_code.mcode < 3:
                        out_vals[n] = (-1) ** s_code.sign * s_code.mcode
                    elif s_code.mcode == 3:
                        out_vals[n] = (-1) ** s_code.sign * lookup.b0[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (
                        (-1) ** s_code.sign
                        * lookup.nrl_b0[s_code.mcode]
                        * lookup.sf[thidx]
                    )
            elif brc == 1:
                if thidx <= 3:
                    if s_code.mcode < 4:
                        out_vals[n] = (-1) ** s_code.sign * s_code.mcode
                    elif s_code.mcode == 4:
                        out_vals[n] = (-1) ** s_code.sign * lookup.b1[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (
                        (-1) ** s_code.sign
                        * lookup.nrl_b1[s_code.mcode]
                        * lookup.sf[thidx]
                    )
            elif brc == 2:
                if thidx <= 5:
                    if s_code.mcode < 6:
                        out_vals[n] = (-1) ** s_code.sign * s_code.mcode
                    elif s_code.mcode == 6:
                        out_vals[n] = (-1) ** s_code.sign * lookup.b2[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (
                        (-1) ** s_code.sign
                        * lookup.nrl_b2[s_code.mcode]
                        * lookup.sf[thidx]
                    )
            elif brc == 3:
                if thidx <= 6:
                    if s_code.mcode < 9:
                        out_vals[n] = (-1) ** s_code.sign * s_code.mcode
                    elif s_code.mcode == 9:
                        out_vals[n] = (-1) ** s_code.sign * lookup.b3[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (
                        (-1) ** s_code.sign
                        * lookup.nrl_b3[s_code.mcode]
                        * lookup.sf[thidx]
                    )
            elif brc == 4:
                if thidx <= 8:
                    if s_code.mcode < 15:
                        out_vals[n] = (-1) ** s_code.sign * s_code.mcode
                    elif s_code.mcode == 15:
                        out_vals[n] = (-1) ** s_code.sign * lookup.b4[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (
                        (-1) ** s_code.sign
                        * lookup.nrl_b4[s_code.mcode]
                        * lookup.sf[thidx]
                    )
            else:
                logging.error("Unhandled reconstruction case")

            n += 1

    return out_vals
