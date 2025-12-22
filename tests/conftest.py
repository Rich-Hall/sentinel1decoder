from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class FDBAQSpecExample:
    page: int
    description: str
    brc: int
    thidx: int
    huffman_bits: str
    expected_value: float


@dataclass(frozen=True)
class BypassSpecExample:
    page: int
    description: str
    bits: str
    expected_value: float


@pytest.fixture(scope="session")
def bypass_spec_examples() -> list[BypassSpecExample]:
    """
    Explicit numeric Bypass examples extracted verbatim from:

        Sentinel-1 SAR Space Packet Protocol Data Unit

    Each example includes the page number where it appears.
    """
    return [
        BypassSpecExample(
            page=61,
            description="Bypass mode example",
            bits="1010111100",
            expected_value=-188,
        ),
    ]


@pytest.fixture(scope="session")
def fdbaq_spec_examples() -> list[FDBAQSpecExample]:
    """
    Explicit numeric FDBAQ examples extracted verbatim from:

      Sentinel-1 SAR Space Packet Protocol Data Unit

    Each example includes the page number where it appears.
    """

    return [
        FDBAQSpecExample(
            page=74,
            description="Example 1 - normal reconstruction (NRL x SF)",
            brc=2,
            thidx=239,
            huffman_bits="0111110",
            # The spec lists the result as 596.594, but the example in the spec seems to be incorrect.
            # The spec calculates this value as follows:
            #
            # S_value = (-1)^sign * NRL[brc=2, mcode=5] * SF[thidx=239]
            # S_value = (-1)^0 * 2.5084 * 237.19 = 594.96
            #
            # However, 2.5084 does not match the NRL table for brc=2, mcode=5.
            # In fact, it doesn't appear anywhere in the NRL table for any value.
            # The value of NRL[brc=2, mcode=5] is instead listed as 2.5369.
            # The SF used in the calculation seems to be correct.
            expected_value=2.5369 * 237.19,
        ),
        FDBAQSpecExample(
            page=75,
            description="Example 2 - simple reconstruction (low THIDX)",
            brc=3,
            thidx=3,
            huffman_bits="111111111",
            expected_value=-9.0,
        ),
        FDBAQSpecExample(
            page=75,
            description="Example 3 - normal reconstruction (NRL x SF)",
            brc=3,
            thidx=5,
            huffman_bits="111111111",
            # The spec lists this result as -9.48, but the example in the spec also seems to be incorrect.
            # The spec calculates this value as follows:
            #
            # S_value = (-1)^sign * B3[thidx] when mcode == 9
            # S_value = (-1)^1 * 9.4800 = -9.4800
            #
            # However, the value of B3[thidx=5] is 9.5000, not 9.4800.
            expected_value=-9.5,
        ),
        FDBAQSpecExample(
            page=-1,
            description=(
                "Not in the spec - this test case includes HCodes of max possible "
                "length to test for integer overflows"
            ),
            brc=4,
            thidx=0,
            huffman_bits="1111111111",
            expected_value=-15,
        ),
    ]
