import logging
from typing import BinaryIO, Tuple

import numpy as np
import pandas as pd

from sentinel1decoder import _headers as hdrs
from sentinel1decoder import constants as cnst
from sentinel1decoder._sentinel1decoder import (
    decode_batched_bypass_packets,
    decode_batched_fdbaq_packets,
)


class Level0Decoder:
    """Decoder for Sentinel-1 Level 0 files."""

    def __init__(self, filename: str, log_level: int = logging.WARNING):
        # TODO: Better logging functionality
        logging.basicConfig(filename="output_log.log", level=log_level)
        logging.debug("Initialized logger")

        self.filename = filename

    def decode_metadata(self) -> pd.DataFrame:
        """Decode the full header of each packet in a Sentinel-1 Level 0 file.

        Sentinel-1 Space Packet format consists of a primary header of 6 bytes
        followed by a packet data field. The first 62 bytes of the packet data
        field are taken up by the packet secondary header.

        Returns:
            A Pandas Dataframe containing the decoded metadata.
        """
        output_row_list = []

        with open(self.filename, "rb") as f:
            # An input file typically consists of many packets.
            # We don't know how many ahead of time.
            while True:
                try:
                    output_dictionary_row, _ = self._read_single_packet(f)
                except NoMorePacketsException:
                    break
                output_row_list.append(output_dictionary_row)

        output_dataframe = pd.DataFrame(output_row_list)
        return output_dataframe

    def decode_packets(self, input_header: pd.DataFrame, batch_size: int = 256) -> np.ndarray:
        """
        Decode the data payload from the specified packets.

        The input header should be a dataframe of header data, filtered to only include
        the packets to decode. The selected packets should have the same swath number,
        number of quads, and BAQ mode.

        The decoder will multithread the decoding of packets in batches of the specified size.
        Multithreading the calling of this function is therefore not recommended.

        Args:
            input_header: A Pandas dataframe of the header information for the packets to decode.
            batch_size: The number of packets to batch together for parallelized decoding.

        Returns:
            A NumPy array of the decoded data, with dimensions (num_packets, num_quads * 2).
        """
        swath_numbers = input_header[cnst.SWATH_NUM_FIELD_NAME].unique()
        num_quads_values = input_header[cnst.NUM_QUADS_FIELD_NAME].unique()
        baq_modes = input_header[cnst.BAQ_MODE_FIELD_NAME].unique()

        if len(swath_numbers) != 1:
            raise ValueError("Multiple swath numbers found")
        if len(num_quads_values) != 1:
            raise ValueError("Multiple num_quads values found")
        if len(baq_modes) != 1:
            raise ValueError("Multiple BAQ modes found")

        num_quads = num_quads_values[0]
        baq_mode = baq_modes[0]

        if baq_mode in (12, 13, 14):
            batch_decoder = decode_batched_fdbaq_packets
        elif baq_mode == 0:
            batch_decoder = decode_batched_bypass_packets
        elif baq_mode in (3, 4, 5):
            raise NotImplementedError("Data format C not implemented")
        else:
            raise ValueError(f"Invalid BAQ mode: {baq_mode}")

        desired_packet_counts = set(input_header[cnst.SPACE_PACKET_COUNT_FIELD_NAME].values)

        output_data = np.zeros((len(desired_packet_counts), num_quads * 2), dtype=np.complex64)

        batch = []
        output_idx = 0

        with open(self.filename, "rb") as f:
            while output_idx < len(desired_packet_counts):
                try:
                    header, payload = self._read_single_packet(f)
                except NoMorePacketsException:
                    break

                if header[cnst.SPACE_PACKET_COUNT_FIELD_NAME] in desired_packet_counts:
                    batch.append(payload)

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

    def _read_single_packet(self, opened_file: BinaryIO) -> Tuple[dict, bytes]:
        """
        Read a single packet of data from the file.

        Args:
            opened_file:    Sentinel-1 RAW file opened in 'rb' mode with read
                            position at the start of a packet

        Returns:
            A dict of the header data fields for this packet
            The raw bytes of the user data payload for this packet
        """
        # PACKET PRIMARY HEADER (6 bytes)
        # First check if we have reached the end of the file
        data_buffer = opened_file.read(6)
        if not data_buffer:
            raise NoMorePacketsException()

        output_dictionary_row = hdrs.decode_primary_header(data_buffer)

        # PACKET DATA FIELD (between 62 and 65534 bytes)
        # First 62 bytes contain the PACKET SECONDARY HEADER
        pkt_data_len = output_dictionary_row[cnst.PACKET_DATA_LEN_FIELD_NAME]
        packet_data_buffer = opened_file.read(pkt_data_len)
        if not packet_data_buffer:
            raise Exception("Unexpectedly hit EOF while trying to read packet data field.")

        secondary_hdr = hdrs.decode_secondary_header(packet_data_buffer[:62])
        output_dictionary_row.update(secondary_hdr)

        # END OF SECONDARY HEADER.
        # User data follows for bytes 62 ---> packet_data_length
        output_bytes = packet_data_buffer[62:]

        return output_dictionary_row, output_bytes


class NoMorePacketsException(Exception):
    """Exception raised when we run out of packets to read in a file"""
