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

from utils import read_B, read_OP

# Define string representations of the opcodes.

instruction_names = [
    "nop", "alt", "nbalt", "goto", "call", "frame", "spawn", "runt",
    "load", "mcall", "mspawn", "mframe", "ret", "jmp", "case", "exit",
    "new", "newa", "newcb", "newcw", "newcf", "newcp", "newcm", "newcmp",
    "send", "recv", "consb", "consw", "consp", "consf", "consm", "consmp",
    "headb", "headw", "headp", "headf", "headm", "headmp", "tail", "lea",
    "indx", "movp", "movm", "movmp", "movb", "movw", "movf", "cvtbw",
    "cvtwb", "cvtfw", "cvtwf", "cvtca", "cvtac", "cvtwc", "cvtcw", "cvtfc",
    "cvtcf", "addb", "addw", "addf", "subb", "subw", "subf", "mulb",
    "mulw", "mulf", "divb", "divw", "divf", "modw", "modb", "andb",
    "andw", "orb", "orw", "xorb", "xorw", "shlb", "shlw", "shrb",
    "shrw", "insc", "indc", "addc", "lenc", "lena", "lenl", "beqb",
    "bneb", "bltb", "bleb", "bgtb", "bgeb", "beqw", "bnew", "bltw",
    "blew", "bgtw", "bgew", "beqf", "bnef", "bltf", "blef", "bgtf",
    "bgef", "beqc", "bnec", "bltc", "blec", "bgtc", "bgec", "slicea",
    "slicela", "slicec", "indw", "indf", "indb", "negf", "movl", "addl",
    "subl", "divl", "modl", "mull", "andl", "orl", "xorl", "shll",
    "shrl", "bnel", "bltl", "blel", "bgtl", "bgel", "beql", "cvtlf",
    "cvtfl", "cvtlw", "cvtwl", "cvtlc", "cvtcl", "headl", "consl", "newcl",
    "casec", "indl", "movpc", "tcmp", "mnewz", "cvtrf", "cvtfr", "cvtws",
    "cvtsw", "lsrw", "lsrl", "eclr", "newz", "newaz", "raise", "casel",
    "mulx", "divx", "cvtxx", "mulx0", "divx0", "cvtxx0", "mulx1", "divx1",
    "cvtxx1", "cvtfx", "cvtxf", "expw", "expl", "expf", "self"
    ]


class Instruction:

    def read(self, f):
    
        self.opcode = read_B(f)
        self.address_mode = read_B(f)
        
        middle = self.address_mode & 0xc0
        self.middle, self.middle_type = self.read_middle_operand(middle, f)
        
        source = (self.address_mode & 0x38) >> 3
        self.source, self.source_type = self.read_operand(source, f)
        
        destination = self.address_mode & 0x07
        self.destination, self.destination_type = self.read_operand(destination, f)
        
        return self
    
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
            name = instruction_names[self.opcode]
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


# Define the instructions and their opcode values.

class nop(Instruction):

    opcode = 0x00

class alt(Instruction):

    opcode = 0x01

class nbalt(Instruction):

    opcode = 0x02

class goto(Instruction):

    opcode = 0x03

class call(Instruction):

    opcode = 0x04

class frame(Instruction):

    opcode = 0x05

class spawn(Instruction):

    opcode = 0x06

class runt(Instruction):

    opcode = 0x07

class load(Instruction):

    opcode = 0x08

class mcall(Instruction):

    opcode = 0x09

class mspawn(Instruction):

    opcode = 0x0a

class mframe(Instruction):

    opcode = 0x0b

class ret(Instruction):

    opcode = 0x0c

class jmp(Instruction):

    opcode = 0x0d

class case(Instruction):

    opcode = 0x0e

class exit(Instruction):

    opcode = 0x0f

class new(Instruction):

    opcode = 0x10

class newa(Instruction):

    opcode = 0x11

class newcb(Instruction):

    opcode = 0x12

class newcw(Instruction):

    opcode = 0x13

class newcf(Instruction):

    opcode = 0x14

class newcp(Instruction):

    opcode = 0x15

class newcm(Instruction):

    opcode = 0x16

