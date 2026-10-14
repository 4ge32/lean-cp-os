#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <lean/lean.h>
#include "bridge.h"

extern lean_object *initialize_LeanCpOs_Bridge(uint8_t builtin, lean_object *world);
extern void lean_initialize_runtime_module(void);
int main(void) {
    lean_initialize_runtime_module();
    lean_object *r = initialize_LeanCpOs_Bridge(1, lean_io_mk_world());
    if (lean_io_result_is_error(r)) {
        lean_io_result_show_error(r);
        lean_dec(r);
        return 2;
    }
    lean_dec(r);
    lean_io_mark_end_initialization();
    uint32_t mask, op, id;
    int count;
    while ((count = scanf("%" SCNu32 " %" SCNu32 " %" SCNu32,
                         &mask, &op, &id)) == 3) {
        printf("%" PRIu64 "\n", lean_cp_step(mask, op, id));
    }
    return count == EOF ? 0 : 3;
}
