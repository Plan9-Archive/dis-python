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
    d.data_size = 8
    d.entry_pc = 0
    d.entry_type = 1
    
    """
    implement count;

    include "sys.m";
    include "draw.m";

    count: module
    {
        init: fn(ctxt: ref Draw->Context, args: list of string);
    };

    init(ctxt: ref Draw->Context, args: list of string)
    {
        sys := load Sys Sys->PATH;
        for (i := 0; i < 123; i++)
            ;
    }
    """
    
    d.code = [
    opcodes.load(LOmp(0), Imm(0), LOfp(48)),
    opcodes.movw(Imm(0), LOfp(40)),
    opcodes.blew(Imm(123), SOfp(40), Imm(5)),
    opcodes.addw(Imm(1), NoOp(), LOfp(40)),
    opcodes.jmp(Imm(2)),
    opcodes.ret()
    ]
    
    d.types = [
        dis.Type(0, 8, "\xc0"),
        dis.Type(1, 56, "\x00\xc8")
        ]
    
    d.data = {
        0: dis.Data(0, 0, 0x03, array = "$Sys"),
        }
    
    d.module_name = "count"
    d.link = [dis.Link(0, 1, 0x4244b354, "init")]
    d.initialised_globals = 1
    d.ldt = []
    d.path = sys.argv[0]
    
    d.write(open(sys.argv[1], "w"))
    
    sys.exit()
