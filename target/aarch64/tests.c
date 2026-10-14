#include "runtime.h"
#define CHECK(call) os_assert((call) == E_OK, #call)
#define END() do { CHECK(TerminateTask()); os_assert(0, "TerminateTask returned on success"); } while (0)
#define EXPECT(name, ...) do { const unsigned e[] = {__VA_ARGS__}; os_expect(e, sizeof(e)/sizeof(e[0]), name); } while (0)

static void preempt_callback(void) { CHECK(ActivateTask(1)); }
static void preempt_low(void) {
    volatile unsigned locals[8] = {81,82,83,84,85,86,87,88};
    os_trace(10);
    os_assert(os_register_probe(preempt_callback), "callee-saved registers survived preemption");
    for (unsigned i = 0; i < 8; ++i) os_assert(locals[i] == 81 + i, "stack locals survived preemption");
    os_trace(11); END();
}
static void preempt_high(void) { os_trace(20); CHECK(ActivateTask(2)); END(); }
static void preempt_mid(void) { os_trace(30); END(); }

static void fifo_a(void) {
    os_trace(10); CHECK(ActivateTask(2)); CHECK(ActivateTask(3));
    CHECK(Schedule()); os_trace(11); END();
}
static void fifo_b(void) { os_trace(20); END(); }
static void fifo_c(void) { os_trace(30); END(); }
static void fifo_d(void) { os_trace(40); END(); }

static unsigned repeated_entries;
static void repeat_a(void) {
    volatile unsigned fresh = 100;
    unsigned invocation = ++repeated_entries;
    os_assert(invocation <= 3 && fresh == 100, "fresh activation entered at start");
    os_trace(10 + invocation);
    fresh += invocation;
    if (invocation == 1) {
        os_assert(ActivateTask(0) == E_OS_LIMIT, "queued activation limit returned");
        CHECK(ActivateTask(1));
        os_assert(fresh == 101, "repeat task preemption resumed existing frame");
    }
    END();
}
static void repeat_b(void) { os_trace(20); END(); }

static unsigned chain_a_entries, chain_b_entries;
static void chain_a(void) {
    volatile unsigned fresh = 701;
    unsigned invocation = ++chain_a_entries;
    os_assert(fresh == 701 && invocation <= 2, "self chain starts a fresh stack frame");
    fresh = 999;
    os_trace(invocation == 1 ? 10 : 11);
    CHECK(ChainTask(invocation == 1 ? 0 : 1));
    os_assert(0, "ChainTask returned on success");
}
static void chain_b(void) {
    unsigned invocation = ++chain_b_entries;
    os_trace(invocation == 1 ? 20 : 21);
    if (invocation == 1)
        os_assert(ChainTask(0) == E_OS_LIMIT, "chain target limit returned to same caller");
    END();
}

static void nonpreempt_low(void) {
    os_trace(10); CHECK(ActivateTask(1)); os_trace(11);
    CHECK(ActivateTask(2)); os_trace(12);
    CHECK(Schedule()); os_trace(13); END();
}
static void nonpreempt_high(void) { os_trace(20); END(); }
static void nonpreempt_mid(void) { os_trace(30); END(); }

static void errors(void) {
    unsigned value = 999;
    CHECK(GetTaskID(&value)); os_assert(value == 0, "GetTaskID running id");
    CHECK(GetTaskState(0, &value)); os_assert(value == 3, "GetTaskState running");
    CHECK(GetTaskState(1, &value)); os_assert(value == 1, "GetTaskState suspended");
    os_assert(ActivateTask(9) == E_OS_ID, "invalid id returns");
    os_assert(ActivateTask(0) == E_OS_LIMIT, "activation limit returns");
    os_assert(ChainTask(9) == E_OS_ID, "chain invalid id returns");
    for (unsigned op = OS_TERMINATE; op <= OS_SCHEDULE; ++op)
        os_assert(os_service(op, 0, 4).status == E_OS_RESOURCE, "resource guard returns");
    os_assert(os_service(OS_TERMINATE, 0, 1).status == E_OS_CALLEVEL, "wrong context returns");
    os_assert(os_service(99, 0, 2).status == E_BAD_INPUT, "unknown command returns");
    CHECK(GetTaskID(&value)); os_assert(value == 0, "errors preserve running task");
    os_trace(10); END();
}