class newcmp(Instruction):

    opcode = 0x17

class send(Instruction):

    opcode = 0x18

class recv(Instruction):

    opcode = 0x19

class consb(Instruction):

    opcode = 0x1a

class consw(Instruction):

    opcode = 0x1b

class consp(Instruction):

    opcode = 0x1c

class consf(Instruction):

    opcode = 0x1d

class consm(Instruction):

    opcode = 0x1e

class consmp(Instruction):

    opcode = 0x1f

class headb(Instruction):

    opcode = 0x20

class headw(Instruction):

    opcode = 0x21

class headp(Instruction):

    opcode = 0x22

class headf(Instruction):

    opcode = 0x23

class headm(Instruction):

    opcode = 0x24

class headmp(Instruction):

    opcode = 0x25

class tail(Instruction):

    opcode = 0x26

class lea(Instruction):

    opcode = 0x27

class indx(Instruction):

    opcode = 0x28

class movp(Instruction):

    opcode = 0x29

class movm(Instruction):

    opcode = 0x2a

class movmp(Instruction):

    opcode = 0x2b

class movb(Instruction):

    opcode = 0x2c

class movw(Instruction):

    opcode = 0x2d

class movf(Instruction):

    opcode = 0x2e

class cvtbw(Instruction):

    opcode = 0x2f

class cvtwb(Instruction):

    opcode = 0x30

class cvtfw(Instruction):

    opcode = 0x31

class cvtwf(Instruction):

    opcode = 0x32

class cvtca(Instruction):

    opcode = 0x33

class cvtac(Instruction):

    opcode = 0x34

class cvtwc(Instruction):

    opcode = 0x35

class cvtcw(Instruction):

    opcode = 0x36

class cvtfc(Instruction):

    opcode = 0x37

class cvtcf(Instruction):

    opcode = 0x38

class addb(Instruction):

    opcode = 0x39

class addw(Instruction):

    opcode = 0x3a

class addf(Instruction):

    opcode = 0x3b

class subb(Instruction):

    opcode = 0x3c

class subw(Instruction):

    opcode = 0x3d

class subf(Instruction):

    opcode = 0x3e

class mulb(Instruction):

    opcode = 0x3f

class mulw(Instruction):

    opcode = 0x40

class mulf(Instruction):

    opcode = 0x41

class divb(Instruction):

    opcode = 0x42

class divw(Instruction):

    opcode = 0x43

class divf(Instruction):

    opcode = 0x44

class modw(Instruction):

    opcode = 0x45

class modb(Instruction):

    opcode = 0x46

class andb(Instruction):

    opcode = 0x47

class andw(Instruction):

    opcode = 0x48

class orb(Instruction):

    opcode = 0x49

class orw(Instruction):

    opcode = 0x4a

class xorb(Instruction):

    opcode = 0x4b

class xorw(Instruction):

    opcode = 0x4c

class shlb(Instruction):

    opcode = 0x4d

class shlw(Instruction):

    opcode = 0x4e

class shrb(Instruction):

    opcode = 0x4f

class shrw(Instruction):

    opcode = 0x50

class insc(Instruction):

    opcode = 0x51

class indc(Instruction):

    opcode = 0x52

class addc(Instruction):

    opcode = 0x53

class lenc(Instruction):

    opcode = 0x54

class lena(Instruction):

    opcode = 0x55

class lenl(Instruction):

    opcode = 0x56

class beqb(Instruction):

    opcode = 0x57

class bneb(Instruction):

    opcode = 0x58

class bltb(Instruction):

    opcode = 0x59

class bleb(Instruction):

    opcode = 0x5a

class bgtb(Instruction):

    opcode = 0x5b

class bgeb(Instruction):

    opcode = 0x5c

class beqw(Instruction):

    opcode = 0x5d

class bnew(Instruction):

    opcode = 0x5e

class bltw(Instruction):

    opcode = 0x5f

class blew(Instruction):

    opcode = 0x60

class bgtw(Instruction):

    opcode = 0x61

class bgew(Instruction):

    opcode = 0x62

class beqf(Instruction):

    opcode = 0x63

