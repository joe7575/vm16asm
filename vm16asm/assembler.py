#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# vm16asm - Macro Assembler for the VM16 CPU
# Copyright (C) 2019-2021 Joe <iauit@gmx.de>
#

# v16asm is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# v16asm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with v16asm.  If not, see <https://www.gnu.org/licenses/>.

import re
import sys
import os
import pprint
import struct
from .instructions import *
from copy import copy
from array import array

DEST_PATH = ""

reLABEL = re.compile(r"^([A-Za-z_][A-Za-z_0-9\.]+):")
reCONST = re.compile(r"#(\$?[0-9A-Fa-fx]+)$")
reADDR = re.compile(r"(\$?[0-9A-Fa-fx]+)$")
reREL  = re.compile(r"([\+\-])(\$?[0-9A-Fa-fx]+)$")
reSTACK = re.compile(r"\[SP\+(\$?[0-9A-Fa-fx]+)\]$")
reINCL =  re.compile(r'^\$include +"(.+?)"')
reMACRO_DEF = re.compile(r'^\$macro +([A-Za-z_][A-Za-z_0-9\.]+) *([0-9]?)$')
reMACRO =  re.compile(r'^([A-Za-z_][A-Za-z_0-9\.]+) *(.*)$')
reEQUALS = re.compile(r"^([A-Za-z_][A-Za-z_0-9\.]+) *= *(\S+)")
rePARAM = re.compile(r'^\-[cls]{1,3}')

# Token tuple indexes
FILENAME = 0
LINENUM = 1
LINESTR = 2
LINETYPE = 3
ADDRESS = 4
INSTRSIZE = 5
INSTRWORDS = 6
OPCODES = 7

# Segment types
CODETYPE = 0
WTEXTTYPE = 1
BTEXTTYPE = 2
DATATYPE = 3
COMMENT = 4

def outp(s, new=False):
    if "--srv" in sys.argv:
        outfile = DEST_PATH + "pipe.sys"
        if new:
            open(outfile, "w").write(s+"\n")
        else:
            open(outfile, "a").write(s+"\n")
    print(s)

def startswith(s, keyword):
    return s.split(" ")[0] == keyword
    
def parameter():
    for item in sys.argv:
        if rePARAM.match(item):
            if "c" in item: sys.argv.append("--com") 
            if "l" in item: sys.argv.append("--lst") 
            if "s" in item: sys.argv.append("--sym") 
    
