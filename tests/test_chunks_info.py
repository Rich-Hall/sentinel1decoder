from __future__ import annotations

import logging

import pandas as pd

from sentinel1decoder import _field_names as fn
from sentinel1decoder import chunks_info
from sentinel1decoder.enums import SignalType


class _FakeLevel0File:
    def __init__(self, inputfile: str) -> None:
        self.inputfile = inputfile
        self.packet_metadata = pd.DataFrame(
            {
                "Signal Type": [
                    SignalType.ECHO,
                    SignalType.ECHO,
                    SignalType.NOISE,
                    SignalType.RX_CAL,
                    SignalType.ECHO,
                ]
            },
            index=pd.MultiIndex.from_tuples(
                [
                    (0, 0), # chunk=0, packet=0
                    (0, 1),
                    (1, 0),
                    (2, 0),
                    (5, 0),
                ],
                names=[fn.ACQUISITION_CHUNK_NUM_DECODED, fn.PACKET_NUM_DECODED],
            ),
        )

    def get_acquisition_chunk_metadata(self, acquisition_chunk: int) -> pd.DataFrame:
        return self.packet_metadata.loc[acquisition_chunk]


def test_extract_sm_chunk_info_logs_and_groups(monkeypatch, caplog) -> None:
    monkeypatch.setattr(chunks_info, "Level0File", _FakeLevel0File)
    caplog.set_level(logging.INFO, logger=chunks_info.logger.name)

    l0file, result = chunks_info.extract_SM_chunk_info("dummy-file", visualize=True)

    assert isinstance(l0file, _FakeLevel0File)
    assert result["SM"] == [0, 5]
    assert result["noise"] == [1]
    assert result["rx_cal_chunks"] == [2]

    log_text = caplog.text
    assert "SM chunks" in log_text
    assert "noise chunks" in log_text
    assert "rx_cal_chunks" in log_text