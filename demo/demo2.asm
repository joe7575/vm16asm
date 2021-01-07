        .org $100
        .code
start:  move    A, #text1
        sys     #0
        halt

        .data
var1:	100
var2:   $2123

        .org $200
        .text
text1:  "Hello World\0"
