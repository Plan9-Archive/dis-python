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

nop     = 0x00
alt     = 0x01
nbalt   = 0x02
goto    = 0x03
call    = 0x04
frame   = 0x05
spawn   = 0x06
runt    = 0x07
load    = 0x08
mcall   = 0x09
mspawn  = 0x0a
mframe  = 0x0b
ret     = 0x0c
jmp     = 0x0d
case    = 0x0e
exit    = 0x0f
new     = 0x10
newa    = 0x11
newcb   = 0x12
newcw   = 0x13
newcf   = 0x14
newcp   = 0x15
newcm   = 0x16
newcmp  = 0x17
send    = 0x18
recv    = 0x19
consb   = 0x1a
consw   = 0x1b
consp   = 0x1c
consf   = 0x1d
consm   = 0x1e
consmp  = 0x1f
headb   = 0x20
headw   = 0x21
headp   = 0x22
headf   = 0x23
headm   = 0x24
headmp  = 0x25
tail    = 0x26
lea     = 0x27
indx    = 0x28
movp    = 0x29
movm    = 0x2a
movmp   = 0x2b
movb    = 0x2c
movw    = 0x2d
movf    = 0x2e
cvtbw   = 0x2f
cvtwb   = 0x30
cvtfw   = 0x31
cvtwf   = 0x32
cvtca   = 0x33
cvtac   = 0x34
cvtwc   = 0x35
cvtcw   = 0x36
cvtfc   = 0x37
cvtcf   = 0x38
addb    = 0x39
addw    = 0x3a
addf    = 0x3b
subb    = 0x3c
subw    = 0x3d
subf    = 0x3e
mulb    = 0x3f
mulw    = 0x40
mulf    = 0x41
divb    = 0x42
divw    = 0x43
divf    = 0x44
modw    = 0x45
modb    = 0x46
andb    = 0x47
andw    = 0x48
orb     = 0x49
orw     = 0x4a
xorb    = 0x4b
xorw    = 0x4c
shlb    = 0x4d
shlw    = 0x4e
shrb    = 0x4f
shrw    = 0x50
insc    = 0x51
indc    = 0x52
addc    = 0x53
lenc    = 0x54
lena    = 0x55
lenl    = 0x56
beqb    = 0x57
bneb    = 0x58
bltb    = 0x59
bleb    = 0x5a
bgtb    = 0x5b
bgeb    = 0x5c
beqw    = 0x5d
bnew    = 0x5e
bltw    = 0x5f
blew    = 0x60
bgtw    = 0x61
bgew    = 0x62
beqf    = 0x63
bnef    = 0x64
bltf    = 0x65
blef    = 0x66
bgtf    = 0x67
bgef    = 0x68
beqc    = 0x69
bnec    = 0x6a
bltc    = 0x6b
blec    = 0x6c
bgtc    = 0x6d
bgec    = 0x6e
slicea  = 0x6f
slicela = 0x70
slicec  = 0x71
indw    = 0x72
indf    = 0x73
indb    = 0x74
negf    = 0x75
movl    = 0x76
addl    = 0x77
subl    = 0x78
divl    = 0x79
modl    = 0x7a
mull    = 0x7b
andl    = 0x7c
orl     = 0x7d
xorl    = 0x7e
shll    = 0x7f
shrl    = 0x80
bnel    = 0x81
bltl    = 0x82
blel    = 0x83
bgtl    = 0x84
bgel    = 0x85
beql    = 0x86
cvtlf   = 0x87
cvtfl   = 0x88
cvtlw   = 0x89
cvtwl   = 0x8a
cvtlc   = 0x8b
cvtcl   = 0x8c
headl   = 0x8d
consl   = 0x8e
newcl   = 0x8f
casec   = 0x90
indl    = 0x91
movpc   = 0x92
tcmp    = 0x93
mnewz   = 0x94
cvtrf   = 0x95
cvtfr   = 0x96
cvtws   = 0x97
cvtsw   = 0x98
lsrw    = 0x99
lsrl    = 0x9a
eclr    = 0x9b
newz    = 0x9c
newaz   = 0x9d
raise_  = 0x9e
casel   = 0x9f
mulx    = 0xa0
divx    = 0xa1
cvtxx   = 0xa2
mulx0   = 0xa3
divx0   = 0xa4
cvtxx0  = 0xa5
mulx1   = 0xa6
divx1   = 0xa7
cvtxx1  = 0xa8
cvtfx   = 0xa9
cvtxf   = 0xaa
expw    = 0xab
expl    = 0xac
expf    = 0xad
self    = 0xae

names = [
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
