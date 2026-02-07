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

logger = logging.getLogger(__name__)


class Level0Decoder:
    """Decoder for Sentinel-1 Level 0 files."""

    def __init__(self, filename: str) -> None:
        """Initialize the Level0Decoder.

        Args:
            filename: The filename of the Sentinel-1 Level 0 file to decode.
        """
        self.filename = filename
        self._user_data_bounds: Optional[list[tuple[int, int]]] = None
        logger.debug("Initialized decoder for %s", filename)

    def decode_metadata(self, return_raw: bool = False) -> pd.DataFrame:
        """Decode the metadata of each packet in a Sentinel-1 Level 0 file.

        Sentinel-1 Space Packet format consists of a primary header of 6 bytes
        followed by a packet data field. The first 62 bytes of the packet data
        field are taken up by the packet secondary header.

        Returns:
            A Pandas Dataframe containing the decoded metadata.
        """
        logger.debug("Decoding metadata from %s", self.filename)
        with open(self.filename, "rb") as f:
            data = f.read()
            columns, bounds = decode_packet_headers(data)

        self._user_data_bounds = bounds
        logger.debug("Decoded metadata for %d packets", len(bounds))

        if return_raw:
            out_df = pd.DataFrame(columns)
            out_df = self._add_acquisition_chunk_index(out_df, use_raw_names=True)
            return out_df

        out_df = parse_raw_metadata_columns(columns)
        out_df = self._add_acquisition_chunk_index(out_df, use_raw_names=False)
        return out_df

    def decode_packets(self, input_header: pd.DataFrame, batch_size: int = 256) -> np.ndarray:
        """Decode the radar echoes from a given set of packets.

        Args:
            input_header: DataFrame of packets to decode.
            batch_size: The number of packets to decode at once.

        Returns:
            An array of complex samples from the SAR instrument.
        """

        packet_nums, num_quads, baq_mode = self._check_packets_are_valid_for_decoding(input_header)

        logger.info(
            "Decoding %d packets with BAQ mode %s, batch_size=%d",
            len(packet_nums),
            baq_mode.name,
            batch_size,
        )

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

        logger.debug("Decoded %d packets to shape %s", len(packet_nums), output_data.shape)
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
        packet_num_name = fn.PACKET_NUM_DECODED
        if packet_num_name in (packets.index.names or []):
            packet_nums = np.asarray(packets.index.get_level_values(packet_num_name).unique())
        elif packet_num_name in packets.columns:
            packet_nums = np.asarray(packets[packet_num_name].unique())
        else:
            raise ValueError("No PACKET_NUM column or index level found")

        # Check we have a single number of quads
        if fn.NUM_QUADS_DECODED in packets.columns:
            nq_col_name = fn.NUM_QUADS_DECODED
        elif fn.NUM_QUADS_RAW in packets.columns:
            nq_col_name = fn.NUM_QUADS_RAW
        else:
            raise ValueError("No NUM_QUADS column found")
        unique_num_quads = packets[nq_col_name].unique()
        if len(unique_num_quads) != 1:
            raise ValueError("Multiple num_quads values found")

        # Check we have a single BAQ mode
        if fn.BAQ_MODE_DECODED in packets.columns:
            baq_mode_col_name = fn.BAQ_MODE_DECODED
        elif fn.BAQ_MODE_RAW in packets.columns:
            baq_mode_col_name = fn.BAQ_MODE_RAW
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
        """Add an acquisition chunk index to a dataframe of packets.

        Args:
            df: DataFrame of packets to add the acquisition chunk index to.
            use_raw_names: Whether to use the raw or decoded names for the columns.

        Returns:
            A DataFrame with the acquisition chunk index added.
        """

        if use_raw_names:
            sig, swath, nq, baq = (
                fn.SIGNAL_TYPE_RAW,
                fn.SWATH_NUM_RAW,
                fn.NUM_QUADS_RAW,
                fn.BAQ_MODE_RAW,
            )
            swst, swl, pri = fn.SWST_RAW, fn.SWL_RAW, fn.PRI_RAW
            prict, abadr, ebadr = fn.PRI_COUNT_RAW, fn.ABADR_RAW, fn.EBADR_RAW
        else:
            sig, swath, nq, baq = fn.SIGNAL_TYPE_DECODED, fn.SWATH_NUM_DECODED, fn.NUM_QUADS_DECODED, fn.BAQ_MODE_DECODED
            swst, swl, pri = fn.SWST_DECODED, fn.SWL_DECODED, fn.PRI_DECODED
            prict, abadr, ebadr = fn.PRI_COUNT_DECODED, fn.ABADR_DECODED, fn.EBADR_DECODED

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
            names=[fn.ACQUISITION_CHUNK_NUM_DECODED, fn.PACKET_NUM_DECODED],
        )
        return result
