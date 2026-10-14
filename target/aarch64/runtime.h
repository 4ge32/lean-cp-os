#ifndef LEAN_CP_OS_TARGET_RUNTIME_H
#define LEAN_CP_OS_TARGET_RUNTIME_H
#include <stdint.h>
#include <stddef.h>
enum { OS_ACTIVATE, OS_TERMINATE, OS_CHAIN, OS_SCHEDULE, OS_GET_ID, OS_GET_STATE,
       OS_STEP_PC, OS_ENTER_ISR, OS_EXIT_ISR };
enum { E_OK, E_OS_ID, E_OS_LIMIT, E_OS_CALLEVEL, E_OS_RESOURCE, E_BAD_INPUT };
typedef void (*TaskEntry)(void);
struct OsConfig { unsigned count; unsigned priority[4], limit[4], preemptive[4]; };
struct OsReply { unsigned status, value; };
uint64_t os_pack_config(const struct OsConfig *cfg);
void os_run(const struct OsConfig *cfg, const TaskEntry entry[4], const unsigned *autostart, unsigned count);
struct OsReply os_service(unsigned op, unsigned id, unsigned ctx);
unsigned ActivateTask(unsigned id);
unsigned TerminateTask(void);
unsigned ChainTask(unsigned id);
unsigned Schedule(void);
unsigned GetTaskID(unsigned *id);
unsigned GetTaskState(unsigned id, unsigned *state);
void os_assert(int condition, const char *message);
void os_puts(const char *text);
void os_number(unsigned number);
void os_trace(unsigned event);
void os_expect(const unsigned *events, unsigned count, const char *name);
_Noreturn void os_exit(unsigned code);
unsigned os_register_probe(void (*callback)(void));
#endif
