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

import collections
import struct

import uproot.write.sink.cursor
import uproot.write.TKey

class TDirectory(object):
    def __init__(self, tfile, fName, fNbytesName, fNbytesKeys=0, fSeekDir=100, fSeekParent=0, fSeekKeys=0, allocationbytes=1024, growfactor=10):
        self.tfile = tfile
        self.fName = fName
        self.fNbytesName = fNbytesName
        self.fNbytesKeys = fNbytesKeys
        self.fSeekDir = fSeekDir
        self.fSeekParent = fSeekParent
        self.fSeekKeys = fSeekKeys

        self.allocationbytes = allocationbytes
        self.growfactor = growfactor

        self.headkey = uproot.write.TKey.TKey(fClassName = b"TFile",
                                              fName      = self.fName,
                                              fObjlen    = self._format2.size,
                                              fSeekKey   = self.fSeekKeys,
                                              fNbytes    = self.fNbytesKeys)
        self.nkeys = 0
        self.keys = collections.OrderedDict()

    def update(self):
        fVersion = 1005
        fDatimeC = 1573188772   # FIXME!
        fDatimeM = 1573188772   # FIXME!
        self.cursor.update_fields(self.sink, self._format1, fVersion, fDatimeC, fDatimeM, self.fNbytesKeys, self.fNbytesName, self.fSeekDir, self.fSeekParent, self.fSeekKeys)

    def write(self, cursor, sink):
        cursor.write_string(sink, self.fName)
        cursor.write_data(sink, b"\x00")

        self.cursor = uproot.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink
        self.update()

        cursor.skip(self._format1.size)

    _format1 = struct.Struct(">hIIiiqqq")
    _format2 = struct.Struct(">i")

    def writekeys(self, cursor):
        self.fSeekKeys = cursor.index
        self.fNbytesKeys = self.headkey.fObjlen + self._format2.size + sum(x.fObjlen for x in self.keys)

        self.tfile._expandfile(uproot.write.sink.cursor.Cursor(self.fSeekKeys + self.allocationbytes))

        self.keycursor = uproot.write.sink.cursor.Cursor(self.fSeekKeys)
        self.headkey.write(self.keycursor, self.sink)
        self.nkeycursor = uproot.write.sink.cursor.Cursor(self.keycursor.index)
        self.keycursor.write_fields(self.sink, self._format2, self.nkeys)

        self.update()

    def setkey(self, newkey):
        newcursor = None

        if newkey.fName in self.keys:
            newcursor = uproot.write.sink.cursor.Cursor(self.fSeekKeys)

        self.headkey.fObjlen += newkey.fKeylen
        self.headkey.fNbytes += newkey.fKeylen
        self.nkeys += 1
        self.keys[newkey.fName] = newkey

        self.fNbytesKeys = self.headkey.fObjlen + self._format2.size + sum(x.fObjlen for x in self.keys)
        while self.fNbytesKeys > self.allocationbytes:
            self.allocationbytes *= self.growfactor
            newcursor = uproot.write.sink.cursor.Cursor(self.tfile.fSeekFree)

        if newcursor is not None:
            self.writekeys(newcursor)
        else:
            newkey.write(self.keycursor, self.sink)
            self.headkey.update()
            self.nkeycursor.update_fields(self.sink, self._format2, self.nkeys)
            self.update()

    def delkey(self, name):
        oldkey = self.keys[name]
        self.headkey.fObjlen -= oldkey
        self.headkey.fNbytes -= oldkey
        self.nkeys -= 1
        del self.keys[name]

        self.fNbytesKeys = self.headkey.fObjlen + self._format2.size + sum(x.fObjlen for x in self.keys)
        self.writekeys(uproot.write.sink.cursor.Cursor(self.fSeekKeys))