class Tokenizer(object):
    """
    Read asm-file and generate one large list of tokens (filename, lineno, line).
    This include:
    - import $include files
    - expand macros
    """
    def __init__(self):
        self.lPathList = []
        self.dMacros = {}
        
    def error(self, filename, lineno, err):
        outp("Error in file %s(%u):\n%s" % (filename, lineno, err))
        sys.exit(-1)
    
    def find_file(self, path, filename):
        # Server mode needs special handling due to the lack of dirs 
        # and the UID as file name prefix.
        if "--srv" in sys.argv:
            filename = path + os.path.basename(filename)
            path, basename = filename.rsplit("_", 1)
            path = path + "_"
            namespace = os.path.splitext(basename)[0]
            if os.path.exists(filename):
                return filename, path, basename, namespace
            outp("Error: File '%s' missing" % basename)
        else:
            filename = os.path.realpath(os.path.join(path, filename))
            path = os.path.dirname(filename)
            basename = os.path.basename(filename)
            namespace = os.path.splitext(basename)[0]
            if os.path.exists(filename):
                return filename, path, basename, namespace
            outp("Error: File '%s' missing" % filename)
        sys.exit(-1)
    
    def expand_macro(self, match, filename, lineno, line):
        name = match.group(1)
        params = match.group(2).split()
        num_param = len(params)
        if name not in self.dMacros:
             self.error(filename, lineno, "Unknown macro")
        if num_param != self.dMacros[name][0]:
             self.error(filename, lineno, "Invalid number of parameters")
        tokens = []
        for item in self.dMacros[name][1:]:
            if num_param > 0: item = item.replace("%1", params[0])
            if num_param > 1: item = item.replace("%2", params[1])
            if num_param > 2: item = item.replace("%3", params[2])
            if num_param > 3: item = item.replace("%4", params[3])
            if num_param > 4: item = item.replace("%5", params[4])
            if num_param > 5: item = item.replace("%6", params[5])
            if num_param > 6: item = item.replace("%7", params[6])
            if num_param > 7: item = item.replace("%8", params[7])
            if num_param > 8: item = item.replace("%9", params[8])
            tokens.append((filename, lineno, item))
        return tokens  
        
    def load_file(self, path, filename, lNameSpaces=[]):
        """
        Read ASM file with all include files.
        Function is called recursively to handle includes.
        The file name is used as name space for all labels and aliases.
        Return a token list with (namespace, line-no, line-string) 
        """
        filename, path, basename, namespace = self.find_file(path, filename)
        macro_name = False
    
        lToken = []
    
        if namespace not in lNameSpaces:
            lNameSpaces.append(namespace)
            self.namespace = namespace
    
            lToken.append((basename, 0, ""))
            lToken.append((basename, 0, ";############ File: %s ############" % basename))
            lineno = 0
            try:
                lines = open(filename).readlines()
            except:
                self.error(basename, lineno, "Invalid file format")
            for idx, line in enumerate(lines):
                lineno += 1
                clean_line = line.strip()
                # include files
                m = reINCL.match(clean_line)
                if m:
                    fname = m.group(1)
                    outp(" - import %s..." % os.path.basename(fname))
                    t, _ = self.load_file(path, fname, lNameSpaces)
                    lToken.extend(t)
                    continue
                # end of macro definition
                if macro_name and startswith(clean_line, "$endmacro"):
                    macro_name = False
                # code of macro definition
                elif macro_name:
                    self.dMacros[macro_name].append(line)
                # start of macro definition
                elif startswith(clean_line, "$macro"):
                    m = reMACRO_DEF.match(clean_line)
                    if m:
                        macro_name = m.group(1)
                        num_param = int(m.group(2) or "0")
                        self.dMacros[macro_name] = [num_param]
                        lToken.append((basename, lineno, "; " + line))
                    else:
                        self.error(basename, lineno, "Invalid macro syntax")
                else:
                    # expand macro 
                    m = reMACRO.match(clean_line)
                    if m and m.group(1) in self.dMacros:
                        lToken.extend(self.expand_macro(m, basename, lineno, line))
                        continue
                    lToken.append((basename, lineno, line))
        return lToken, lNameSpaces

