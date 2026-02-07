from __future__ import annotations

import os
import warnings
from typing import Any, Iterator, Optional, cast

import numpy as np
import pandas as pd

from sentinel1decoder import _field_names as fn
from sentinel1decoder.l0decoder import Level0Decoder
from sentinel1decoder.utilities import read_subcommed_data


class Level0File:
    "A Sentinel-1 Level 0 file contains several 'acquisition chunks', or azimuth blocks"

    def __init__(self, filename: str) -> None:
        """Initialize the Level0File.

        Args:
            filename: The filename of the Sentinel-1 Level 0 file to read.
        """

        self._filename = filename
        self._decoder = Level0Decoder(filename)

        packet_metadata = self._decoder.decode_metadata(return_raw=False)
        self._packet_metadata = packet_metadata

        # Only calculate raw packet metadata if requested
        self._raw_packet_metadata: Optional[pd.DataFrame] = None

        # Only calculate ephemeris if requested
        self._ephemeris: Optional[pd.DataFrame] = None

        # Only decode radar echoes from acquisition chunks if that data is requested
        self._acquisition_chunk_data_dict: dict[int, Optional[np.ndarray]] = dict.fromkeys(
            self._packet_metadata.index.unique(level=fn.ACQUISITION_CHUNK_NUM_DECODED), None
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
    def raw_packet_metadata(self) -> pd.DataFrame:
        """
        Get a dataframe of the raw metadata from all space packets in this file
        """
        if self._raw_packet_metadata is None:
            self._raw_packet_metadata = self._decoder.decode_metadata(return_raw=True)
        return self._raw_packet_metadata

    @property
    def ephemeris(self) -> pd.DataFrame:
        """
        Get the sub-commutated satellite ephemeris data for this file.
        Will be calculated upon first request for this data.
        """
        if self._ephemeris is None:
            self._ephemeris = read_subcommed_data(self.packet_metadata)

        return self._ephemeris

    def get_acquisition_chunk_metadata(self, acquisition_chunk: int) -> pd.DataFrame:
        """
        Get a dataframe of the metadata from all packets in a given acquisition chunk.
        An acquisition chunk is a set of consecutive space packets where:
        - The signal type is constant
        - The swath number is constant
        - The number of quads is constant
        - The BAQ mode is constant
        - The SWST is constant
        - The SWL is constant
        - The PRI is constant
        - The PRI count increments by 1 packet-by-packet (wrapping around at 2^32-1)
        - The Azimuth beam address increases monotonically
        - The Elevation beam address remains constant

        Args:
            acquisition_chunk:  The acquisition chunk to retreive data for. Acquisition chunks are numbered
                    consecutively from the start of the file (1, 2, 3...)
        """

        # packet_metadata is a multiindexed pd.DataFrame so using loc like this returns a pd.DataFrame too
        return cast(pd.DataFrame, self.packet_metadata.loc[acquisition_chunk])

    @property
    def acquisition_chunks(self) -> list[int]:
        """List of acquisition chunk IDs in this file (0-indexed)."""
        return list(self._packet_metadata.index.unique(level=fn.ACQUISITION_CHUNK_NUM_DECODED))

    def get_acquisition_chunk_constants(self, acquisition_chunk: int) -> dict[str, Any]:
        """Get the constant metadata values for an acquisition chunk.

        Within a chunk, these fields are the same for every packet: signal_type,
        swath_num, num_quads, baq_mode, swst, swl, pri, elevation_beam_address.

        Args:
            acquisition_chunk: The acquisition chunk ID (0-indexed).

        Returns:
            Dict with keys: signal_type, swath_num, num_quads, baq_mode, swst,
            swl, pri, elevation_beam_address. Values are from the first packet
            in the chunk.
        """
        meta = self.get_acquisition_chunk_metadata(acquisition_chunk)
        row = meta.iloc[0]
        return {
            "signal_type": row[fn.SIGNAL_TYPE_DECODED],
            "swath_num": row[fn.SWATH_NUM_DECODED],
            "num_quads": row[fn.NUM_QUADS_DECODED],
            "baq_mode": row[fn.BAQ_MODE_DECODED],
            "swst": row[fn.SWST_DECODED],
            "swl": row[fn.SWL_DECODED],
            "pri": row[fn.PRI_DECODED],
            "elevation_beam_address": row[fn.EBADR_DECODED],
        }

    def iter_chunks_matching(self, **kwargs: Any) -> Iterator[int]:
        """Yield acquisition chunk IDs whose constants match all given criteria.

        Args:
            **kwargs: Field names and values to match. Keys must be among:
                signal_type, swath_num, num_quads, baq_mode, swst, swl, pri,
                elevation_beam_address.

        Yields:
            Chunk IDs that match all criteria.

        Example:
            >>> for chunk in l0.iter_chunks_matching(signal_type=SignalType.ECHO):
            ...     process_echo_chunk(chunk)
        """
        for chunk_id in self.acquisition_chunks:
            constants = self.get_acquisition_chunk_constants(chunk_id)
            if all(constants.get(k) == v for k, v in kwargs.items()):
                yield chunk_id

    def get_acquisition_chunk_data(self, acquisition_chunk: int, try_load_from_file: bool = True) -> np.ndarray:
        """
        Get an array of complex samples from the SAR instrument for a given acquisition chunk.
        An acquisition chunk is a set of consecutive space packets where:
        - The signal type is constant
        - The swath number is constant
        - The number of quads is constant
        - The BAQ mode is constant
        - The SWST is constant
        - The SWL is constant
        - The PRI is constant
        - The PRI count increments by 1 packet-by-packet (wrapping around at 2^32-1)
        - The Azimuth beam address increases monotonically
        - The Elevation beam address remains constant
        """
        if self._acquisition_chunk_data_dict[acquisition_chunk] is None:
            if try_load_from_file:
                save_file_name = self._generate_acquisition_chunk_cache_filename(acquisition_chunk)
                try:
                    self._acquisition_chunk_data_dict[acquisition_chunk] = np.load(save_file_name)
                except (OSError, FileNotFoundError, ValueError):
                    pass
                return self.get_acquisition_chunk_data(acquisition_chunk, try_load_from_file=False)
            else:
                acquisition_chunk_header = self._packet_metadata.loc[[acquisition_chunk]]
                self._acquisition_chunk_data_dict[acquisition_chunk] = self._decoder.decode_packets(
                    acquisition_chunk_header
                )

        return self._acquisition_chunk_data_dict[acquisition_chunk]  # type: ignore

    def save_acquisition_chunk_data(self, acquisition_chunk: int) -> None:
        """Save the radar echoes for a given acquisition chunk to a .npy file.

        Args:
            acquisition_chunk: The acquisition chunk to save the data for.
        """

        save_file_name = self._generate_acquisition_chunk_cache_filename(acquisition_chunk)
        np.save(save_file_name, self.get_acquisition_chunk_data(acquisition_chunk))

    # ------------------------------------------------------------------------
    # ----------------------- Deprecated aliases ------------------------------
    # ------------------------------------------------------------------------

    def get_burst_metadata(self, burst: int) -> pd.DataFrame:
        """Deprecated. Use get_acquisition_chunk_metadata instead."""
        warnings.warn(
            "get_burst_metadata is deprecated and will be removed in a future version, "
            "use get_acquisition_chunk_metadata instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_acquisition_chunk_metadata(burst)

    def get_burst_data(self, burst: int, try_load_from_file: bool = True) -> np.ndarray:
        """Deprecated. Use get_acquisition_chunk_data instead."""
        warnings.warn(
            "get_burst_data is deprecated and will be removed in a future version, "
            "use get_acquisition_chunk_data instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_acquisition_chunk_data(burst, try_load_from_file=try_load_from_file)

    def save_burst_data(self, burst: int) -> None:
        """Deprecated. Use save_acquisition_chunk_data instead."""
        warnings.warn(
            "save_burst_data is deprecated and will be removed in a future version, "
            "use save_acquisition_chunk_data instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.save_acquisition_chunk_data(burst)

    # ------------------------------------------------------------------------
    # ----------------------- Private class functions ------------------------
    # ------------------------------------------------------------------------
    def _generate_acquisition_chunk_cache_filename(self, acquisition_chunk: int) -> str:
        """Generate a filename for a cache file for a given acquisition chunk.

        Args:
            acquisition_chunk: The acquisition chunk to generate a cache filename for.

        Returns:
            A filename for a cache file for a given acquisition chunk.
        """

        return os.path.splitext(self.filename)[0] + "_acquisition_chunk_" + str(acquisition_chunk) + ".npy"
