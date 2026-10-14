/* AAPCS64 call-boundary context switch. Build all task code -mgeneral-regs-only.
 * Asynchronous IRQ context and SIMD/FPU state are deliberately outside this HAL. */
.text
.global os_context_switch
.type os_context_switch, %function
os_context_switch:
    stp x19, x20, [x0, #0]
    stp x21, x22, [x0, #16]
    stp x23, x24, [x0, #32]
    stp x25, x26, [x0, #48]
    stp x27, x28, [x0, #64]
    stp x29, x30, [x0, #80]
    mov x2, sp
    str x2, [x0, #96]
    ldp x19, x20, [x1, #0]
    ldp x21, x22, [x1, #16]
    ldp x23, x24, [x1, #32]
    ldp x25, x26, [x1, #48]
    ldp x27, x28, [x1, #64]
    ldp x29, x30, [x1, #80]
    ldr x2, [x1, #96]
    mov sp, x2
    ret
.size os_context_switch, .-os_context_switch

/* Seed every preserved general register across a callback that preempts us. */
.global os_register_probe
.type os_register_probe, %function
os_register_probe:
    stp x19, x20, [sp, #-96]!
    stp x21, x22, [sp, #16]
    stp x23, x24, [sp, #32]
    stp x25, x26, [sp, #48]
    stp x27, x28, [sp, #64]
    stp x29, x30, [sp, #80]
    mov x19, #119
    mov x20, #120
    mov x21, #121
    mov x22, #122
    mov x23, #123
    mov x24, #124
    mov x25, #125
    mov x26, #126
    mov x27, #127
    mov x28, #128
    mov x29, #129
    blr x0
    mov x0, #0
    cmp x19, #119
    b.ne 1f
    cmp x20, #120
    b.ne 1f
    cmp x21, #121
    b.ne 1f
    cmp x22, #122
    b.ne 1f
    cmp x23, #123
    b.ne 1f
    cmp x24, #124
    b.ne 1f
    cmp x25, #125
    b.ne 1f
    cmp x26, #126
    b.ne 1f
    cmp x27, #127
    b.ne 1f
    cmp x28, #128
    b.ne 1f
    cmp x29, #129
    b.ne 1f
    mov x0, #1
1:  ldp x19, x20, [sp, #0]
    ldp x21, x22, [sp, #16]
    ldp x23, x24, [sp, #32]
    ldp x25, x26, [sp, #48]
    ldp x27, x28, [sp, #64]
    ldp x29, x30, [sp, #80]
    add sp, sp, #96
    ret
.size os_register_probe, .-os_register_probe
