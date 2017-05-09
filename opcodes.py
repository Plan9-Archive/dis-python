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

# See http://inferno-os.org/inferno/papers/dis.html or
#     http://doc.cat-v.org/inferno/4th_edition/dis_VM_specification
# for information.

from utils import read_B, read_OP, write_B, write_OP

class Instruction:

    def __init__(self):
    
        self.source = NoOperand()
        self.middle = NoOperand()
        self.destination = NoOperand()
        self.set_address_mode()
    
    def read(self, f):
    
        opcode = read_B(f)
        class_ = instructions[opcode]
        
        address_mode = read_B(f)
        
        middle = address_mode & 0xc0
        middle = self.read_middle_operand(middle, f)
        
        source = (address_mode & 0x38) >> 3
        source = self.read_operand(source, f)
        
        destination = address_mode & 0x07
        destination = self.read_operand(destination, f)
        
        if issubclass(class_, Src):
            return class_(source)
        elif issubclass(class_, Src_Src):
            return class_(source, middle)
        elif issubclass(class_, Src_Dst):
            return class_(source, destination)
        elif issubclass(class_, Src_Src_Dst):
            return class_(source, middle, destination)
        elif issubclass(class_, Src_Src_Src):
            return class_(source, middle, destination)
        elif issubclass(class_, Dst):
            return class_(destination)
        else:
            return class_()
    
    def set_address_mode(self):
    
        self.address_mode = self.middle.middle_address_mode | \
                            (self.source.address_mode << 3) | \
                            self.destination.address_mode
    
    def read_operand(self, operand, f):
    
        # Since we shift the address flags for the source operand, we can
        # check both source and destination operands using the same values.
        
        if operand == 0x00:
            operand = LongOffsetMP(read_OP(f), "LO(MP)")
        elif operand == 0x01:
            operand = LongOffsetFP(read_OP(f), "LO(FP)")
        elif operand == 0x02:
            operand = Immediate(read_OP(f), "$OP")
        
        # No operand for 0x03.
        
        elif operand == 0x04:
            operand = DoubleShortOffsetMP((read_OP(f), read_OP(f)), "SO(SO(MP))")
        elif operand == 0x05:
            operand = DoubleShortOffsetFP((read_OP(f), read_OP(f)), "SO(SO(FP))")
        else:
            operand = NoOperand()
        
        return operand
    
    def read_middle_operand(self, operand, f):
    
        # The middle operand bits are not shifted.
        
        if operand == 0x40:
            operand = Immediate(read_OP(f), "$SI")
        elif operand == 0x80:
            operand = ShortOffsetFP(read_OP(f), "SO(FP)")
        elif operand == 0xc0:
            operand = ShortOffsetMP(read_OP(f), "SO(MP)")
        else:
            operand = NoOperand()
        
        return operand
    
    def write(self, f):
    
        write_B(f, self.opcode)
        write_B(f, self.address_mode)
        
        self.middle.write(f)
        self.source.write(f)
        self.destination.write(f)
    
    def __repr__(self):
    
        try:
            name = self.__class__.__name__
        except IndexError:
            name = hex(self.opcode)
        
        operands = []
        
        for operand in self.source, self.middle, self.destination:
            s = str(operand)
            if s:
                operands.append(s)
        
        return name + " " + ", ".join(operands)


# Define the argument types.

class NoOperand:

    middle_address_mode = 0x00
    address_mode = 0x03
    
    def write(self, f):
        pass
    
    def __str__(self):
        return ""

class Operand:

    def __init__(self, value, annotation = None):
    
        self.value = value
        self.annotation = annotation
    
    def __str__(self):
        return self.str_pattern % self.value
    
    def write(self, f):
        write_OP(f, self.value)

class Immediate(Operand):
    str_pattern = "$%x"
    middle_address_mode = 0x40
    address_mode = 0x02

class LongOffset(Operand):
    pass

class LongOffsetMP(LongOffset):
    str_pattern = "%i(mp)"
    address_mode = 0x00

class LongOffsetFP(LongOffset):
    str_pattern = "%i(fp)"
    address_mode = 0x01

class ShortOffset(Operand):
    pass

class ShortOffsetMP(ShortOffset):
    str_pattern = "%i(mp)"
    middle_address_mode = 0xc0

class ShortOffsetFP(ShortOffset):
    str_pattern = "%i(fp)"
    middle_address_mode = 0x80

class DoubleShortOffset(Operand):

    def write(self, f):
        write_OP(f, self.value[0] & 0xffff)
        write_OP(f, self.value[1] & 0xffff)

class DoubleShortOffsetMP(DoubleShortOffset):
    str_pattern = "%i(%i(mp))"
    address_mode = 0x04

