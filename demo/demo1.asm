; Demo1 demonstrates the possibilities of the vm16asm assembler.

; Macro: if equal(%1, %2) then <block> %3: 
    $macro  ifeq 3
        move  A, %1
        skeq  A, %2
        jump  %3
    $endmacro

VAR1 = $13E         ; global const definition
  var2 = $13F         ; local const definition

        .org $200   ; set location counter
        .code       ; start code segement

START1:             ; global label
  start2:             ; local label
exit:   jump  1000
        jump  $1000
        
        ifeq var1 #10 TEXT1
        halt
end:        
        brk   #$10

        .text       ; normal text segment (one ascii char per word)
TEXT1:  "Hello "
        "World!\0"  ; \0 as end-of-string

        .ctext      ; compressed text segment (two ascii chars per word)
TEXT2:  "Hello World\0"
TEXT3:  "Hello World!\0"
TEXT4:  "Hello World!!\0"

        .data       ; start data segment
var1:   $10
var2:   $1234, 4000, 0        

$include "strcmp.asm"

        .code       ; start code segement
        jump $1000
        call strcmp
        call strcmp.start