class bnef(Instruction):

    opcode = 0x64

class bltf(Instruction):

    opcode = 0x65

class blef(Instruction):

    opcode = 0x66

class bgtf(Instruction):

    opcode = 0x67

class bgef(Instruction):

    opcode = 0x68

class beqc(Instruction):

    opcode = 0x69

class bnec(Instruction):

    opcode = 0x6a

class bltc(Instruction):

    opcode = 0x6b

class blec(Instruction):

    opcode = 0x6c

class bgtc(Instruction):

    opcode = 0x6d

class bgec(Instruction):

    opcode = 0x6e

class slicea(Instruction):

    opcode = 0x6f

class slicela(Instruction):

    opcod = 0x70

class slicec(Instruction):

    opcode = 0x71

class indw(Instruction):

    opcode = 0x72

class indf(Instruction):

    opcode = 0x73

class indb(Instruction):

    opcode = 0x74

class negf(Instruction):

    opcode = 0x75

class movl(Instruction):

    opcode = 0x76

class addl(Instruction):

    opcode = 0x77

class subl(Instruction):

    opcode = 0x78

class divl(Instruction):

    opcode = 0x79

class modl(Instruction):

    opcode = 0x7a

class mull(Instruction):

    opcode = 0x7b

class andl(Instruction):

    opcode = 0x7c

class orl(Instruction):

    opcode = 0x7d

class xorl(Instruction):

    opcode = 0x7e

class shll(Instruction):

    opcode = 0x7f

class shrl(Instruction):

    opcode = 0x80

class bnel(Instruction):

    opcode = 0x81

class bltl(Instruction):

    opcode = 0x82

class blel(Instruction):

    opcode = 0x83

class bgtl(Instruction):

    opcode = 0x84

class bgel(Instruction):

    opcode = 0x85

class beql(Instruction):

    opcode = 0x86

class cvtlf(Instruction):

    opcode = 0x87

class cvtfl(Instruction):

    opcode = 0x88

class cvtlw(Instruction):

    opcode = 0x89

class cvtwl(Instruction):

    opcode = 0x8a

class cvtlc(Instruction):

    opcode = 0x8b

class cvtcl(Instruction):

    opcode = 0x8c

class headl(Instruction):

    opcode = 0x8d

class consl(Instruction):

    opcode = 0x8e

class newcl(Instruction):

    opcode = 0x8f

class casec(Instruction):

    opcode = 0x90

class indl(Instruction):

    opcode = 0x91

class movpc(Instruction):

    opcode = 0x92

class tcmp(Instruction):

    opcode = 0x93

class mnewz(Instruction):

    opcode = 0x94

class cvtrf(Instruction):

    opcode = 0x95

class cvtfr(Instruction):

    opcode = 0x96

class cvtws(Instruction):

    opcode = 0x97

class cvtsw(Instruction):

    opcode = 0x98

class lsrw(Instruction):

    opcode = 0x99

class lsrl(Instruction):

    opcode = 0x9a

class eclr(Instruction):

    opcode = 0x9b

class newz(Instruction):

    opcode = 0x9c

class newaz(Instruction):

    opcode = 0x9d

class raise_(Instruction):

    opcode = 0x9e

class casel(Instruction):

    opcode = 0x9f

class mulx(Instruction):

    opcode = 0xa0

class divx(Instruction):

    opcode = 0xa1

class cvtxx(Instruction):

    opcode = 0xa2

class mulx0(Instruction):

    opcode = 0xa3

class divx0(Instruction):

    opcode = 0xa4

class cvtxx0(Instruction):

    opcode = 0xa5

class mulx1(Instruction):

    opcode = 0xa6

class divx1(Instruction):

    opcode = 0xa7

class cvtxx1(Instruction):

    opcode = 0xa8

class cvtfx(Instruction):

    opcode = 0xa9

class cvtxf(Instruction):

    opcode = 0xaa

class expw(Instruction):

    opcode = 0xab

class expl(Instruction):

    opcode = 0xac

class expf(Instruction):

    opcode = 0xad

class self(Instruction):

    opcode = 0xae
