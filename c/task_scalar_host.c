/* Decimal scalar ABI runner. Links only reachable generated scalar code. */
#include <inttypes.h>
#include <stdio.h>
#include <stdint.h>
extern uint64_t lean_osek_step(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
int main(void) {
    uint64_t cfg, state, op, id, ctx;
    int n;
    while ((n = scanf("%" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64 " %" SCNu64,
                     &cfg, &state, &op, &id, &ctx)) == 5)
        printf("%" PRIu64 "\n", lean_osek_step(cfg, state, op, id, ctx));
    return n == EOF ? 0 : 2;
}
