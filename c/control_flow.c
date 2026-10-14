/* Host-only test of successful termination discarding a C continuation.
 * setjmp/longjmp are a test HAL; no target context-switch claim. */
#include <setjmp.h>
#include <stdio.h>
#include <lean/lean.h>
#include "bridge.h"
extern void lean_initialize_runtime_module(void);
extern lean_object *initialize_LeanCpOs_Bridge(uint8_t, lean_object *);
static jmp_buf dispatcher;
static uint32_t active_mask;
static unsigned after_termination;
static unsigned count;
static unsigned order[3];

static unsigned terminate_task(void) {
    uint64_t result = lean_cp_step(active_mask, 1, 0);
    if (result & 4096) {
        active_mask = (uint32_t)(result & 15);
        longjmp(dispatcher, 1);
    }
    return (unsigned)((result >> 8) & 15);
}
static void task(unsigned id) {
    if (count >= 3) { after_termination++; return; }
    order[count++] = id;
    (void)terminate_task();
    after_termination++; /* Must not execute on success. */
}
int main(void) {
    lean_initialize_runtime_module();
    lean_object *r = initialize_LeanCpOs_Bridge(1, lean_io_mk_world());
    if (lean_io_result_is_error(r)) { lean_dec(r); return 2; }
    lean_dec(r);
    lean_io_mark_end_initialization();
    if (terminate_task() != 3) return 3; /* Error returns to caller. */
    active_mask = (uint32_t)(lean_cp_step(0, 0, 0) & 15);
    active_mask = (uint32_t)(lean_cp_step(active_mask, 0, 2) & 15);
    while (active_mask != 0) {
        if (setjmp(dispatcher) == 0) {
            unsigned current = (unsigned)((lean_cp_step(active_mask, 2, 0) >> 16) & 15);
            task(current - 1);
            return 4; /* Successful task termination must discard this frame. */
        }
    }
    if (count != 2 || order[0] != 2 || order[1] != 0 || after_termination != 0) return 5;
    puts("PASS T-CONTROL: high -> low -> idle; successful termination did not return; idle error returned");
    return 0;
}
