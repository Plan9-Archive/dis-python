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

import opcodes

XMAGIC = 0x0c8030
SMAGIC = 0x0e1722

def _read(f, format):

    size = calcsize(format)
    return unpack(format, f.read(size))[0]

def read_B(f):

    return unpack(">B", f.read(1))[0]

def read_OP(f):

    at = f.tell()
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

    return unpack(">i", f.read(4))

def read_F(f):

    return unpack(">d", f.read(8))

def read_SO(f):

    return unpack(">H", f.read(2))

def read_SI(f):

    return unpack(">h", f.read(2))

def read_LO(f):

    return unpack(">i", f.read(4))


class DisError(Exception):
    pass


class Dis:

    def __init__(self, file_name = None):
    
        if file_name:
            self.read(open(file_name, "rb"), file_name)
    
    def error(self, message):
    
        if self.file_name:
            message += " in file '%s'." % self.file_name
        else:
            message += "."
        
        return DisError(message)
    
    def read(self, f, file_name = None):
    
        self.file_name = file_name
        
        # Read the header.
        magic = read_OP(f)
        
        if magic == XMAGIC:
            self.signed = False
        elif magic == SMAGIC:
            self.signed = True
        else:
            raise self.error("Invalid magic number")
        
        if self.signed:
            length = _read(f, ">I")
            self.signature = f.read(length)
        
        self.runtime_flag = RuntimeFlag(read_OP(f))
        self.stack_extent = read_OP(f)
        self.code_size = read_OP(f)
        self.data_size = read_OP(f)
        self.type_size = read_OP(f)
        self.link_size = read_OP(f)
        self.entry_pc = read_OP(f)
        self.entry_type = read_OP(f)
        
        self.read_code(f)
    
    def read_code(self, f):
    
        self.code = []
        
        i = 0
        while i < self.code_size:
        
            self.code.append(Instruction(f))
            i += 1


class RuntimeFlag:

    # Defined in Inferno's include/isa.h:
    MUSTCOMPILE = 0x01
    DONTCOMPILE = 0x02
    SHAREMP     = 0x04
    DYNMOD      = 0x08
    HASLDTO     = 0x10
    HASEXCEPT   = 0x20
    HASLDT      = 0x40
    
    def __init__(self, value):
        self.value = value


class Instruction:

    def __init__(self, f):
    
        self.opcode = read_B(f)
        self.address_mode = read_B(f)
        
        middle = self.address_mode & 0xc0
        
        if middle == 0x40:
            self.middle = read_OP(f)
            self.middle_type = "$SI"
        elif middle == 0x80:
            self.middle = read_OP(f)
            self.middle_type = "SO(FP)"
        elif middle == 0xc0:
            self.middle = read_OP(f)
            self.middle_type = "SO(MP)"
        else:
            self.middle = None
            self.middle_type = None
        
        source = (self.address_mode & 0x38) >> 3
        self.source, self.source_type = self.read_operand(source, f)
        
        destination = self.address_mode & 0x07
        self.destination, self.destination_type = self.read_operand(destination, f)
    
    def __repr__(self):
    
        try:
            name = opcodes.names[self.opcode]
        except IndexError:
            name = hex(self.opcode)
        
        operands = []
        comments = []
        
        for op, optype in (self.source, self.source_type), \
                          (self.destination, self.destination_type):
        
            if optype == "LO(MP)":
                operands.append(op)
                comments.append(optype)
            elif optype == "LO(FP)":
                operands.append(op)
                comments.append(optype)
            elif optype == "$OP":
                operands.append(op)
                comments.append(optype)
            elif optype == "SO(SO(MP))":
                operands += list(op)
                comments.append(optype)
            elif optype == "SO(SO(FP))":
                operands += list(op)
                comments.append(optype)
        
        if comments:
            return name + " " + ", ".join(map(str, operands)) + " ; " + ", ".join(comments)
        else:
            return name + " " + ", ".join(map(str, operands))
    
    def read_operand(self, operand, f):
    
        if operand == 0x00:
            operand = read_OP(f)
            operand_type = "LO(MP)"
        elif operand == 0x01:
            operand = read_OP(f)
            operand_type = "LO(FP)"
        elif operand == 0x02:
            operand = read_OP(f)
            operand_type = "$OP"
        elif operand == 0x04:
            operand = (read_OP(f), read_OP(f))
            operand_type = "SO(SO(MP))"
        elif operand == 0x05:
            operand = (read_OP(f), read_OP(f))
            operand_type = "SO(SO(FP))"
        else:
            operand = None
            operand_type = None
        
        return operand, operand_type