class AsmBase(object):
    def __init__(self, lNameSpaces):
        self.lNameSpaces = lNameSpaces

    def error(self, err):
        filename = self.token[FILENAME]
        lineno = self.token[LINENUM]
        outp("Error in file %s(%u):\n%s" % (filename, lineno, err))
        sys.exit(-1)
    
    def prepare_opcode_tables(self):
        self.dOpcodes = {}
        self.dOperands = {}
        for idx,s in enumerate(Opcodes):
            opc = s.split(":")[0] 
            self.dOpcodes[opc] = idx
        for idx,s in enumerate(RegOperands):
            self.dOperands[s] = idx

    def string(self, s):
        lOut =[]
        if s[0] == '"' and s[-1] == '"':
            s = s.replace("\\0", "\0")
            s = s.replace("\\n", "\n")
            s = s.replace('"', "")
            for c in s:
                lOut.append(ord(c))
        return lOut
    
    def byte_string(self, s):
        def word_val(s, idx):
            if s[idx] == "\0":
                return 0 
            elif idx + 1 == len(s):
                return ord(s[idx])
            elif s[idx+1] == "\0":
                return ord(s[idx])
            else:
                return (ord(s[idx]) << 8) + ord(s[idx+1])
    
        lOut =[]
        s = s.replace("\\0", "\0\0")
        s = s.replace("\\n", "\n")
        if s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
            for idx in range(0, len(s), 2):
                lOut.append(word_val(s, idx))
        return lOut
    
    def const_val(self, s):
        """
        10 bit const value like in 'sys #123' 
        """
        try:
            if s[0] == "#":
                if s[1] == "$":
                    return int(s[2:], base=16) % 1024
                return int(s[1:], base=10) % 1024
            else:
                self.error("Invalid oprnd in '%s'" % self.line)
        except:
            self.error("Invalid oprnd in '%s'" % self.line)
            
    def value(self, s):
        try:
            if s[0] == "$":
                return int(s[1:], base=16)
            elif s[0:2] == "0x":
                return int(s[2:], base=16)
            elif s[0] == "0":
                return int(s, base=8)
            return int(s, base=10)
        except:
            self.error("Invalid oprnd in '%s'" % self.line)

    def expand_ident(self, namespace, ident):
        """
        Expand an identifier like 'foo' to:
                                   foo.main
                         namespace.foo
        depending on foo is a valid namespace or not. 
        """
        pieces = ident.split(".")
        if len(pieces) == 1:
            if ident in self.lNameSpaces:
                return ident + ".start"
            else:
                return namespace + "." + ident
            ident
        elif len(pieces) == 2:
            if pieces[0] in self.lNameSpaces:
                return ident
        return None
    
    def add_aliase(self, left_val, right_val):
        left_val = self.expand_ident(self.namespace, left_val)
        if left_val:
            self.dAliases[left_val] = right_val
        else:
            self.error("Inv. left value in '%s'" % self.line)

    def add_symbol(self, label, addr):
        label2 = self.expand_ident(self.namespace, label)
        if label2:
            if label != "start" and label2 in self.dSymbols:
                self.error("Label '%s' used twice in\n'%s'" % (label, self.line))
            self.dSymbols[label2] = addr
        else:
            self.error("Inv. label value in '%s'" % self.line)
            
    def add_default_label(self, line, addr):
        words = line.split()
        if words[0] == ".code":
            label = self.namespace + ".start"
            if label not in self.dSymbols:
                self.dSymbols[label] = addr
            
    def get_symbol_addr(self, label):
        label2 = self.expand_ident(self.namespace, label)
        if label2 in self.dSymbols:
            return self.dSymbols[label2]
        if self.ispass2:
            self.error("Invalid oprnd in '%s'" % self.line)
        return 0
            
    def aliases(self, s):    
        namespace = os.path.splitext(self.token[FILENAME])[0]
        
        if s[0] == "#":
            ident = self.expand_ident(namespace, s[1:])
            if ident in self.dAliases:
                return "#" + self.dAliases[ident]
        else:
            ident = self.expand_ident(namespace, s)
            if ident in self.dAliases:
                return self.dAliases[ident]
        return s


