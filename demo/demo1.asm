; Demo1 demonstrates the possibilities of the vm16asm assembler.

VAR1 = $13E         ; global const definition
var2 = $13F         ; local const definition

        .org $200   ; set location counter
        .code       ; start code segement

START1:             ; global label
start2:             ; local label
exit:   jump  1000
        jump  $1000
        halt
        brk   #$10

        .text       ; normal text segment (one ascii char per word)
TEXT1:  "Hello "
        "World!\0"  ; \0 as end-of-string

        .ctext      ; compressed text segment (two ascii chars per word)
TEXT2:  "Hello World\0"
TEXT3:  "Hello World!\0"
TEXT4:  "Hello World!!\0"

        .data       ; start data segment
DATA:   $10, $1234, 4000, 0        

        .code       ; start code segement
        jump $1000
