# vm16asm - Assembler for the VM16 CPU

The Assembler `vm16asm`  is used to translate VM16 assembly code into `.h16`
or `.com` files, used for the mod [pdp13](https://github.com/joe7575/pdp13).
This assembler is available in-game, but can be installed on your PC
(Linux, macOS, and Windows) in addition. Generated `.h16` files can
then be transfered into the game via copy/paste.

Example `7segment.asm`:

```assembly
; 7 segment demo v1.0
; PDP13 7-Segment on port #0

    move A, #$80    ; 'value' command
    move B, #00     ; value in B

loop:
    add  B, #01
    and  B, #$0F    ; values from 0 to 15
    out  #00, A
    nop
    nop
    jump loop
```


## Installation

Download the file `vm16asm-1.2-py3-none-any.whl`
from: https://github.com/joe7575/vm16asm/blob/main/dist/

Install it with Python `pip`, e.g. for Ubuntu:

```
sudo pip3 install vm16asm-1.2-py3-none-any.whl
```


## Using

Syntax:

```
vm16asm <asm-file> <options>
```

Example:

```
vm16asm test.asm
```

Options are:

- `--com`  to generate a `.com` file instead of a `.h16` file
- `--sym` to output all values from the symbol table
- `--lst` to generate a `.lst` file in addition



## License

Copyright (C) 2019-2021 Joachim Stolberg
Licensed under the GNU GPLv3   (See LICENSE.txt)



## History

- 2020-11-21  v1.0.1  * First commit
- 2020-12-08  v1.0.2  * Change syntax for sys instruction
- 2020-12-28  v1.0.3  * Add export for COM files
- 2021-01-03  v1.1.0  * Add 'bkr' opcode
- 2021-01-03  v1.2.0  * Change local/global label handling, add macros feature


