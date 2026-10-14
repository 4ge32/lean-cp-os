ENTRY(_start)
SECTIONS {
  . = 0x40080000;
  .text : { KEEP(*(.text.boot)) *(.text .text.*) }
  .rodata : { *(.rodata .rodata.*) }
  .data : { *(.data .data.*) }
  . = ALIGN(16);
  __bss_start = .;
  .bss (NOLOAD) : { *(.bss .bss.*) *(COMMON) }
  __bss_end = .;
  . = ALIGN(16);
  . += 16384;
  __boot_stack_top = .;
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
