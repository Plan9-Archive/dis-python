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
                  read_W, \
                  _write, write_B, write_C, write_OP, write_F, write_L, \
                  write_P, write_W

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
        
        # Read the other sections.
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
            self.types.append(Type().read(f))
            i += 1
    
    def read_data(self, f):
    
        # Use a dictionary to map pointers in the module's data area to items.
        self.data = {}
        
        # Maintain a list of individual data items for easy inspection.
        self.data_items = []
        
        # Use a list as a load address stack with an initial base address of 0.
        addresses = []
        base = 0
        type_ = None
        
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
                #print "Array", offset
            
            elif array_type == 6:
                # Set array index
                index = _read(f, ">I")
                # Store the current base first.
                addresses.append(base)
                #print "Set", base, offset, index
                base = offset + index
            
            elif array_type == 7:
                # Restore load address
                base = addresses.pop()
                type_ = None
                #print "Restore", base, offset
            
            else:
                #print "Data", offset
                address = base + offset
                item = Data(base, offset, array_type, type_)
                item.read(f, count)
                self.data_items.append(item)
                if address in self.data:
                    print "Overwriting existing data item at %x." % address
                self.data[address] = item
    
    def read_link(self, f):
    
        self.link = []
        i = 0
        
        while i < self.link_size:
            self.link.append(Link().read(f))
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
            
            sequence = []
            
            i = 0
            while i < value:
            
                sequence.append(LDT(f))
                i += 1
            
            self.ldt.append(sequence)
    
    def write(self, f):
    
        # Write the header.
        self.code_size = len(self.code)
        self.type_size = len(self.types)
        self.link_size = len(self.link)
        
        # Only unsigned files are currently supported.
        write_OP(f, XMAGIC)
        
        self.runtime_flag.write(f)
        write_OP(f, self.stack_extent)
        write_OP(f, self.code_size)
        write_OP(f, self.data_size)
        write_OP(f, self.type_size)
        write_OP(f, self.link_size)
        write_OP(f, self.entry_pc)
        write_OP(f, self.entry_type)
        
        # Write the other sections.
        self.write_code(f)
        self.write_types(f)
        self.write_data(f)
        
        write_C(f, self.module_name)
        
        self.write_link(f)
        
        if self.runtime_flag.contains(RuntimeFlag.HASLDT):
            self.write_ldt(f)
        
        write_C(f, self.path)
    
    def write_code(self, f):
    
        for ins in self.code:
            ins.write(f)
    
    def write_types(self, f):
    
        for type_ in self.types:
            type_.write(f)
    
    def write_data(self, f):
    
        # Sort the dictionary items by address.
        items = self.data.items()
        items.sort()
        
        addresses = []
        base = 0
        
        for address, item in items:
        
            if item.base != base:
            
                # Array
                write_B(f, 0x51)                # use count=1 to save a word
                write_OP(f, item.base - base)   # offset
                _write(f, ">I", self.types.index(item.type_))
                _write(f, ">I", len(item.data))
                
                # Set array address
                write_B(f, 0x61)                # use count=1 to save a word
                write_OP(f, item.base - base)   # offset
                _write(f, ">I", 0)              # index
            
            item.write(f)
            
            if item.base != base:
            
                # Restore load address
                write_B(f, 0x71)                # use count=1 to save a word
                write_OP(f, 0)                  # offset
                base = addresses.pop()
        
        write_OP(f, 0)
    
    def write_link(self, f):
    
        for link in self.link:
            link.write(f)
    
    def write_ldt(self, f):
    
        write_OP(f, self.initialised_globals)
        
        for sequence in self.ldt:
        
            write_OP(f, len(sequence))
            
            for ldt in sequence:
                ldt.write(f)
        
        write_OP(f, 0)
    
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
    
    def write(self, f):
        write_OP(f, self.value)


