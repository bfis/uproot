#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numbers
import math

import numpy

import uproot.rootio

class TH1Methods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __repr__(self):
        if hasattr(self, "fName"):
            return "<{0} {1} 0x{2:012x}>".format(self.classname, repr(self.fName), id(self))
        else:
            return "<{0} at 0x{1:012x}>".format(self.classname, id(self))

    @property
    def num(self):
        return self.fXaxis.fNbins

    @property
    def low(self):
        return self.fXaxis.fXmin

    @property
    def high(self):
        return self.fXaxis.fXmax

    @property
    def underflows(self):
        return self[0]

    @property
    def overflows(self):
        return self[-1]

    @property
    def values(self):
        return self[1:-1]

    def fill(self, data, weights=None):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if isinstance(data, numbers.Real):
            if weights is None:
                weights = 1.0

            if data < low:
                self[0] += weight
            elif data >= high:
                self[-1] += weight
            else:
                self[int(math.floor(self.fXaxis.fNbins * (data - low) / (high - low)))] += weights

        else:
            if isinstance(weights, numbers.Real):
                weights = numpy.empty_like(data)

            freq, edges = numpy.histogram(data,
                                          bins=numpy.linspace(low, high, self.fXaxis.fNbins + 1),
                                          weights=weights,
                                          density=False)
            for i, x in enumerate(freq):
                self[i + 1] += x

            underflows = (data < low)
            overflows = (data >= high)

            if isinstance(weights, numpy.ndarray):
                self[0] += weights[underflows].sum()
                self[-1] += weights[overflows].sum()
            else:
                self[0] += underflows.sum()
                self[-1] += overflows.sum()

uproot.rootio.methods["TH1"] = TH1Methods

# holoviews.Spread((e[numpy.repeat(numpy.arange(len(f) + 1), 2)[1:-1]],) + (f[numpy.repeat(numpy.arange(len(f)), 2)]/2.0,) * 2)
