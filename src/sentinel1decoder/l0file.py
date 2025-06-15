import os
from typing import Dict, Optional, cast

import numpy as np
import pandas as pd

from sentinel1decoder import constants as c
from sentinel1decoder.l0decoder import Level0Decoder
from sentinel1decoder.utilities import read_subcommed_data


class Level0File:
    "A Sentinel-1 Level 0 file contains several 'bursts', or azimuth blocks"

    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._decoder = Level0Decoder(filename)

        # Split metadata into blocks of consecutive packets w/ const swath number
        self._packet_metadata = self._index_df_on_bursts(self._decoder.decode_metadata())

        # Only calculate ephemeris if requested
        self._ephemeris: Optional[pd.DataFrame] = None

        # Only decode radar echoes from bursts if that data is requested
        self._burst_data_dict: Dict[int, Optional[np.ndarray]] = dict.fromkeys(
            self._packet_metadata.index.unique(level=c.BURST_NUM_FIELD_NAME), None
        )

    @property
    def filename(self) -> str:
        """
        Get the filename (including filepath) of this file.
        """
        return self._filename

    @property
    def packet_metadata(self) -> pd.DataFrame:
        """
        Get a dataframe of the metadata from all space packets in this file
        """
        return self._packet_metadata

    @property
    def ephemeris(self) -> pd.DataFrame:
        """
        Get the sub-commutated satellite ephemeris data for this file.
        Will be calculated upon first request for this data.
        """
        if self._ephemeris is None:
            self._ephemeris = read_subcommed_data(self.packet_metadata)

        return self._ephemeris

    def get_burst_metadata(self, burst: int) -> pd.DataFrame:
        """
        Get a dataframe of the metadata from all packets in a given burst.
        A burst is a set of consecutive space packets with constant number of samples.

        Args:
            burst:  The burst to retreive data for. Bursts are numbered
                    consecutively from the start of the file (1, 2, 3...)
        """

        # packet_metadata is a multiindexed pd.DataFrame so using loc like this returns a pd.DataFrame too
        return cast(pd.DataFrame, self.packet_metadata.loc[burst])

    def get_burst_data(self, burst: int, try_load_from_file: bool = True) -> np.ndarray:
        """
        Get an array of complex samples from the SAR instrument for a given burst.
        A burst is a set of consecutive space packets with constant number of samples.

        Args:
            burst:  The burst to retreive data for. Bursts are numbered
                    consecutively from the start of the file (1, 2, 3...)
            try_load_from_file: Attempt to load the burst data from .npy file first.
                                File can be generated using save_burst_data
        """
        if self._burst_data_dict[burst] is None:
            if try_load_from_file:
                save_file_name = self._generate_burst_cache_filename(burst)
                try:
                    self._burst_data_dict[burst] = np.load(save_file_name)
                finally:
                    return self.get_burst_data(burst, try_load_from_file=False)
            else:
                self._burst_data_dict[burst] = self._decoder.decode_packets(self.get_burst_metadata(burst))

        return self._burst_data_dict[burst]  # type: ignore

    def save_burst_data(self, burst: int) -> None:
        save_file_name = self._generate_burst_cache_filename(burst)
        np.save(save_file_name, self.get_burst_data(burst))

    # ------------------------------------------------------------------------
    # ----------------------- Private class functions ------------------------
    # ------------------------------------------------------------------------
    def _generate_burst_cache_filename(self, burst: int) -> str:
        return os.path.splitext(self.filename)[0] + "_b" + str(burst) + ".npy"

    def _index_df_on_bursts(self, packet_metadata: pd.DataFrame) -> pd.DataFrame:
        """
        Takes packet metadata dataframe and splits into blocks of consecutive
        packets with the same swath number and the same number of quads.

        Args:
            packet_metadata: pandas dataframe of packet metadata

        Returns:
            The same dataframe with added burst number index
        """
        packet_metadata = packet_metadata.groupby(
            packet_metadata[[c.SWATH_NUM_FIELD_NAME, c.NUM_QUADS_FIELD_NAME]].diff().ne(0).any(axis=1).cumsum(),
            group_keys=True,
        ).apply(lambda x: x)

        packet_metadata.index.names = [
            c.BURST_NUM_FIELD_NAME,
            c.PACKET_NUM_FIELD_NAME,
        ]

        for name, group in packet_metadata.groupby(level=c.BURST_NUM_FIELD_NAME):
            if not _check_series_is_constant(group[c.NUM_QUADS_FIELD_NAME]):
                raise Exception(f"Found too many number of quads in azimuth block {name}")

        return packet_metadata


# Private utility functions
def _check_series_is_constant(series: pd.Series) -> bool:
    """
    Check if the specified pandas series contains all the same vals.

    Args:
        series: Pandas series of values

    Returns:
        True if the series values are all the same, false otherwise
    """
    return cast(bool, series.nunique() == 1)  # type: ignore