class AsmPass1(AsmBase):
    """
    Work on the given token list:
    - feed aliases table
    - feed symbol table
    - determine instruction size (num words)
    - return the enriched token list (file-ref, line-no, line-string, line-type, 
                                      address, instr-size, instr-words)
    """
    def __init__(self, lNameSpaces):
        AsmBase.__init__(self, lNameSpaces)
        self.segment_type = CODETYPE
        self.addr = 0
        self.dSymbols = {}
        self.dAliases = {}
        self.prepare_opcode_tables()

    def directive(self, s):
        words = s.split()
        if words[0] == ".data":
            self.segment_type = DATATYPE
            return True
        elif words[0] == ".code":
            self.segment_type = CODETYPE
            return True
        elif words[0] == ".text":
            self.segment_type = WTEXTTYPE
            return True
        elif words[0] == ".ctext": # compressed
            self.segment_type = BTEXTTYPE
            return True
        elif words[0] == ".org" and len(words) > 1:
            self.addr = self.value(words[1])
            return True
        return False

    def tokenize(self, size, words):
        token = (self.token[FILENAME], self.token[LINENUM], self.token[LINESTR],
                 self.segment_type, self.addr, size, words)
        self.addr += size
        return token
       
    def comment(self):
        return (self.token[FILENAME], self.token[LINENUM], self.token[LINESTR],
                COMMENT, 0, 0, 0, [])

    def operand_size(self, s):
        if not s: return 0
        s = self.aliases(s)
        
        if s in ["#0", "#1", "#$0", "#$1"]: return 0
        if s[0] in ["#", "+", "-"]: return 1
        if s in self.dOperands: return 0
        return 1
    
    def operand_correction(self, words):
        # add the "immediate" sign to all jump instructions
        if words[0] in JumpInst:
            if len(words) == 3:
                if words[2][0] not in ["+", "-", "#"]:
                    words[2] = "#" + words[2]
            elif len(words) == 2:
                if words[1][0] not in ["+", "-", "#"]:
                    words[1] = "#" + words[1]
        return words
        
    def decode(self):
        list_get = lambda l, idx: l[idx] if len(l) > idx else None
            
        line = self.token[LINESTR]
        self.namespace = os.path.splitext(self.token[FILENAME])[0]
        line = line.split(";")[0].rstrip()
        self.line = line.strip() # for error messages
        line = line.replace(",", " ")
        line = line.replace("\t", "    ")
        line = line.strip()
        if line == "": 
            return self.comment()
        words = line.split()
        # assembler directive
        if self.directive(line):
            self.add_default_label(line, self.addr)
            return self.comment()
        # aliases
        m = reEQUALS.match(line)
        if m:
            self.add_aliase(m.group(1), m.group(2))
            return self.comment()
        # address label
        m = reLABEL.match(line)
        if m:
            self.add_symbol(m.group(1), self.addr)
            if len(words) == 1:
                return self.comment()
            words = words[1:]
            line = line.split(" ", 1)[1]
        # text segment
        if self.segment_type == WTEXTTYPE:
            s = self.string(line.strip())
            return self.tokenize(len(s), s)
        if self.segment_type == BTEXTTYPE:
            s = self.byte_string(line.strip())
            return self.tokenize(len(s), s)
        # data segment
        if self.segment_type == DATATYPE:
            l = []
            for s in words:
                l.append(self.value(s))
            return self.tokenize(len(l), l)
        # code segment
        if words[0] not in self.dOpcodes:
            self.error("Invalid syntax '%s'" % self.line)
        opcode = self.dOpcodes[words[0]]
        if len(words) == 2 and opcode < 4: # special handling
            size = 1
        else:
            words = self.operand_correction(words)
            size = 1 + self.operand_size(list_get(words, 1)) + self.operand_size(list_get(words, 2))
            if size > 2:
                self.error("Invalid syntax in '%s'\n(number of words > 2)" % self.line)
        return self.tokenize(size, words)    

    def run(self, lToken):
        lNewToken = []
        for self.token in lToken:
            token = self.decode()
            if token:
                lNewToken.append(token)
        return lNewToken