class DoubleShortOffsetFP(DoubleShortOffset):
    str_pattern = "%i(%i(fp))"
    address_mode = 0x05


# Define the instructions and their opcode values.

class Src(Instruction):
    
    def __init__(self, src):
    
        self.source = src
        self.middle = NoOperand()
        self.destination = NoOperand()
        self.set_address_mode()

class Src_Dst(Instruction):
    
    def __init__(self, src, dst):
    
        self.source = src
        self.middle = NoOperand()
        self.destination = dst
        self.set_address_mode()

class Src_Src(Instruction):
    
    def __init__(self, src1, src2):
    
        self.source = src1
        self.middle = src2
        self.destination = NoOperand()
        self.set_address_mode()

class Src_Src_Dst(Instruction):

    def __init__(self, src1, src2, dst):
    
        self.source = src1
        self.middle = src2
        self.destination = dst
        self.set_address_mode()

class Src_Src_Src(Instruction):

    def __init__(self, src1, src2, src3):
    
        self.source = src1
        self.middle = src2
        self.destination = src3
        self.set_address_mode()

class Dst(Instruction):
    
    def __init__(self, dst):
    
        self.source = NoOperand()
        self.middle = NoOperand()
        self.destination = dst
        self.set_address_mode()

# Groups of instructions
class addx(Src_Src_Dst):  pass
class andx(Src_Src_Dst):  pass
class beqx(Src_Src_Dst):  pass
class bgex(Src_Src_Dst):  pass
class bgtx(Src_Src_Dst):  pass
class blex(Src_Src_Dst):  pass
class bltx(Src_Src_Dst):  pass
class bnex(Src_Src_Dst):  pass
class consx(Src_Dst):     pass
class divx_(Src_Src_Dst): pass
class headx(Src_Dst):     pass
class indx_(Src_Src_Dst): pass
class lsrx(Src_Src_Dst):  pass
class modx(Src_Src_Dst):  pass
class movx(Src_Dst):      pass
class mulx_(Src_Src_Dst): pass
class newcx(Dst):         pass
class orx(Src_Src_Dst):   pass
class shlx(Src_Src_Dst):  pass
class shrx(Src_Src_Dst):  pass
class subx(Src_Src_Dst):  pass
class xorx(Src_Src_Dst):  pass

