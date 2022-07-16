# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 23:22:57 2022.

@author: richa
"""


class SampleCode:
    """Sample code conistsing of sign bit and magnitude code."""

    def __init__(self, sign, mcode):
        self.sign = sign
        self.mcode = mcode

    def __repr__(self):
        return "SampleCode(%(sign)i, %(mcode)i)" % {"sign": self.sign, "mcode": self.mcode}

    @property
    def get_sign(self):
        return self.sign

    @property
    def get_mcode(self):
        return self.mcode
