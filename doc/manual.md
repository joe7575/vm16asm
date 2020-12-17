# Assembler Manual

## Introduction

The Assembler `vm16asm`  is used to translate assembly code into a H16 file as in the following example. This assembler is not available ingame, it must be installed on your PC (Linux, macOS, and Windows). The generated H16 file can then be transfered into the game via copy/paste.

Example "7segment.asm":

```assembly
; 7 segment demo v1.0
; PDP13 7-Segment on port #0

    move A, #$80    ; 'value' command
    move B, #00     ; value in B

loop:
    add  B, #01
    and  B, #$0F    ; values from 0 to 15
    out #00, A
    nop
    nop
    jump loop
```

H16 file "7segment.h16":

```
:80000002010008020300000303000014030000F
:6000800660000000000000012000004
:00000FF
```

The H16 file includes also address information so that the code can be located to the predefined VM16 memory address.

If installed properly, you can directly type:

```
vm16asm <asm-file>
```





## Special signs

The `#` sign in `move A, #0` signals an absolute value (immediate addressing). This value is loaded into the register. In contrast to `move A, 0`, where the value from memory address `0` is loaded into the register.

The `$` sign signals a hexadecimal value. `$400` is equal to `1024`.

`#` and `$` signs also can be combined, like in `jump #$1000`



## Comments

Comments are used for addition documentation, or to disable some lines of code. Every character behind the `;` sign is a comment and is ignored by the assembler:

```assembly
; this is a comment
    move    A, 0    ; this is also a comment
```



## Labels

Labels allow to implement a jump to a dedicated position without knowing the correct memory address. 
In the example above the instruction `out  #8, A` will be executed after the instruction `jump LOOP`.  

For labels  the characters 'A' - 'Z', 'a' - 'z',  '_' and '0' - '9' are allowed ('0' - '9' not as first character) following by the ':' sign.

Labels can be used in two different ways:

- `jump  LOOP` is translated into an instruction with an absolute memory address
- `jump +LOOP` is translated into an instruction with a relative address (+/- some addresses), so that the code can be relocated to a different memory address

The assembler distinguishes two kinds of labels:

- file local labels,  written completely in lowercase letters, e.g. `loop:`
- globally valid labels, written with at least one capital letter, e.g. `Loop:`

The difference between "file local" and "global" will be explained in the chapter "Include Instruction".



## Assembler Directives

Assembler directives are used to distinguish between code and text segments, or to specify a memory address for following code blocks.

Here an example:

```assembly
; Hello world for the Telewriter v1.0

        .code
START:  move    A, #TEXT
        sys     #0
        halt

        .org $100
        .text
TEXT:   "Hello "
        "World\0"
```

- `.code` marks the start of a code block and is optional at the beginning of a program (code is default)

- `.text` marks the start of a text block with "..." strings. `\0` is equal to the value zero and here used to terminate the string for the `sys #0` command.
- `.org` defines a memory start address. In the example above, the text characters will be stored at address 100hex and the following.

The assembler output for the example above looks like:

```
VM16 ASSEMBLER v1.0.2 (c) 2019-2020 by Joe
 - read /home/joachim/minetest5/mods/pdp13/examples/telewriter.asm...
 - write /home/joachim/minetest5/mods/pdp13/examples/telewriter.lst...
 - write /home/joachim/minetest5/mods/pdp13/examples/telewriter.h16...
Symbol table:
 - START            = 0000
 - TEXT             = 0100
Code start address: $0000
Code size: $010C/268 words
```



## Symbols

To make you program better readable, the assembler support constant or symbol definitions.

```assembly
INP_BUFF = $40      ; 64 chars
OUT_BUFF = $80      ; 64 chars

START:  move    X, #INP_BUFF
        move    Y, #OUT_BUFF
```

For symbols  the characters 'A' - 'Z', 'a' - 'z',  '_' and '0' - '9' are allowed ('0' - '9' not as first character).

Of course, symbols must be defined before they can be used.



## Include Instruction

To bind several asm files to one larger project, the assembler allows to import other files with the `$include` instruction:

```assembly
$include "itoa.asm"
```

This allows to use code or call functions from other files by means of globally valid labels (see chap. Labels).

Locally valid labels from other files are not visible and therefore are typically used to build loops.
Globally valid labels from other files are visible and therefore typically used as function start addresses.

