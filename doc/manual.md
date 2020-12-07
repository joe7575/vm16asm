# Assembler Manual

## Introduction

The Assembler `vm16asm`  is used to translate assembly code into a H16 file as in the following example. This assembler is not available ingame, it must be installed on your PC (Linux, macOS, and Windows). The generated H16 file can then be transfered into the game via copy/paste.

Example "demo1.asm":

```assembly
; 7-Segement Demo v1.0
        move    A, #0
LOOP:   out     #8, A
        inc     A
        and     A, #$0F
        dly
        dly
        dly
        dly
        jump    LOOP
```

H16 file "demo1.h16":

```
:8000000200C6600000828004010000F04000400
:500080004000400040012000001
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
; Copy "Hello world" from code area to the screen buffer

        .code
START:  move    X, #TEXT
		move    Y, #$1000
LOOP:   move    [Y]+, [X]    
        bnze    [X]+, +LOOP
        halt

		.org $100
        .text
TEXT:   "Hello "
        "World\0"
```

- `.code` marks the start of a code block and is optional at the beginning of a program (code is default)

- `.text` marks the start of a text block with "..." strings. `\0` is equal to the value zero and here used to terminate the copy loop.
- `.org` defines a memory start address. In the example above, the text characters will be stored at address 100hex and the following.

The assembler output for the example above looks like:

```
VM16 ASSEMBLER v1.0.1 (c) 2019-2020 by Joe
 - read hello.asm...
 - write hello.lst...
 - write hello.h16...
Symbol table:
 - START            = 0000
 - LOOP             = 0004
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

