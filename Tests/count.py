#!/usr/bin/env python

import sys

import dis
import opcodes
from opcodes import Imm, LOfp, LOmp, NoOp, SOfp, SOmp, SOSOfp, SOSOmp
from utils import hash_signature

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
    
    # implement count;
    #
    # include "sys.m";
    # include "draw.m";
    #
    # count: module
    # {
    #     init: fn(ctxt: ref Draw->Context, args: list of string);
    # };
    #
    # init(ctxt: ref Draw->Context, args: list of string)
    # {
    #     sys := load Sys Sys->PATH;
    #     sys->print("Counting...\n");
    #     for (i := 0; i < 20; i++)
    #         sys->print("%d\n", i);
    # }
    
    d.code = [
    opcodes.load(LOmp(0), Imm(0), LOfp(44)),    # "$Sys", ldt[0] -> module
    
    opcodes.frame(Imm(1), LOfp(52)),            # types[1] -> new_frame1 (ptr)
    opcodes.movp(LOmp(8), SOSOfp(32, 52)),      # "Counting..." ->
    opcodes.lea(LOfp(48), SOSOfp(16, 52)),      # 
    opcodes.mcall(LOfp(52), Imm(0), LOfp(44)),  # new_frame1, ldt[0], module
    
    opcodes.movw(Imm(0), LOfp(40)),             # 0 -> i (int)
    opcodes.blew(Imm(0x14), SOfp(40), Imm(0xe)),# 0x6: if 20 <= i branch to 0xe
    
    opcodes.frame(Imm(1), LOfp(48)),            # types[1] -> new_frame2 (ptr)
    opcodes.movp(LOmp(4), SOSOfp(32, 48)),      # "%d\n" -> 
    opcodes.movw(LOfp(40), SOSOfp(36, 48)),
    opcodes.lea(LOfp(52), SOSOfp(16, 48)),      # new_frame1 ->
    opcodes.mcall(LOfp(48), Imm(0), LOfp(44)),  # new_frame2, ldt[0]
    
    opcodes.addw(Imm(1), NoOp(), LOfp(40)),     # 1 + [i] -> i
    opcodes.jmp(Imm(6)),                        # jump to 0x6
    opcodes.ret()                               # 0xe: return
    ]
    
    d.types = [
        dis.Type(0, 16, 1, "\xf0"),
        dis.Type(1, 40, 2, "\x00\x80"),
        # Type 2 is the stack frame type (see below), entry type (see above),
        # 56 bytes (14 words) in size:
        # pointer bitmap: 0 0 0 0 0 0 0 0 | 1 1 0 1 0 0 [0 0]
        dis.Type(2, 56, 2, "\x00\xd0")
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
    d.ldt = [[dis.LDT(hash_signature("f*(s)i"), "print")]]
    d.path = sys.argv[0]
    
    d.write(open(sys.argv[1], "w"))
    
    sys.exit()
