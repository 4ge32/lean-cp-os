.section .text.boot, "ax"
.global _start
_start:
    msr daifset, #15
    ldr x0, =__boot_stack_top
    mov sp, x0
    ldr x0, =__bss_start
    ldr x1, =__bss_end
1:  cmp x0, x1
    b.hs 2f
    str xzr, [x0], #8
    b 1b
2:  bl qemu_main
3:  wfe
    b 3b