# Individual definitions (marked with the file in libinterp with information)
class addb(addx):           opcode = 0x39
class addc(addx):           opcode = 0x53
class addf(addx):           opcode = 0x3b
class addl(addx):           opcode = 0x77
class addw(addx):           opcode = 0x3a
class alt(Src_Dst):         opcode = 0x01
class andb(andx):           opcode = 0x47
class andl(andx):           opcode = 0x7c
class andw(andx):           opcode = 0x48
class beqb(beqx):           opcode = 0x57
class beqc(beqx):           opcode = 0x69
class beqf(beqx):           opcode = 0x63
class beql(beqx):           opcode = 0x86
class beqw(beqx):           opcode = 0x5d
class bgeb(bgex):           opcode = 0x5c
class bgec(bgex):           opcode = 0x6e
class bgef(bgex):           opcode = 0x68
class bgel(bgex):           opcode = 0x85
class bgew(bgex):           opcode = 0x62
class bgtb(bgtx):           opcode = 0x5b
class bgtc(bgtx):           opcode = 0x6d
class bgtf(bgtx):           opcode = 0x67
class bgtl(bgtx):           opcode = 0x84
class bgtw(bgtx):           opcode = 0x61
class bleb(blex):           opcode = 0x5a
class blec(blex):           opcode = 0x6c
class blef(blex):           opcode = 0x66
class blel(blex):           opcode = 0x83
class blew(blex):           opcode = 0x60
class bltb(bltx):           opcode = 0x59
class bltc(bltx):           opcode = 0x6b
class bltf(bltx):           opcode = 0x65
class bltl(bltx):           opcode = 0x82
class bltw(bltx):           opcode = 0x5f
class bneb(bnex):           opcode = 0x58
class bnec(bnex):           opcode = 0x6a
class bnef(bnex):           opcode = 0x64
class bnel(bnex):           opcode = 0x81
class bnew(bnex):           opcode = 0x5e
class call(Src_Dst):        opcode = 0x04
class case(Src_Dst):        opcode = 0x0e
class casec(Src_Dst):       opcode = 0x90
class casel(Src_Dst):       opcode = 0x9f   ### check syntax
class consb(consx):         opcode = 0x1a
class consf(consx):         opcode = 0x1d
class consl(consx):         opcode = 0x8e
class consm(consx):         opcode = 0x1e
class consmp(consx):        opcode = 0x1f
class consp(consx):         opcode = 0x1c
class consw(consx):         opcode = 0x1b
class cvtac(Src_Dst):       opcode = 0x34
class cvtbw(Src_Dst):       opcode = 0x2f
class cvtca(Src_Dst):       opcode = 0x33
class cvtcf(Src_Dst):       opcode = 0x38
class cvtcl(Src_Dst):       opcode = 0x8c
class cvtcw(Src_Dst):       opcode = 0x36
class cvtfc(Src_Dst):       opcode = 0x37
class cvtfl(Src_Dst):       opcode = 0x88
class cvtfr(Src_Dst):       opcode = 0x96
class cvtfw(Src_Dst):       opcode = 0x31
class cvtfx(Src_Dst):       opcode = 0xa9
class cvtlc(Src_Dst):       opcode = 0x8b
class cvtlf(Src_Dst):       opcode = 0x87
class cvtlw(Src_Dst):       opcode = 0x89
class cvtrf(Src_Dst):       opcode = 0x95
class cvtsw(Src_Dst):       opcode = 0x98   # short to word (xec.c)
class cvtwb(Src_Dst):       opcode = 0x30   # word to byte (xec.c)
class cvtwc(Src_Dst):       opcode = 0x35   # word to char array (string.c)
class cvtwf(Src_Dst):       opcode = 0x32   # word to float (xec.c)
class cvtwl(Src_Dst):       opcode = 0x8a   # word to long (xec.c)
class cvtws(Src_Dst):       opcode = 0x97   # word to short (xec.c)
class cvtxf(Src_Src_Dst):   opcode = 0xaa   # word * float -> float (xec.c)
class cvtxx0(Src_Src_Dst):  opcode = 0xa5   ### word ? word -> word (xec.c)
class cvtxx1(Src_Src_Dst):  opcode = 0xa8   ### word ? word -> word (xec.c)
class cvtxx(Src_Src_Dst):   opcode = 0xa2   ### word ? word -> word (xec.c)
class divb(divx_):          opcode = 0x42
class divf(divx_):          opcode = 0x44
class divl(divx_):          opcode = 0x79
class divw(divx_):          opcode = 0x43
class divx0(divx_):         opcode = 0xa4   # (xec.c)
class divx1(divx_):         opcode = 0xa7   # (xec.c)
class divx(divx_):          opcode = 0xa1   # (xec.c)
class eclr(Instruction):    opcode = 0x9b   # unused
class exit(Instruction):    opcode = 0x0f
class expf(Src_Src_Dst):    opcode = 0xad   # word word -> float (xec.c)
class expl(Src_Src_Dst):    opcode = 0xac   # word long -> long (xec.c)
class expw(Src_Src_Dst):    opcode = 0xab   # word word -> word (xec.c)
class frame(Src_Dst):       opcode = 0x05   # not src1, src2 as in documentation
class goto(Src_Dst):        opcode = 0x03
class headb(headx):         opcode = 0x20
class headf(headx):         opcode = 0x23
class headl(headx):         opcode = 0x8d
class headm(headx):         opcode = 0x24
class headmp(headx):        opcode = 0x25
class headp(headx):         opcode = 0x22
class headw(headx):         opcode = 0x21
class indb(indx_):          opcode = 0x74
class indc(Src_Src_Dst):    opcode = 0x52
class indf(indx_):          opcode = 0x73
class indl(indx_):          opcode = 0x91
class indw(indx_):          opcode = 0x72
class indx(Src_Src_Dst):    opcode = 0x28
class insc(Src_Src_Dst):    opcode = 0x51
class jmp(Dst):             opcode = 0x0d
class lea(Src_Dst):         opcode = 0x27
class lena(Src_Dst):        opcode = 0x55
class lenc(Src_Dst):        opcode = 0x54
class lenl(Src_Dst):        opcode = 0x56
class load(Src_Src_Dst):    opcode = 0x08
class lsrl(lsrx):           opcode = 0x9a
class lsrw(lsrx):           opcode = 0x99
class mcall(Src_Src_Src):   opcode = 0x09
class mframe(Src_Src_Dst):  opcode = 0x0b
class mnewz(Src_Src_Dst):   opcode = 0x94
class modb(modx):           opcode = 0x46
class modl(modx):           opcode = 0x7a
class modw(modx):           opcode = 0x45
class movb(movx):           opcode = 0x2c
class movf(movx):           opcode = 0x2e
class movl(movx):           opcode = 0x76
class movm(Src_Src_Dst):    opcode = 0x2a
class movmp(Src_Src_Dst):   opcode = 0x2b
class movpc(Src_Dst):       opcode = 0x92
class movp(Src_Dst):        opcode = 0x29
class movw(movx):           opcode = 0x2d
class mspawn(Src_Src_Src):  opcode = 0x0a
class mulb(mulx_):          opcode = 0x3f
class mulf(mulx_):          opcode = 0x41
class mull(mulx_):          opcode = 0x7b
class mulw(mulx_):          opcode = 0x40
class mulx0(mulx_):         opcode = 0xa3   ### word * word -> word (xec.c)
class mulx1(mulx_):         opcode = 0xa6   ### word * word -> word (xec.c)
class mulx(mulx_):          opcode = 0xa0   ### word * word -> word (xec.c)
class nbalt(Src_Dst):       opcode = 0x02
class negf(Src_Dst):        opcode = 0x75
class new(Src_Dst):         opcode = 0x10
class newa(Src_Src_Dst):    opcode = 0x11
class newaz(Src_Src_Dst):   opcode = 0x9d
class newcb(newcx):         opcode = 0x12
class newcf(newcx):         opcode = 0x14
class newcl(newcx):         opcode = 0x8f
class newcm(newcx):         opcode = 0x16
class newcmp(newcx):        opcode = 0x17
class newcp(newcx):         opcode = 0x15
class newcw(newcx):         opcode = 0x13
class newz(Src_Dst):        opcode = 0x9c
class nop(Instruction):     opcode = 0x00
class orb(orx):             opcode = 0x49
class orl(orx):             opcode = 0x7d
class orw(orx):             opcode = 0x4a
class raise_(Src):          opcode = 0x9e   ### type (xec.c)
class recv(Src_Dst):        opcode = 0x19
class ret(Instruction):     opcode = 0x0c
class runt(Instruction):    opcode = 0x07   ### no operands (xec.c)
class self(Instruction):    opcode = 0xae   ### no operands? (xec.c)
class send(Src_Dst):        opcode = 0x18
class shlb(shlx):           opcode = 0x4d
class shll(shlx):           opcode = 0x7f
class shlw(shlx):           opcode = 0x4e
class shrb(shrx):           opcode = 0x4f
class shrl(shrx):           opcode = 0x80
class shrw(shrx):           opcode = 0x50
class slicea(Src_Src_Dst):  opcode = 0x6f
class slicec(Src_Src_Dst):  opcode = 0x71
class slicela(Src_Src_Dst): opcode = 0x70
class spawn(Src_Dst):       opcode = 0x06
class subb(subx):           opcode = 0x3c
class subf(subx):           opcode = 0x3e
class subl(subx):           opcode = 0x78
class subw(subx):           opcode = 0x3d
class tail(Src_Dst):        opcode = 0x26
class tcmp(Src_Dst):        opcode = 0x93
class xorb(xorx):           opcode = 0x4b
class xorl(xorx):           opcode = 0x7e
class xorw(xorx):           opcode = 0x4c