class AsmPass2(AsmBase):
    """
    Work on the given token list:
    - determine opcodes
    - return the enriched token list (file-ref, line-no, line-string, line-type, 
                                      address, instr-size, instr-words, opcodes)
    """
    def __init__(self, lNameSpaces, dSymbols, dAliases):
        AsmBase.__init__(self, lNameSpaces)
        self.ispass2 = True
        self.dSymbols = dSymbols
        self.dAliases = dAliases
        self.lNameSpaces = lNameSpaces
        self.prepare_opcode_tables()

    def check_operand_type(self, instr, opnd1, opnd2):
        opcode = self.dOpcodes[instr]
        words = Opcodes[opcode].split(":")
        if words[1] != "-":
            validOpnds = globals()[words[1]]
            if opnd1 != None and Operands[opnd1] not in validOpnds:
                self.error("Invalid operand1 type in\n'%s'" % self.line)
        if words[2] != "-":
            validOpnds = globals()[words[2]]
            if opnd2 != None and Operands[opnd2] not in validOpnds:
                self.error("Invalid operand2 type in\n'%s'" % self.line)
    
    def operand(self, s):
        if not s: return 0, None
        s = self.aliases(s)
        if s in self.dOperands:
            return self.dOperands[s], None
        if s == "#$0": return Operands.index("#0"), None
        if s == "#$1": return Operands.index("#1"), None
        m = reCONST.match(s)
        if m: return Operands.index("IMM"), self.value(m.group(1))
        m = reADDR.match(s)
        if m: return Operands.index("IND"), self.value(m.group(1))
        m = reREL.match(s)
        if m: 
            if m.group(1) == "-": 
                offset = (0x10000 - self.value(m.group(2))) & 0xFFFF
            else:
                offset = self.value(m.group(2))
            return Operands.index("REL"), offset
        m = reSTACK.match(s)
        if m: return Operands.index("[SP+n]"), self.value(m.group(1))
        if s[0] == "#": return Operands.index("IMM"), self.get_symbol_addr(s[1:]) 
        if s[0] in ["+", "-"]:
            dst_addr = self.get_symbol_addr(s[1:])
            src_addr = self.token[ADDRESS]  
            offset = (0x10000 + dst_addr - src_addr - 2) & 0xFFFF
            return Operands.index("REL"), offset
        return Operands.index("IND"), self.get_symbol_addr(s) 
        
    def get_opcode(self, instr):
        if instr not in self.dOpcodes:
            self.error("Invalid opcode in '%s'" % self.line)
        opc1 = self.dOpcodes[instr]
        num_opnds = 2 - Opcodes[opc1].count("-") 
        num_has = len(self.token[INSTRWORDS]) - 1
        if num_opnds != num_has:
            self.error("Invalid oprnd in '%s'" % self.line)
        return opc1 
    
    def tokenize(self, code):
        token = (self.token[FILENAME], self.token[LINENUM], self.token[LINESTR],
                 self.token[LINETYPE], self.token[ADDRESS], 
                 self.token[INSTRSIZE], self.token[INSTRWORDS], code)
        return token

    def decode(self):
        line = self.token[LINESTR]
        self.namespace = os.path.splitext(self.token[FILENAME])[0]
        self.line = line.split(";")[0].strip() # for error messages
        list_get = lambda l, idx: l[idx] if len(l) > idx else None
        instr = list_get(self.token[INSTRWORDS], 0)
        oprnd1 = list_get(self.token[INSTRWORDS], 1)
        oprnd2 = list_get(self.token[INSTRWORDS], 2)

        if instr not in self.dOpcodes:
             self.error("Invalid opcode in '%s'" % self.line)
        opc1 = self.get_opcode(instr)
        if oprnd1 and opc1 < 4:
            num = self.const_val(oprnd1)
            opc2, val1 = int(num / 32), None
            opc3, val2 = int(num % 32), None
        else:
            opc2, val1 = self.operand(oprnd1)
            opc3, val2 = self.operand(oprnd2)
        code = [(opc1 * 1024) + (opc2 * 32) + opc3]
        if val1 or val1 == 0: code.append(val1)
        if val2 or val2 == 0: code.append(val2)
        if len(code) != self.token[INSTRSIZE]:
             self.error("Internal error '%s'" % repr(self.token))
        return self.tokenize(code)
    
    def run(self, lToken):
        lNewToken = []
        for self.token in lToken:
            if self.token[LINETYPE] == CODETYPE:
                token = self.decode()
            else:
                token = self.tokenize(self.token[INSTRWORDS])
            lNewToken.append(token)
        return lNewToken

