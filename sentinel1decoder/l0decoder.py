# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 22:02:54 2022.

@author: richa
"""
import logging
import numpy as np
import pandas as pd

from sentinel1decoder import _headers as hdrs
from sentinel1decoder._user_data_decoder import user_data_decoder
from sentinel1decoder.constants import *


class Level0Decoder:
    """Decoder for Sentinel-1 Level 0 files."""

    def __init__(self, filename, log_level=logging.WARNING):
        # TODO: Better logging functionality
        logging.basicConfig(filename='output_log.log', level=log_level)
        logging.debug("Initialized logger")

        self.filename = filename

    def decode_metadata(self):
        """Decode the full header of each packet in a Sentinel-1 Level 0 file.

        Sentinel-1 Space Packet format consists of a primary header of 6 bytes,
        followed by a packet data field. The first 62 bytes of the packet data
        field are taken up by the packet secondary header.

        Returns
        -------
        A Pandas Dataframe containing the decoded metadata.

        """
        # TODO: Fix docstring
        packet_counter = 0
        output_row_list = []

        with open(self.filename, 'rb') as f:

            # Each iteration of the below loop will process one space packet.
            # An input file typically consists of many packets.
            # We don't know how many ahead of time.
            while True:

                # ---------------------------------------------------------
                # PACKET PRIMARY HEADER (6 bytes)
                # ---------------------------------------------------------
                # First check if we have reached the end of the file

                # TODO: Break this out into separate function
                data_buffer = f.read(6)
                if not data_buffer:
                    break

                output_dictionary_row = hdrs.decode_primary_header(data_buffer)
                packet_counter = packet_counter + 1

                # ---------------------------------------------------------
                # PACKET DATA FIELD (between 62 and 65534 bytes)
                # ---------------------------------------------------------
                # First 62 bytes contain the PACKET SECONDARY HEADER

                pkt_data_len = output_dictionary_row[PACKET_DATA_LENGTH_FIELD_NAME]
                packet_data = f.read(pkt_data_len)
                secondary_hdr = hdrs.decode_secondary_header(packet_data[:62])
                output_dictionary_row.update(secondary_hdr)

                # ---------------------------------------------------------
                # END OF SECONDARY HEADER.
                # User data follows for bytes 62 ---> packet_data_length
                # ---------------------------------------------------------

                output_row_list.append(output_dictionary_row)

            output_dataframe = pd.DataFrame(output_row_list)
            return output_dataframe

    def decode_file(self, input_header):
        """Decode the user data payload from the specified space packets.

        Packet data typically consists of a single radar echo. SAR images are
        built from multiple radar echoes.

        Parameters
        ----------
        input_header : Pandas DataFrame
            A DataFrame containing the packets to be processed. Expected usage
            is to call decode_metadata to return the full set of packets in the
            file, select the desired packets from these, and supply the result
            as the input to this function. Packet Primary and Secondary headers
            must match exactly for a packet to be processed.

        Returns
        -------
        output_data : Numpy Array
            The complex I/Q values outputted by the Sentinel-1 SAR instrument
            and downlinked in the specified space packets.

        """
        # Check we can output this data as a single block.
        # TODO: More rigorous checks here
        # TODO: Fix checks when only one packet supplied as input_header
        # TODO: Report progress since this takes a long time
        swath_numbers = input_header[SWATH_NUM_FIELD_NAME].unique()
        num_quads = input_header[NUM_QUADS_FIELD_NAME].unique()
        if not len(swath_numbers) == 1:
            logging.error(f"Supplied mismatched header info - too many swath numbers {swath_numbers}")
        if not len(num_quads) == 1:
            logging.error(f"Supplied mismatched header info - too many number of quads {num_quads}")

        packet_counter = 0
        packets_to_process = len(input_header)
        nq = input_header[NUM_QUADS_FIELD_NAME].unique()[0]

        output_data = np.zeros([packets_to_process, nq * 2], dtype=(complex))

        with open(self.filename, 'rb') as f:

            # Each iteration of the below loop will process one space packet.
            # An input file typically consists of many packets.
            while packet_counter < packets_to_process:

                # First check if we have reached the end of the file
                data_buffer = f.read(6)
                if not data_buffer:
                    break

                # We require several variables from the header
                this_header = hdrs.decode_primary_header(data_buffer)
                pkt_data_len = this_header[PACKET_DATA_LENGTH_FIELD_NAME]

                pkt_data = f.read(pkt_data_len)
                secondary_hdr = hdrs.decode_secondary_header(pkt_data[:62])
                this_header.update(secondary_hdr)

                # Comparing space packet count is faster than comparing entire row
                if this_header[SPACE_PACKET_COUNT_FIELD_NAME] in input_header[SPACE_PACKET_COUNT_FIELD_NAME].values:
                    logging.debug(f"Decoding data from packet: {this_header}")
                    try:
                        baqmod = this_header[BAQ_MODE_FIELD_NAME]
                        nq = this_header[NUM_QUADS_FIELD_NAME]
                        data_decoder = user_data_decoder(pkt_data[62:], baqmod, nq)
                        this_data_packet = data_decoder.decode()
                        output_data[packet_counter, :] = this_data_packet
                    except Exception as e:
                        logging.error(f"Failed to process packet {packet_counter} with Space Packet Count {this_header[SPACE_PACKET_COUNT_FIELD_NAME]}\n{e}")
                        output_data[packet_counter, :] = 0
                                      

                    logging.debug("Finished decoding packet data")

                    packet_counter += 1

        return output_data
