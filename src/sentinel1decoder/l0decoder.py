import logging
from typing import Optional

import numpy as np
import pandas as pd

from sentinel1decoder import _field_names as fn
from sentinel1decoder._metadata_parser import parse_raw_metadata_columns
from sentinel1decoder._sentinel1decoder import (
    decode_batched_bypass_packets,
    decode_batched_fdbaq_packets,
    decode_packet_headers,
)
from sentinel1decoder.enums import BaqMode


class Level0Decoder:
    """Decoder for Sentinel-1 Level 0 files."""

    def __init__(self, filename: str, log_level: int = logging.WARNING):
        # TODO: Better logging functionality
        logging.basicConfig(filename="output_log.log", level=log_level)
        logging.debug("Initialized logger")

        self.filename = filename
        self._user_data_bounds: Optional[list[tuple[int, int]]] = None

    def decode_metadata(self, return_raw: bool = False) -> pd.DataFrame:
        with open(self.filename, "rb") as f:
            data = f.read()
            columns, bounds = decode_packet_headers(data)

        self._user_data_bounds = bounds

        if return_raw:
            out_df = pd.DataFrame(columns)
            out_df = self._add_acquisition_chunk_index(out_df, use_raw_names=True)
            return out_df

        out_df = parse_raw_metadata_columns(columns)
        out_df = self._add_acquisition_chunk_index(out_df, use_raw_names=False)
        return out_df

    def decode_packets(self, input_header: pd.DataFrame, batch_size: int = 256) -> np.ndarray:

        packet_nums, num_quads, baq_mode = self._check_packets_are_valid_for_decoding(input_header)

        if baq_mode == BaqMode.BYPASS_MODE:
            batch_decoder = decode_batched_bypass_packets
        elif baq_mode in (BaqMode.BAQ_3_BIT_MODE, BaqMode.BAQ_4_BIT_MODE, BaqMode.BAQ_5_BIT_MODE):
            raise NotImplementedError("Data format C not implemented")
        elif baq_mode in (BaqMode.FDBAQ_MODE_0, BaqMode.FDBAQ_MODE_1, BaqMode.FDBAQ_MODE_2):
            batch_decoder = decode_batched_fdbaq_packets
        else:
            raise ValueError(f"Invalid BAQ mode: {baq_mode}")

        output_data = np.zeros((len(packet_nums), num_quads * 2), dtype=np.complex64)
        batch = []
        output_idx = 0

        with open(self.filename, "rb") as f:
            bounds = self._user_data_bounds
            if bounds is None:
                _, bounds = decode_packet_headers(f.read())
                self._user_data_bounds = bounds

            for packet_num in sorted(packet_nums):
                f.seek(bounds[packet_num][0])
                data_bytes = f.read(bounds[packet_num][1])
                batch.append(data_bytes)

                if len(batch) == batch_size:
                    decoded = batch_decoder(batch, num_quads)
                    output_data[output_idx : output_idx + len(decoded), :] = decoded
                    output_idx += len(decoded)
                    batch.clear()

            # Flush remainder
            if batch:
                decoded = batch_decoder(batch, num_quads)
                output_data[output_idx : output_idx + len(decoded), :] = decoded

        return output_data

    def _check_packets_are_valid_for_decoding(self, packets: pd.DataFrame) -> tuple[list[int], int, BaqMode]:
        """Check if the packets are valid for decoding.

        Args:
            packets: DataFrame of packets to check.

        Returns:
            Tuple of the packet numbers, the number of quads and the BAQ mode
        """

        # Check we have more than 0 packets
        if len(packets) == 0:
            raise ValueError("No packets to check")

        # Check we have been given packet numbers
        packet_num_name = fn.f("PACKET_NUM")
        if packet_num_name in (packets.index.names or []):
            packet_nums = np.asarray(packets.index.get_level_values(packet_num_name).unique())
        elif packet_num_name in packets.columns:
            packet_nums = np.asarray(packets[packet_num_name].unique())
        else:
            raise ValueError("No PACKET_NUM column or index level found")

        # Check we have a single number of quads
        if fn.f("NUM_QUADS") in packets.columns:
            nq_col_name = fn.f("NUM_QUADS")
        elif fn.f("NUM_QUADS", "raw") in packets.columns:
            nq_col_name = fn.f("NUM_QUADS", "raw")
        else:
            raise ValueError("No NUM_QUADS column found")
        unique_num_quads = packets[nq_col_name].unique()
        if len(unique_num_quads) != 1:
            raise ValueError("Multiple num_quads values found")

        # Check we have a single BAQ mode
        if fn.f("BAQ_MODE") in packets.columns:
            baq_mode_col_name = fn.f("BAQ_MODE")
        elif fn.f("BAQ_MODE", "raw") in packets.columns:
            baq_mode_col_name = fn.f("BAQ_MODE", "raw")
        else:
            raise ValueError("No BAQ mode column found")
        unique_baq_modes = packets[baq_mode_col_name].unique()
        if len(unique_baq_modes) != 1:
            raise ValueError("Multiple BAQ modes found")

        # Convert the unique values to the correct types if needed
        packet_nums_int_list = [int(x) for x in packet_nums]
        num_quads = int(unique_num_quads[0])
        baq_mode = unique_baq_modes[0]
        if isinstance(baq_mode, int):
            baq_mode = BaqMode(baq_mode)
        if not isinstance(baq_mode, BaqMode):
            raise ValueError(f"Invalid BAQ mode: {baq_mode}")

        return (packet_nums_int_list, num_quads, baq_mode)

    def _add_acquisition_chunk_index(self, df: pd.DataFrame, *, use_raw_names: bool = False) -> pd.DataFrame:
        if use_raw_names:
            sig, swath, nq, baq = (
                fn.f("SIGNAL_TYPE", "raw"),
                fn.f("SWATH_NUM", "raw"),
                fn.f("NUM_QUADS", "raw"),
                fn.f("BAQ_MODE", "raw"),
            )
            swst, swl, pri = fn.f("SWST", "raw"), fn.f("SWL", "raw"), fn.f("PRI", "raw")
            prict, abadr, ebadr = fn.f("PRI_COUNT", "raw"), fn.f("ABADR", "raw"), fn.f("EBADR", "raw")
        else:
            sig, swath, nq, baq = fn.f("SIGNAL_TYPE"), fn.f("SWATH_NUM"), fn.f("NUM_QUADS"), fn.f("BAQ_MODE")
            swst, swl, pri = fn.f("SWST"), fn.f("SWL"), fn.f("PRI")
            prict, abadr, ebadr = fn.f("PRI_COUNT"), fn.f("ABADR"), fn.f("EBADR")

        prev = df.shift(1)

        # Check various parameters remain constant
        break_const = (
            (df[sig] != prev[sig])
            | (df[swath] != prev[swath])
            | (df[nq] != prev[nq])
            | (df[baq] != prev[baq])
            | (df[swst] != prev[swst])
            | (df[swl] != prev[swl])
            | (df[pri] != prev[pri])
        )

        # Check PRI count increments by 1 packet-by-packet (wrapping around at 2^32-1)
        break_prict = (
            ~((df[prict] == prev[prict] + 1) | ((prev[prict] == 2**32 - 1) & (df[prict] == 0)))
            & df[prict].notna()
            & prev[prict].notna()
        )

        # Check Azimuth beam address increases monotonically
        break_abadr = (df[abadr] < prev[abadr]) & df[abadr].notna() & prev[abadr].notna()

        # Check Elevation beam address remains constant
        break_ebadr = (df[ebadr] != prev[ebadr]) & df[ebadr].notna() & prev[ebadr].notna()

        break_mask = break_const | break_prict | break_abadr | break_ebadr
        break_mask = break_mask.fillna(True)  # treat NA as break (start new chunk)
        chunk_id = break_mask.astype(np.intp).cumsum() - 1

        packet_num = np.arange(len(df))
        result = df.copy()
        result.index = pd.MultiIndex.from_arrays(
            [chunk_id.to_numpy(), packet_num],
            names=[fn.f("ACQUISITION_CHUNK_NUM"), fn.f("PACKET_NUM")],
        )
        return result
