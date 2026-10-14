#ifndef LEAN_CP_BRIDGE_H
#define LEAN_CP_BRIDGE_H
#include <stdint.h>
/* Scalar test ABI. Initialization required once by the host before use.
 * Bits: [3:0] active mask, [7:4] runner (0 idle, 1..3 task),
 * [11:8] project status, bit 12 dispatch, [19:16] query value.
 * No pointer ownership crosses this boundary. */
uint64_t lean_cp_step(uint32_t mask, uint32_t op, uint32_t id);
#endif