def locater(lToken):
    """
    Memory allocation of the token list code.
    Returns start-address, the array with the opcodes, and the last used address
    (unused memory cells are set to -1) 
    """
    l = copy(lToken)
    l.sort(key=lambda item: item[ADDRESS])
    start = list(filter(lambda t: t[LINETYPE] < COMMENT, l))[0][ADDRESS]
    end   = l[-1][ADDRESS] + l[-1][INSTRSIZE]
    size = end - start
    mem = array('l', [-1] * size)

    for token in lToken:
        if token[LINETYPE] == CODETYPE:
            addr = token[ADDRESS] - start
            for idx, val in enumerate(token[OPCODES]):
                if mem[addr + idx] != -1: outp("Warning: Mem. loc. conflict at $%04X" % (addr + idx))
                mem[addr + idx] = val
        elif token[LINETYPE] in [BTEXTTYPE, WTEXTTYPE]:
            addr = token[ADDRESS] - start
            for idx, val in enumerate(token[OPCODES]):
                if mem[addr + idx] != -1: outp("Warning: Mem. loc. conflict at $%04X" % (addr + idx))
                mem[addr + idx] = val
        elif token[LINETYPE] == DATATYPE:
            addr = token[ADDRESS] - start
            for idx, val in enumerate(token[OPCODES]):
                if mem[addr + idx] != -1: outp("Warning: Mem. loc. conflict at $%04X" % (addr + idx))
                mem[addr + idx] = val
    return start, mem, end-1
    
def list_file(path, fname, lToken):
    """
    Generate a list file
    """
    from time import localtime, strftime
    fname = os.path.splitext(fname)[0] + ".lst"
    outp(" - write %s..." % fname)
    t = strftime("%d-%b-%y %H:%M:%S", localtime())
    lOut = []
    lOut.append("VM16ASM v%s  %s  %s" % (VERSION, fname, t))
    lOut.append("")
    for token in lToken:
        if token[LINETYPE] == COMMENT:
            cmnt = "%s" % token[LINESTR].rstrip()
            lOut.append("%s" % cmnt)
        elif token[LINETYPE] == CODETYPE:
            addr = "%04X" % token[ADDRESS]
            code = ", ".join(["%04X" % c for c in token[OPCODES]])
            cmnt = "%s" % token[LINESTR].strip()
            lOut.append("%s: %-12s  %s" % (addr, code, cmnt))
        elif token[LINETYPE] in [BTEXTTYPE, WTEXTTYPE]:
            addr = "%04X" % token[ADDRESS]
            code = ", ".join(["%04X" % c for c in token[OPCODES]])
            cmnt = "%s" % token[LINESTR].rstrip()
            lOut.append("%s" % cmnt)
            lOut.append("%s: %s" % (addr, code))
        elif token[LINETYPE] == DATATYPE:
            addr = "%04X" % token[ADDRESS]
            code = ", ".join(["%04X" % c for c in token[OPCODES]])
            cmnt = "%s" % token[LINESTR].rstrip()
            lOut.append("%s" % cmnt)
            lOut.append("%s: %s" % (addr, code))
    open(path + fname, "wt").write("\n".join(lOut))
    
def bin_file(path, fname, mem, fillword=0):
    """
    Generate a text file with hex values for import into Minetest 
    """
    fname = os.path.splitext(fname)[0] + ".bin"
    outp(" - write %s..." % fname)
    lOut = []
    for idx, v in enumerate(mem):
        lOut.append("%04X" % (v if v != -1 else 0))
        if idx > 0 and idx % 8 == 0:
            lOut[-1] = "\n" + lOut[-1]
    open(path + fname, "wt").write(" ".join(lOut))
    
def tbl_file(path, fname, mem, fillword=0):
    """
    Generate a text block to be used as constant table for testing purposes
    """
    fname = os.path.splitext(fname)[0] + ".tbl"
    outp(" - write %s..." % fname)
    lOut = []
    for idx, v in enumerate(mem):
        lOut.append("0x%04X" % (v if v != -1 else 0))
        if idx > 0 and idx % 8 == 0:
            lOut[-1] = "\n" + lOut[-1]
    open(path + fname, "wt").write(", ".join(lOut))
    
def com_file(path, fname, start_addr, mem):
    """
    Generate a binary COM file with for J/OS
    """
    if start_addr == 0x100:
        fname = os.path.splitext(fname)[0] + ".com"
        outp(" - write %s..." % fname)
        size = len(mem)
        s = struct.pack("<" + size*'H', *mem)
        open(path + fname, "wb").write(s)
        return size
    outp("Error: Start address must be $100 (hex)!")
    sys.exit(-1)
    
