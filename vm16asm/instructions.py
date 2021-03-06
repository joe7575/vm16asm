#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# VM16 Assembler v1.0
# Copyright (C) 2019-2021 Joe <iauit@gmx.de>
#
# This file is part of VM16.

# VM16 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# VM16 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with VM16.  If not, see <https://www.gnu.org/licenses/>.

#  History:
#  1.0.0  01-Dec-2019  first draft
#  1.0.1  21-Nov-2020  Add setup
#  1.0.2  08-Dec-2020  Change syntax for sys instruction
#  1.0.3  28-Dec-2020  Add export for COM files
#  1.1.0  03-Jan-2021  Add 'bkr' opcode
#  1.2.0  05-Jan-2021  Change local/global label handling

VERSION = "1.2.0"


#
# OP-codes
#
Opcodes = [
    "nop:-:-", "brk:CNST:-", "sys:CNST:-", "res2:CNST:-",
    "jump:ADR:-", "call:ADR:-", "ret:-:-", "halt:-:-",
    "move:DST:SRC", "xchg:DST:DST", "inc:DST:-", "dec:DST:-",
    "add:DST:SRC", "sub:DST:SRC", "mul:DST:SRC", "div:DST:SRC",
    "and:DST:SRC", "or:DST:SRC", "xor:DST:SRC", "not:DST:-",
    "bnze:DST:ADR", "bze:DST:ADR", "bpos:DST:ADR", "bneg:DST:ADR",
    "in:DST:CNST", "out:CNST:SRC", "push:SRC:-", "pop:DST:-", 
    "swap:DST:-", "dbnz:DST:ADR", "mod:DST:SRC",
    "shl:DST:SRC", "shr:DST:SRC", "addc:DST:SRC", "mulc:DST:SRC",
    "skne:SRC:SRC", "skeq:SRC:SRC", "sklt:SRC:SRC", "skgt:SRC:SRC",
]

JumpInst = ["call", "jump", "bnze", "bze", "bpos", "bneg", "dbnz"]

#
# Operands
#
Operands = [
    "A", "B", "C", "D", "X", "Y", "PC", "SP",
    "[X]", "[Y]", "[X]+", "[Y]+", "#0", "#1", "-", "-", 
    "IMM", "IND", "REL", "[SP+n]",
]
RegOperands = Operands[0:-4]

#
# Operand Groups
#
REG = ["A", "B", "C", "D", "X", "Y", "PC", "SP"]
MEM = ["[X]", "[Y]", "[X]+", "[Y]+", "IND", "[SP+n]"]
ADR = ["IMM", "REL", "#0", "#1"]
CNST = ["#0", "#1", "IMM"]
DST = REG + MEM
SRC = DST + CNST 
NUM = ["NUM"]
