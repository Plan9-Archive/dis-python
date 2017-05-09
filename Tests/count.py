#!/usr/bin/env python

import sys

import dis
import opcodes
from opcodes import Imm, LOfp, LOmp, NoOp, SOfp, SOmp, SOSOfp, SOSOmp

if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    d = dis.Dis()
    d.runtime_flag = dis.RuntimeFlag(dis.RuntimeFlag.HASLDT)
    d.stack_extent = 560
    d.data_size = 16
    d.entry_pc = 0
    d.entry_type = 2    # refers to Type 2
    
    d.code = [
        opcodes.load(LOmp(0), Imm(0), LOfp(44)),
        opcodes.frame(Imm(1), LOfp(52)),
        opcodes.movp(LOmp(8), SOSOfp(52, 32)),
        opcodes.lea(LOfp(48), SOSOfp(52, 16)),
        opcodes.mcall(LOfp(52), Imm(0), LOfp(44)),
        opcodes.movw(Imm(0), LOfp(40)),
        opcodes.blew(Imm(0x14), SOfp(40), Imm(0xe)),
        opcodes.frame(Imm(1), LOfp(48)),
        opcodes.movp(LOmp(4), SOSOfp(48, 32)),
        opcodes.movw(LOfp(40), SOSOfp(48, 36)),
        opcodes.lea(LOfp(52), SOSOfp(48, 16)),
        opcodes.mcall(LOfp(48), Imm(0), LOfp(44)),
        opcodes.addw(Imm(1), NoOp(), LOfp(40)),
        opcodes.jmp(Imm(6)),
        opcodes.ret()
        ]
    
    d.types = [
        dis.Type(0, 16, 1, "\xf0"),
        dis.Type(1, 40, 2, "\x00\x80"),
        dis.Type(2, 56, 2, "\x00\xd0")  # stack frame type, entry type
        ]
    
    d.data = {
        #       code size
        0: dis.Data(0, 0, 0x03, array = "$Sys"),
        4: dis.Data(0, 4, 0x03, array = "%d\n"),
        8: dis.Data(0, 8, 0x03, array = "Counting...\n"),
        }
    
    d.module_name = "count"
    d.link = [dis.Link(0, 2, 0x4244b354, "init")]   # refers to Type 2
    d.initialised_globals = 1
    d.ldt = [[dis.LDT(0xac849033, "print")]]
    d.path = sys.argv[0]
    
    d.write(open(sys.argv[1], "w"))
    
    sys.exit()