def h16_file(path, fname, start_addr, last_addr, mem):
    """
    Generate a H16 file for import into Minetest 
    """
    def first_valid(arr, start):
        for idx, val in enumerate(arr[start:]):
            if val != -1: return start + idx
        return ROWSIZE
     
    def first_invalid(arr, start):       
        for idx, val in enumerate(arr[start:]):
            if val == -1: return start + idx
        return ROWSIZE

    def add(lOut, row, addr):
        s = "".join(["%04X" % v for v in row])
        lOut.append(":%X%04X00%s" % (len(row), addr, s))
        return len(row)
             
    fname = os.path.splitext(fname)[0] + ".h16"
    outp(" - write %s..." % fname)

    idx = 0
    ROWSIZE = 8
    lOut = []
    size = 0
    lOut.append(":2000001%04X%04X" % (start_addr, last_addr))
    while idx < len(mem):
        row = mem[idx:idx+ROWSIZE]
        i1 = 0
        offs = 0
        while i1 < ROWSIZE and idx < len(mem):
            i1 = first_valid(row, i1)
            i2  = first_invalid(row, i1)
            if i1 != i2 and i1 < ROWSIZE:
                size += add(lOut, row[i1:i2], start_addr + idx + i1)
                i1 = i2
        idx += ROWSIZE
    lOut.append(":00000FF")
    open(path + fname, "wt").write("\n".join(lOut))
    return size
 
def symbol_table(dSymbols):
    outp("\nSymbol table:")
    items = []
    for key, addr in dSymbols.items():
        items.append((key, addr))
    items.sort(key=lambda item: item[1])
    for item in items:
        outp(" - %-24s = %04X" % (item[0], item[1]))

def debug_out(lToken, dSymbols, dAliases):    
    for tok in lToken:
        print(str(tok))
    print(dSymbols)
    print(dAliases)
       
def assembler():
    global DEST_PATH

    ## server side files need a special path/name handing
    if "--srv" in sys.argv:
        DEST_PATH = sys.argv[2]
        fname = sys.argv[3]
    else:
        DEST_PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[1]))) + "/"
        fname = os.path.basename(sys.argv[1])

    outp("VM16 ASSEMBLER v%s (c) 2019-2021 by Joe\n" % VERSION, True)
    outp(" - read %s..." % fname)
    
    t = Tokenizer()
    lToken, lNameSpaces = t.load_file(DEST_PATH, fname)
    #debug_out(lToken, {}, {})
    #sys.exit(0)
    
    a = AsmPass1(lNameSpaces)
    lToken = a.run(lToken)
    #debug_out(lToken, a.dSymbols, a.dAliases)
    
    a = AsmPass2(lNameSpaces, a.dSymbols, a.dAliases)
    lToken = a.run(lToken)

    if "--lst" in sys.argv:
        list_file(DEST_PATH, fname, lToken)
        
    start_addr, mem, last_addr = locater(lToken)
    
    if "--com" in sys.argv:
        size = com_file(DEST_PATH, fname, start_addr, mem)
    else:
        size = h16_file(DEST_PATH, fname, start_addr, last_addr, mem)
    
    if "--tbl" in sys.argv: tbl_file(DEST_PATH, fname, mem)
    if "--sym" in sys.argv: symbol_table(a.dSymbols)
    
    outp("")
    outp("Code start address: $%04X" % start_addr)
    outp("Last used address:  $%04X" % last_addr)
    outp("Code size: $%04X/%u words\n" % (size, size))
    return 0

def main():
    if len(sys.argv) < 2 or ("--srv" in sys.argv and len(sys.argv) < 4):
        outp("Syntax: vm16asm <asm-file> <options>")
        outp("Options:")
        outp(" --com  Generate COM file (not H16)")
        outp(" --lst  Generate list file")
        outp(" --sym  Print symbol table entries")
        outp("or:")
        outp(" -cls   Short for '--com --lst --sym'")
        
        sys.exit(0)
    
    parameter()
    assembler()

