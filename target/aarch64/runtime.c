#include "runtime.h"
extern uint64_t lean_osek_step(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
struct Context { uint64_t saved[12], sp; };
_Static_assert(offsetof(struct Context, sp) == 96, "assembly context offset");
extern void os_context_switch(struct Context *, const struct Context *);
static struct Context scheduler, contexts[4];
static _Alignas(16) uint64_t stacks[4][2048];
static unsigned live[4], executing, task_count;
static TaskEntry entries[4];
static uint64_t config, state;
static unsigned events[128], event_count;
#define STATE_MASK UINT64_C(0xffffffffff)
#define GUARD UINT64_C(0x7361636b67756172)

void *memset(void *p, int c, size_t n) {
    unsigned char *s = p;
    for (size_t i = 0; i < n; ++i) s[i] = (unsigned char)c;
    return p;
}
void *memcpy(void *to, const void *from, size_t n) {
    unsigned char *d = to;
    const unsigned char *s = from;
    for (size_t i = 0; i < n; ++i) d[i] = s[i];
    return to;
}
void os_puts(const char *text) {
    volatile uint32_t *uart = (volatile uint32_t *)UINT64_C(0x09000000);
    while (*text) {
        while (uart[0x18 / 4] & (1u << 5)) { }
        uart[0] = (unsigned char)*text++;
    }
}
void os_number(unsigned n) {
    char s[12];
    unsigned i = 0;
    do { s[i++] = (char)('0' + n % 10); n /= 10; } while (n);
    while (i) { char v[2] = {s[--i], 0}; os_puts(v); }
}
_Noreturn void os_exit(unsigned code) {
    uint64_t block[2] = {UINT64_C(0x20026), code};
    register uint64_t operation __asm__("x0") = 0x20;
    register uint64_t argument __asm__("x1") = (uintptr_t)block;
    __asm__ volatile("hlt #0xf000" : "+r"(operation) : "r"(argument) : "memory");
    for (;;) __asm__ volatile("wfe");
}
void os_assert(int condition, const char *message) {
    if (!condition) { os_puts("FAIL "); os_puts(message); os_puts("\n"); os_exit(1); }
}
void os_trace(unsigned event) {
    os_assert(event_count < 128, "trace overflow");
    events[event_count++] = event;
}
void os_expect(const unsigned *expected, unsigned count, const char *name) {
    os_puts("TRACE "); os_puts(name); os_puts(":");
    for (unsigned i = 0; i < event_count; ++i) { os_puts(" "); os_number(events[i]); }
    os_puts("\n");
    os_assert(event_count == count, "trace length");
    for (unsigned i = 0; i < count; ++i) os_assert(events[i] == expected[i], "trace order");
    os_puts("PASS "); os_puts(name); os_puts("\n");
}
uint64_t os_pack_config(const struct OsConfig *cfg) {
    os_assert(cfg->count > 0 && cfg->count <= 4, "task count capacity");
    uint64_t packed = (uint64_t)cfg->count << 36;
    unsigned sum = 0;
    for (unsigned i = 0; i < cfg->count; ++i) {
        os_assert(cfg->priority[i] <= 15, "priority capacity");
        os_assert(cfg->limit[i] > 0 && cfg->limit[i] <= 8, "activation limit capacity");
        os_assert(cfg->preemptive[i] <= 1, "preemptive flag");
        sum += cfg->limit[i];
        packed |= (uint64_t)cfg->priority[i] << (4 * i);
        packed |= (uint64_t)cfg->limit[i] << (16 + 4 * i);
        packed |= (uint64_t)cfg->preemptive[i] << (32 + i);
    }
    os_assert(sum <= 8, "total activation capacity");
    return packed;
}
static unsigned current(void) { return (unsigned)((state >> 32) & 15); }
static void start_task(void) {
    entries[executing]();
    os_assert(0, "task returned without TerminateTask or ChainTask");
}
struct OsReply os_service(unsigned op, unsigned id, unsigned ctx) {
    unsigned old = current();
    uint64_t r = lean_osek_step(config, state, op, id, ctx);
    state = r & STATE_MASK;
    struct OsReply reply = {(unsigned)((r >> 40) & 15), (unsigned)((r >> 44) & 15)};
    if ((r >> 48) & 1) {
        os_assert(old != 0 && reply.status == E_OK, "discard validity");
        os_assert(stacks[old - 1][0] == GUARD, "discarded stack guard");
        live[old - 1] = 0;
        os_context_switch(&contexts[old - 1], &scheduler);
        os_assert(0, "discarded continuation resumed");
    } else if (old != current()) {
        os_assert(old != 0, "unexpected task dispatch outside dispatcher");
        os_context_switch(&contexts[old - 1], &scheduler);
        os_assert(executing == old - 1, "wrong resumed task");
    }
    return reply;
}
static unsigned call_context(void) { return ((state >> 36) & 15) ? 1 : 0; }
unsigned ActivateTask(unsigned id) { return os_service(OS_ACTIVATE, id, call_context()).status; }
unsigned TerminateTask(void) { return os_service(OS_TERMINATE, 0, call_context()).status; }
unsigned ChainTask(unsigned id) { return os_service(OS_CHAIN, id, call_context()).status; }
unsigned Schedule(void) { return os_service(OS_SCHEDULE, 0, call_context()).status; }
unsigned GetTaskID(unsigned *id) {
    struct OsReply r = os_service(OS_GET_ID, 0, call_context());
    if (r.status == E_OK) *id = r.value ? r.value - 1 : UINT32_MAX;
    return r.status;
}
unsigned GetTaskState(unsigned id, unsigned *task_state) {
    struct OsReply r = os_service(OS_GET_STATE, id, call_context());
    if (r.status == E_OK) *task_state = r.value;
    return r.status;
}
void os_run(const struct OsConfig *cfg, const TaskEntry entry[4], const unsigned *autostart, unsigned count) {
    config = os_pack_config(cfg); state = 0; event_count = 0; task_count = cfg->count;
    for (unsigned i = 0; i < 4; ++i) { live[i] = 0; entries[i] = entry[i]; }
    os_assert(((lean_osek_step(config, 0, OS_TERMINATE, 0, 0) >> 40) & 15) == E_OS_CALLEVEL,
              "idle termination must return error");
    /* Model startup as an ISR boundary to defer dispatch until autostart is complete.
       This is software injection, not a hardware interrupt implementation. */
    state = lean_osek_step(config, state, OS_ENTER_ISR, 0, 0) & STATE_MASK;
    for (unsigned i = 0; i < count; ++i) {
        uint64_t r = lean_osek_step(config, state, OS_ACTIVATE, autostart[i], 1);
        os_assert(((r >> 40) & 15) == E_OK, "autostart failed");
        state = r & STATE_MASK;
    }
    state = lean_osek_step(config, state, OS_EXIT_ISR, 0, 1) & STATE_MASK;
    while (current()) {
        executing = current() - 1;
        os_assert(executing < task_count, "invalid dispatched task");
        if (!live[executing]) {
            for (unsigned i = 0; i < 12; ++i) contexts[executing].saved[i] = 0;
            contexts[executing].saved[11] = (uintptr_t)start_task;
            contexts[executing].sp = (uintptr_t)&stacks[executing][2048];
            stacks[executing][0] = GUARD;
            live[executing] = 1;
        }
        os_context_switch(&scheduler, &contexts[executing]);
        for (unsigned i = 0; i < task_count; ++i)
            if (live[i]) os_assert(stacks[i][0] == GUARD, "stack guard");
    }
    for (unsigned i = 0; i < task_count; ++i) os_assert(!live[i], "stranded continuation");
    os_assert((state & UINT64_C(0xffffffff)) == 0, "idle with pending activations");
}
