# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 17:36:54 2022.

@author: richa
"""
import struct
import numpy as np
import pandas as pd
from sentinel1decoder import constants as cnst

def range_dec_to_sample_rate(rgdec_code):
    if rgdec_code == 0:
        return 3 * cnst.f_ref
    elif rgdec_code == 1:
        return (8/3) * cnst.f_ref
    elif rgdec_code == 3:
        return (20/9) * cnst.f_ref
    elif rgdec_code == 4:
        return (16/9) * cnst.f_ref
    elif rgdec_code == 5:
        return (3/2) * cnst.f_ref
    elif rgdec_code == 6:
        return (4/3) * cnst.f_ref
    elif rgdec_code == 7:
        return (2/3) * cnst.f_ref
    elif rgdec_code == 8:
        return (12/7) * cnst.f_ref
    elif rgdec_code == 9:
        return (5/4) * cnst.f_ref
    elif rgdec_code == 10:
        return (6/13) * cnst.f_ref
    elif rgdec_code == 11:
        return (16/11) * cnst.f_ref
    else:
        # TODO: Throw error
        return 0


def read_subcommed_data(df):
    index_col = "Sub-commutated Ancilliary Data Word Index"
    data_col = "Sub-commutated Ancilliary Data Word"
    start_indices = df.index[df[index_col] == 1]
    output_dict_list = []

    dbl_type = np.dtype(np.float64).newbyteorder('>')
    sgl_type = np.dtype(np.float32).newbyteorder('>')
    for i in start_indices:

        # check our index is followed by a continuous block of 64
        if len(df) - i >= 64:
            if all(df.loc[i:i+63][index_col] == list(range(1, 65))):
                d = df.loc[i:i+63][data_col].tolist()
                x_bytes = struct.pack('>HHHH', d[0], d[1], d[2], d[3])
                y_bytes = struct.pack('>HHHH', d[4], d[5], d[6], d[7])
                z_bytes = struct.pack('>HHHH', d[8], d[9], d[10], d[11])
                x = np.frombuffer(x_bytes, dtype=dbl_type)[0]
                y = np.frombuffer(y_bytes, dtype=dbl_type)[0]
                z = np.frombuffer(z_bytes, dtype=dbl_type)[0]

                x_vel_bytes = struct.pack('>HH', d[12], d[13])
                y_vel_bytes = struct.pack('>HH', d[14], d[15])
                z_vel_bytes = struct.pack('>HH', d[16], d[17])
                x_vel = np.frombuffer(x_vel_bytes, dtype=sgl_type)[0]
                y_vel = np.frombuffer(y_vel_bytes, dtype=sgl_type)[0]
                z_vel = np.frombuffer(z_vel_bytes, dtype=sgl_type)[0]

                pvt_t1 = d[18] * 2**24
                pvt_t2 = (d[19] * 2**8)
                pvt_t3 = (d[20] * 2**-8)
                pvt_t4 = (d[21] * 2**-24)
                pvt_t = pvt_t1 + pvt_t2 + pvt_t3 + pvt_t4

                output_dictionary = {
                    "X-axis position ECEF": x,
                    "Y-axis position ECEF": y,
                    "Z-axis position ECEF": z,
                    "X-axis velocity ECEF": x_vel,
                    "Y-axis velocity ECEF": y_vel,
                    "Z-axis velocity ECEF": z_vel,
                    "POD Solution Data Timestamp": pvt_t
                }

                q0_bytes = struct.pack('>HH', d[22], d[23])
                q1_bytes = struct.pack('>HH', d[24], d[25])
                q2_bytes = struct.pack('>HH', d[26], d[27])
                q3_bytes = struct.pack('>HH', d[28], d[29])
                q0 = np.frombuffer(q0_bytes, dtype=sgl_type)[0]
                q1 = np.frombuffer(q1_bytes, dtype=sgl_type)[0]
                q2 = np.frombuffer(q2_bytes, dtype=sgl_type)[0]
                q3 = np.frombuffer(q3_bytes, dtype=sgl_type)[0]

                x_ang_rate_bytes = struct.pack('>HH', d[30], d[31])
                y_ang_rate_bytes = struct.pack('>HH', d[32], d[33])
                z_ang_rate_bytes = struct.pack('>HH', d[34], d[35])
                x_ang_rate = np.frombuffer(x_ang_rate_bytes, dtype=sgl_type)[0]
                y_ang_rate = np.frombuffer(y_ang_rate_bytes, dtype=sgl_type)[0]
                z_ang_rate = np.frombuffer(z_ang_rate_bytes, dtype=sgl_type)[0]

                att_t1 = d[36] * 2**24
                att_t2 = (d[37] * 2**8)
                att_t3 = (d[38] * 2**-8)
                att_t4 = (d[39] * 2**-24)
                att_t = att_t1 + att_t2 + att_t3 + att_t4

                output_dictionary.update({
                    "Q0 Attitude Quaternion": q0,
                    "Q1 Attitude Quaternion": q1,
                    "Q2 Attitude Quaternion": q2,
                    "Q3 Attitude Quaternion": q3,
                    "Omega-X Angular Rate": x_ang_rate,
                    "Omega-Y Angular Rate": y_ang_rate,
                    "Omega-Z Angular Rate": z_ang_rate,
                    "Attitude Data Timestamp": att_t
                })

                output_dict_list.append(output_dictionary)
    out_df = pd.DataFrame(output_dict_list)
    return out_df
