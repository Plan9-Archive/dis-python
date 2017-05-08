"""
Copyright (C) 2017 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from struct import calcsize, pack, unpack

def _read(f, format):

    size = calcsize(format)
    return unpack(format, f.read(size))[0]

def read_B(f):
    # byte, 8-bit unsigned
    return unpack(">B", f.read(1))[0]

def read_OP(f):

    s = f.read(1)
    v = unpack(">B", s)[0]
    
    encoding = v & 0xc0
    
    if encoding == 0x80:
        s += f.read(1)
        v = unpack(">H", s)[0] & 0x3fff
        if v >= 0x2000:
            v = v - 0x4000
    
    elif encoding == 0xc0:
        s += f.read(3)
        v = unpack(">I", s)[0] & 0x3fffffff
        if v >= 0x20000000:
            v = v - 0x40000000
    else:
        # The top bit is clear, the next-to-top bit can be 0 or 1.
        # -64 (0xc0) <= original value <= 63 (0x2f)
        # -64 (0x40) <= encoded value  <= 63 (0x2f)
        if encoding != 0:
            # The next-to-top bit is set meaning that
            # -64 <= original value <= -1
            v = v - 0x80
    
    return v

def read_W(f):
    # 32-bit word
    return unpack(">i", f.read(4))[0]

def read_F(f):
    # 64-bit float
    return unpack(">d", f.read(8))[0]

def read_L(f):
    # 64-bit big integer
    # Signed or unsigned? Assume signed for now.
    return unpack(">q", f.read(8))[0]

def read_P(f):
    # 32-bit pointer
    return unpack(">I", f.read(4))[0]

def read_C(f):
    # UTF-8 encoded string
    s = ""
    while True:
        c = f.read(1)
        if c == "\x00":
            break
        s += c
    
    return s

# Currently unused:

def read_SO(f):

    return unpack(">H", f.read(2))[0]

def read_SI(f):

    return unpack(">h", f.read(2))[0]

def read_LO(f):

    return unpack(">i", f.read(4))[0]