static void isr_low(void) {
    os_trace(10);
    CHECK(os_service(OS_ENTER_ISR, 0, 0).status);
    CHECK(os_service(OS_ENTER_ISR, 0, 1).status);
    CHECK(ActivateTask(1));
    unsigned observed;
    CHECK(GetTaskID(&observed)); os_assert(observed == 0, "ISR GetTaskID sees interrupted task");
    CHECK(GetTaskState(1, &observed)); os_assert(observed == 2, "ISR sees ready activation");
    os_trace(11);
    os_assert(TerminateTask() == E_OS_CALLEVEL, "ISR cannot terminate task");
    CHECK(os_service(OS_EXIT_ISR, 0, 1).status); os_trace(12);
    CHECK(os_service(OS_EXIT_ISR, 0, 1).status); os_trace(13); END();
}
static void isr_high(void) { os_trace(20); END(); }

void qemu_main(void) {
    os_puts("Lean OSEK basic-task target: AArch64 virt / cortex-a53\n");
    {
        const struct OsConfig cfg = {3, {1,3,2}, {1,1,1}, {1,1,1}};
        const TaskEntry entry[4] = {preempt_low,preempt_high,preempt_mid,0};
        const unsigned start[] = {0}; os_run(&cfg, entry, start, 1);
        EXPECT("preempt-resume-registers-stack", 10,20,30,11);
    }
    {
        const struct OsConfig cfg = {4, {2,2,2,3}, {1,1,1,1}, {1,1,1,1}};
        const TaskEntry entry[4] = {fifo_a,fifo_b,fifo_c,fifo_d};
        const unsigned start[] = {0,1}; os_run(&cfg, entry, start, 2);
        EXPECT("equal-priority-fifo", 10,40,11,20,30);
    }
    {
        const struct OsConfig cfg = {2, {1,2}, {3,1}, {1,1}};
        const TaskEntry entry[4] = {repeat_a,repeat_b,0,0};
        const unsigned start[] = {0,0,0}; os_run(&cfg, entry, start, 3);
        EXPECT("queued-activations-fresh-entry", 11,20,12,13);
    }
    {
        const struct OsConfig cfg = {2, {1,1}, {1,1}, {1,1}};
        const TaskEntry entry[4] = {chain_a,chain_b,0,0};
        const unsigned start[] = {0,1}; os_run(&cfg, entry, start, 2);
        EXPECT("chain-self-other-nonreturn", 10,20,11,21);
    }
    {
        const struct OsConfig cfg = {3, {1,3,2}, {1,1,1}, {0,1,1}};
        const TaskEntry entry[4] = {nonpreempt_low,nonpreempt_high,nonpreempt_mid,0};
        const unsigned start[] = {0}; os_run(&cfg, entry, start, 1);
        EXPECT("nonpreemptive-explicit-schedule", 10,11,12,20,30,13);
    }
    {
        const struct OsConfig cfg = {2, {1,2}, {1,1}, {1,1}};
        const TaskEntry entry[4] = {errors,0,0,0};
        const unsigned start[] = {0}; os_run(&cfg, entry, start, 1);
        EXPECT("errors-return-with-state-intact", 10);
    }
    {
        const struct OsConfig cfg = {2, {1,2}, {1,1}, {1,1}};
        const TaskEntry entry[4] = {isr_low,isr_high,0,0};
        const unsigned start[] = {0}; os_run(&cfg, entry, start, 1);
        EXPECT("modeled-isr-defers-dispatch", 10,11,12,20,13);
    }
    os_puts("PASS QEMU: 7 scenarios; real task stacks; generated Lean decisions\n");
    os_exit(0);
}
