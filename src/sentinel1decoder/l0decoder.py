import logging
from typing import BinaryIO, Tuple

import numpy as np
import pandas as pd

from sentinel1decoder import _headers as hdrs
from sentinel1decoder import constants as cnst
from sentinel1decoder._user_data_decoder import UserDataDecoder


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

    def decode_packets(self, input_header: pd.DataFrame) -> np.ndarray:
        """Decode the user data payload from the specified space packets.

        Packet data typically consists of a single radar echo. SAR images are
        built from multiple radar echoes.

        Args:
            input_header:   A DataFrame containing the packets to be processed. Expected usage
                            is to call decode_metadata to return the full set of packets in the
                            file, select the desired packets from these, and supply the result
                            as the input to this function.

        Returns:
            The complex I/Q values outputted by the Sentinel-1 SAR instrument
            and downlinked in the specified space packets.

        """
        # Check we can output this data as a single block.
        # TODO: More rigorous checks here
        # TODO: Fix checks when only one packet supplied as input_header
        # TODO: Report progress since this takes a long time
        swath_numbers = input_header[cnst.SWATH_NUM_FIELD_NAME].unique()
        num_quads = input_header[cnst.NUM_QUADS_FIELD_NAME].unique()
        if not len(swath_numbers) == 1:
            logging.error(f"Supplied mismatched header info - too many swath numbers {swath_numbers}")
            raise Exception(f"Received {len(swath_numbers)} swath numbers {swath_numbers}, expected 1.")
        if not len(num_quads) == 1:
            logging.error(f"Supplied mismatched header info - too many number of quads {num_quads}")
            raise Exception(f"Received {len(num_quads)} different number of quads {num_quads}, expected 1.")

        packet_counter = 0
        packets_to_process = len(input_header)
        nq = input_header[cnst.NUM_QUADS_FIELD_NAME].unique()[0]

        output_data = np.zeros([packets_to_process, nq * 2], dtype=np.complex64)

        with open(self.filename, "rb") as f:
            # Each iteration of the below loop will process one space packet.
            # An input file typically consists of many packets.
            while packet_counter < packets_to_process:
                try:
                    this_header, packet_data_bytes = self._read_single_packet(f)
                except NoMorePacketsException:
                    break

                # Comparing space packet count is faster than comparing entire row
                if (
                    this_header[cnst.SPACE_PACKET_COUNT_FIELD_NAME]
                    in input_header[cnst.SPACE_PACKET_COUNT_FIELD_NAME].values
                ):
                    logging.debug(f"Decoding data from packet: {this_header}")
                    try:
                        baqmod = this_header[cnst.BAQ_MODE_FIELD_NAME]
                        nq = this_header[cnst.NUM_QUADS_FIELD_NAME]
                        data_decoder = UserDataDecoder(packet_data_bytes, baqmod, nq)
                        this_data_packet = data_decoder.decode()
                        output_data[packet_counter, :] = this_data_packet
                    except Exception as e:
                        logging.error(
                            (
                                f"Failed to process packet {packet_counter} "
                                f"with Space Packet Count {this_header[cnst.SPACE_PACKET_COUNT_FIELD_NAME]}\n{e}"
                            )
                        )
                        output_data[packet_counter, :] = 0

                    logging.debug("Finished decoding packet data")

                    packet_counter += 1

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