class Type:

    def __init__(self, desc_number = 0, size = 0, number_ptrs = 0, array = ""):
    
        self.desc_number = desc_number
        self.size = size
        self.number_ptrs = number_ptrs
        self.array = array
    
    def read(self, f):
    
        self.desc_number = read_OP(f)
        self.size = read_OP(f)
        self.number_ptrs = read_OP(f)
        self.array = f.read(self.number_ptrs)
        
        return self
    
    def __repr__(self):
    
        return "Type(desc=%i, size=%i, ptrs=%i)" % (self.desc_number,
            self.size, self.number_ptrs)
    
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
    
    def write(self, f):
    
        write_OP(f, self.desc_number)
        write_OP(f, self.size)
        write_OP(f, self.number_ptrs)
        f.write(self.array)


class Data:

    array_types = ["Invalid", "8-bit byte", "32-bit word",
                   "UTF-8 encoded string", "64-bit float", "Array",
                   "Set array address", "Restore load address"]
    
    def __init__(self, base, offset, array_type, type_ = None, array = None):
    
        self.base = base
        self.offset = offset
        self.array_type = array_type
        self.type_ = type_
        if not array:
            self.array = []
        else:
            self.array = array
    
    def read(self, f, count):
    
        base = 0
        i = 0
        while i < count:
        
            if self.array_type == 1:
                # 8-bit byte
                self.array.append(read_B(f))
            elif self.array_type == 2:
                # 32-bit word
                self.array.append(read_W(f))
            elif self.array_type == 3:
                # UTF-8 encoded string (each item is a character)
                self.array.append(f.read(1))
            elif self.array_type == 4:
                # 64-bit float
                self.array.append(read_F(f))
            elif self.array_type == 8:
                # 64-bit integer
                self.array.append(read_L(f))
            
            i += 1
    
    def __repr__(self):
    
        if self.type_:
            return "Data(base=%i offset=%i raw='%s' type=%s data=%s>" % (
                self.base, self.offset, self.array_types[self.array_type],
                self.type_, repr(self.data()))
        else:
            return "Data(base=%i offset=%i raw='%s' data=%s>" % (
                self.base, self.offset, self.array_types[self.array_type],
                repr(self.data()))
    
    def data(self):
    
        if self.array_type == 3:
            return "".join(self.array)
        else:
            return self.array
    
    def encoded(self):
    
        """Returns the contents of the array in the form they would take if
        serialised on a big-endian system."""
        
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
    
    def write(self, f):
    
        code = self.array_type << 4
        count = len(self.array)
        
        if count < 16:
            code |= count
        
        write_B(f, code)
        
        if count >= 16:
            write_OP(f, count)
        
        write_OP(f, self.offset)
        
        for item in self.array:
        
            if self.array_type == 1:
                write_B(f, item)
            elif self.array_type == 2:
                write_W(f, item)
            elif self.array_type == 3:
                f.write(item)
            elif self.array_type == 4:
                write_F(f, item)
            elif self.array_type == 8:
                write_L(f, item)


class Link:

    def __init__(self, pc = 0, desc_number = 0, sig = 0, name = ""):
    
        self.pc = pc
        self.desc_number = desc_number
        self.sig = sig
        self.name = name
    
    def read(self, f):
    
        self.pc = read_OP(f)
        self.desc_number = read_OP(f)
        self.sig = read_W(f)       # unsigned for hashes
        self.name = read_C(f)
    
    def __repr__(self):
    
        return "Link(pc=%s, desc=%i, sig=%s, name='%s')" % (
            hex(self.pc), self.desc_number, hex(self.sig), self.name)
    
    def write(self, f):
    
        write_OP(f, self.pc)
        write_OP(f, self.desc_number)
        write_W(f, self.sig)
        write_C(f, self.name)


class LDT:

    def __init__(self, sig = 0, name = ""):
    
        self.sig = sig
        self.name = name
    
    def read(self, f):
    
        self.sig = _read(f, ">I")   # unsigned for hashes
        self.name = read_C(f)
    
    def __repr__(self):
    
        return "LDT(sig=0x%x, name='%s')" % (self.sig, self.name)
    
    def write(self, f):
    
        _write(f, ">I", self.sig)
        write_C(f, self.name)
