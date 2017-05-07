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

def read_SO(f):

    return unpack(">H", f.read(2))[0]

def read_SI(f):

    return unpack(">h", f.read(2))[0]

def read_LO(f):

    return unpack(">i", f.read(4))[0]


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
        self.read_types(f)
        self.read_data(f)
        
        self.module_name = read_C(f)
        
        self.read_link(f)
    
    def read_code(self, f):
    
        self.code = []
        i = 0
        
        while i < self.code_size:
            self.code.append(Instruction(f))
            i += 1
    
    def read_types(self, f):
    
        self.types = []
        i = 0
        
        while i < self.type_size:
            self.types.append(Type(f))
            i += 1
    
    def read_data(self, f):
    
        self.data = []
        addresses = []
        base = 0
        offset = 0
        
        while True:
        
            at = f.tell()
            
            code = read_B(f)
            if code == 0:
                break
            
            count = code & 0x0f
            array_type = code >> 4
            
            if count == 0:
                count = read_OP(f)
            
            offset = read_OP(f)
            
            if not 1 <= array_type <= 8:
                raise self.error("Unknown type in data item at 0x%x" % at)
            
            elif array_type == 5:
                # Array
                type_index = _read(f, ">I")
                length = _read(f, ">I")
                type_ = self.types[type_index]
                #print "Array", type_, type_.size, length
            elif array_type == 6:
                # Set array address
                index = _read(f, ">I")
                #print "Set array address", index, "(offset=%i)" % offset
                addresses.append(base)
                base = offset + index
            elif array_type == 7:
                # Restore load address
                #print "Restore load address"
                base = addresses.pop()
            else:
                self.data.append(Data(f, code, count, base + offset, array_type))
    
    def read_link(self, f):
    
        self.link = []
        i = 0
        
        while i < self.link_size:
            self.link.append(Link(f))
            i += 1
    
    def list(self):
    
        address = 0
        for ins in self.code:
            print hex(address), str(ins)
            address += ins.size


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
    
        self.start = f.tell()
        
        self.opcode = read_B(f)
        self.address_mode = read_B(f)
        
        middle = self.address_mode & 0xc0
        self.middle, self.middle_type = self.read_middle_operand(middle, f)
        
        source = (self.address_mode & 0x38) >> 3
        self.source, self.source_type = self.read_operand(source, f)
        
        destination = self.address_mode & 0x07
        self.destination, self.destination_type = self.read_operand(destination, f)
        
        self.size = f.tell() - self.start
    
    def read_operand(self, operand, f):
    
        # Since we shift the address flags for the source operand, we can
        # check both source and destination operands using the same values.
        
        if operand == 0x00:
            operand = read_OP(f)
            operand_type = "LO(MP)"
        elif operand == 0x01:
            operand = read_OP(f)
            operand_type = "LO(FP)"
        elif operand == 0x02:
            operand = read_OP(f)
            operand_type = "$OP"
        
        # No operand for 0x03.
        
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
    
    def read_middle_operand(self, operand, f):
    
        # The middle operand bits are not shifted.
        
        if operand == 0x40:
            operand = read_OP(f)
            operand_type = "$SI"
        elif operand == 0x80:
            operand = read_OP(f)
            operand_type = "SO(FP)"
        elif operand == 0xc0:
            operand = read_OP(f)
            operand_type = "SO(MP)"
        else:
            operand = None
            operand_type = None
        
        return operand, operand_type
    
    def __repr__(self):
    
        try:
            name = opcodes.names[self.opcode]
        except IndexError:
            name = hex(self.opcode)
        
        operands = []
        comments = []
        
        for op, optype in (self.source, self.source_type), \
                          (self.middle, self.middle_type), \
                          (self.destination, self.destination_type):
        
            if optype == "$SI":
                operands.append("$%x" % op)
            elif optype == "SO(FP)":
                operands.append("%i(fp)" % op)
            elif optype == "SO(MP)":
                operands.append("%i(mp)" % op)
            elif optype == "LO(MP)":
                operands.append("%i(mp)" % op)
            elif optype == "LO(FP)":
                operands.append("%i(fp)" % op)
            elif optype == "$OP":
                operands.append("$%x" % op)
            elif optype == "SO(SO(MP))":
                operands.append("%i(%i(mp))" % op)
            elif optype == "SO(SO(FP))":
                operands.append("%i(%i(fp))" % op)
        
        return name + " " + ", ".join(operands)


class Type:

    def __init__(self, f):
    
        self.desc_number = read_OP(f)
        self.size = read_OP(f)
        self.number_ptrs = read_OP(f)
        self.array = f.read(self.number_ptrs)
    
    def is_pointer(self, address):
    
        # Each bit in the array represents a word in the type. If the bit is 1
        # then the word contains a pointer.
        
        # Convert the address of a word to a bit offset in the array.
        bit = address / 4
        # Extract the byte containing the bit we want to check.
        byte = self.array[bit / 8]
        # Check whether the bit is 1 or 0, returning True for 1 and False for 0.
        mask = 1 << (bit % 8)
        return (ord(byte) & mask) != 0


class Data:

    array_types = ["Invalid", "8-bit byte", "32-bit word",
                   "UTF-8 encoded string", "64-bit float", "Array",
                   "Set array address", "Restore load address"]
    
    def __init__(self, f, code, count, address, array_type):
    
        self.code = code
        self.count = count
        self.address = address
        self.array_type = array_type
        
        self.array = []
        base = 0
        i = 0
        while i < count:
        
            if array_type == 1:
                # 8-bit byte
                self.array.append(read_B(f))
            elif array_type == 2:
                # 32-bit word
                self.array.append(read_W(f))
            elif array_type == 3:
                # UTF-8 encoded string (each item is a character)
                self.array.append(f.read(1))
            elif array_type == 4:
                # 64-bit float
                self.array.append(read_F(f))
            elif array_type == 8:
                # 64-bit integer
                self.array.append(read_L(f))
            
            i += 1
    
    def data(self):
    
        if self.array_type == 3:
            return "".join(self.array)
        else:
            return self.array
    
    def __repr__(self):
    
        return "<%s.%s (%s) %s>" % (self.__module__, self.__class__.__name__,
            self.array_types[self.array_type], repr(self.data()))


class Link:

    def __init__(self, f):
    
        self.pc = read_OP(f)
        self.desc_number = read_OP(f)
        self.sig = read_W(f)
        self.name = read_C(f)
