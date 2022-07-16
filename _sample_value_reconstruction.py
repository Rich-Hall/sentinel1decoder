# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 10:16:29 2022.

@author: richa
"""
import logging

import numpy as np

import sentinel1decoder._lookup_tables as lookup


def reconstruct_channel_vals(data, block_brcs, block_thidxs, vals_to_process):
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
                    if s_code.get_mcode < 3:
                        out_vals[n] = (-1)**s_code.get_sign * s_code.get_mcode
                    elif s_code.get_mcode == 3:
                        out_vals[n] = (-1)**s_code.get_sign * lookup.b0[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (-1)**s_code.get_sign * lookup.nrl_b0[s_code.get_mcode] * lookup.sf[thidx]
            elif brc == 1:
                if thidx <= 3:
                    if s_code.get_mcode < 4:
                        out_vals[n] = (-1)**s_code.get_sign * s_code.get_mcode
                    elif s_code.get_mcode == 4:
                        out_vals[n] = (-1)**s_code.get_sign * lookup.b1[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (-1)**s_code.get_sign * lookup.nrl_b1[s_code.get_mcode] * lookup.sf[thidx]
            elif brc == 2:
                if thidx <= 5:
                    if s_code.get_mcode < 6:
                        out_vals[n] = (-1)**s_code.get_sign * s_code.get_mcode
                    elif s_code.get_mcode == 6:
                        out_vals[n] = (-1)**s_code.get_sign * lookup.b2[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (-1)**s_code.get_sign * lookup.nrl_b2[s_code.get_mcode] * lookup.sf[thidx]
            elif brc == 3:
                if thidx <= 6:
                    if s_code.get_mcode < 9:
                        out_vals[n] = (-1)**s_code.get_sign * s_code.get_mcode
                    elif s_code.get_mcode == 9:
                        out_vals[n] = (-1)**s_code.get_sign * lookup.b3[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (-1)**s_code.get_sign * lookup.nrl_b3[s_code.get_mcode] * lookup.sf[thidx]
            elif brc == 4:
                if thidx <= 8:
                    if s_code.get_mcode < 15:
                        out_vals[n] = (-1)**s_code.get_sign * s_code.get_mcode
                    elif s_code.get_mcode == 15:
                        out_vals[n] = (-1)**s_code.get_sign * lookup.b4[thidx]
                    else:
                        logging.error("Unhandled reconstruction case")
                else:
                    out_vals[n] = (-1)**s_code.get_sign * lookup.nrl_b4[s_code.get_mcode] * lookup.sf[thidx]
            else:
                logging.error("Unhandled reconstruction case")

            n += 1

    return out_vals