# Define a list to map opcodes to instruction classes.

instructions = [
    nop, alt, nbalt, goto, call, frame, spawn, runt,
    load, mcall, mspawn, mframe, ret, jmp, case, exit,
    new, newa, newcb, newcw, newcf, newcp, newcm, newcmp,
    send, recv, consb, consw, consp, consf, consm, consmp,
    headb, headw, headp, headf, headm, headmp, tail, lea,
    indx, movp, movm, movmp, movb, movw, movf, cvtbw,
    cvtwb, cvtfw, cvtwf, cvtca, cvtac, cvtwc, cvtcw, cvtfc,
    cvtcf, addb, addw, addf, subb, subw, subf, mulb,
    mulw, mulf, divb, divw, divf, modw, modb, andb,
    andw, orb, orw, xorb, xorw, shlb, shlw, shrb,
    shrw, insc, indc, addc, lenc, lena, lenl, beqb,
    bneb, bltb, bleb, bgtb, bgeb, beqw, bnew, bltw,
    blew, bgtw, bgew, beqf, bnef, bltf, blef, bgtf,
    bgef, beqc, bnec, bltc, blec, bgtc, bgec, slicea,
    slicela, slicec, indw, indf, indb, negf, movl, addl,
    subl, divl, modl, mull, andl, orl, xorl, shll,
    shrl, bnel, bltl, blel, bgtl, bgel, beql, cvtlf,
    cvtfl, cvtlw, cvtwl, cvtlc, cvtcl, headl, consl, newcl,
    casec, indl, movpc, tcmp, mnewz, cvtrf, cvtfr, cvtws,
    cvtsw, lsrw, lsrl, eclr, newz, newaz, raise_, casel,
    mulx, divx, cvtxx, mulx0, divx0, cvtxx0, mulx1, divx1,
    cvtxx1, cvtfx, cvtxf, expw, expl, expf, self
    ]
