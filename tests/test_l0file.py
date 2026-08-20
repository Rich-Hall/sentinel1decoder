from __future__ import annotations

import pandas as pd

from sentinel1decoder import _field_names as fn
from sentinel1decoder.enums import SignalType
from sentinel1decoder.l0file import Level0File


def _file_from_chunks(chunks: list[tuple[int, int, SignalType, int]]) -> Level0File:
    """Build a Level0File with synthetic packet metadata.

    Each tuple is ``(chunk_id, n_packets, signal_type, swath_num)``.
    """
    records: list[dict[str, object]] = []
    index: list[tuple[int, int]] = []
    packet_num = 0
    for chunk_id, n_packets, signal_type, swath_num in chunks:
        for _ in range(n_packets):
            records.append(
                {
                    fn.SIGNAL_TYPE_DECODED: signal_type,
                    fn.SWATH_NUM_DECODED: swath_num,
                }
            )
            index.append((chunk_id, packet_num))
            packet_num += 1

    df = pd.DataFrame(records)
    df.index = pd.MultiIndex.from_tuples(
        index,
        names=[fn.ACQUISITION_CHUNK_NUM_DECODED, fn.PACKET_NUM_DECODED],
    )

    l0file = Level0File.__new__(Level0File)
    l0file._packet_metadata = df
    return l0file


def test_get_chunks_summary_groups_by_signal_and_swath() -> None:
    l0file = _file_from_chunks(
        [
            (0, 8, SignalType.ECHO, 10),
            (1, 20, SignalType.ECHO, 10),
            (2, 5, SignalType.NOISE, 11),
            (3, 12, SignalType.ECHO, 1),
            (4, 2, SignalType.RX_CAL, 10),
        ]
    )

    assert l0file.get_chunks_summary() == {
        "echo_swath_10": [0, 1],
        "noise_swath_11": [2],
        "echo": [3],
        "cal_rx": [4],
    }
