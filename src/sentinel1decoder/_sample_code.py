class SampleCode:
    """Sample code conistsing of sign bit and magnitude code."""

    def __init__(self, sign: int, mcode: int) -> None:
        self._sign = sign
        self._mcode = mcode

    def __repr__(self) -> str:
        return "SampleCode(%(sign)i, %(mcode)i)" % {
            "sign": self._sign,
            "mcode": self._mcode,
        }

    @property
    def sign(self) -> int:
        return self._sign

    @property
    def mcode(self) -> int:
        return self._mcode
