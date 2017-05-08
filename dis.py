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
from utils import _read, read_B, read_C, read_OP, read_F, read_L, read_P, \
                  read_W

XMAGIC = 0x0c8030
SMAGIC = 0x0e1722


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
        
        if self.runtime_flag.contains(RuntimeFlag.HASLDT):
            self.read_ldt(f)
        
        self.path = read_C(f)
    
    def read_code(self, f):
    
        self.code = []
        i = 0
        
        while i < self.code_size:
            self.code.append(opcodes.Instruction().read(f))
            i += 1
    
    def read_types(self, f):
    
        self.types = []
        i = 0
        
        while i < self.type_size:
            self.types.append(Type(f))
            i += 1
    
    def read_data(self, f):
    
        # Use a dictionary to map pointers in the module's data area to items.
        self.data = {}
        
        # Maintain a list of individual data items for easy inspection.
        self.data_items = []
        
        # Use a list as a load address stack with an initial base address of 0.
        addresses = []
        base = 0
        
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
                address = base + offset
                item = Data(f, code, count, address, array_type)
                self.data_items.append(item)
                if address in self.data:
                    print "Overwriting existing data item at %x." % address
                self.data[address] = item
    
    def read_link(self, f):
    
        self.link = []
        i = 0
        
        while i < self.link_size:
            self.link.append(Link(f))
            i += 1
    
    def read_ldt(self, f):
    
        self.ldt = []
        
        # The Limbo compiler seems to include the number of initialised globals.
        self.initialised_globals = read_OP(f)
        
        # There seems to be a collection of sequences. Each sequence starts
        # with a number and is followed by that number of definitions.
        while True:
        
            # Read the number of definitions, stopping only when 0 is found.
            value = read_OP(f)
            if value == 0:
                break
            
            i = 0
            while i < value:
            
                self.ldt.append(LDT(f))
                i += 1
    
    def list(self):
    
        for i, ins in enumerate(self.code):
            print hex(i), str(ins)


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
    
    def contains(self, flags):
    
        return self.value & flags != 0


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
    
    def __repr__(self):
    
        return "<%s.%s (%s) %s>" % (self.__module__, self.__class__.__name__,
            self.array_types[self.array_type], repr(self.data()))
    
    def data(self):
    
        if self.array_type == 3:
            return "".join(self.array)
        else:
            return self.array
    
    def encoded(self):
    
        """Returns the contents of the array in the form they would take in the
        module area on a big-endian system."""
        
        data = ""
        
        for item in self.array:
        
            if self.array_type == 1:
                data += pack(">B", item)
            elif self.array_type == 2:
                data += pack(">i", item)
            elif self.array_type == 3:
                data += item
            elif self.array_type == 4:
                data += pack(">d", item)
            elif self.array_type == 8:
                data += pack(">q", item)
        
        return data


class Link:

    def __init__(self, f):
    
        self.pc = read_OP(f)
        self.desc_number = read_OP(f)
        self.sig = read_W(f)       # unsigned for hashes
        self.name = read_C(f)


class LDT:

    def __init__(self, f):
    
        self.sig = _read(f, ">I")   # unsigned for hashes
        self.name = read_C(f)
