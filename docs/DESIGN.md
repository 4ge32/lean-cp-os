# Design: basic-task kernel and the M0 learning model

## Current development scope

The agreed completion unit is a single-core Basic Task subsystem: configurable
task count/priorities/activation limits, equal-priority FIFO, all six task
services, and saved/restored task continuations on QEMU AArch64. Extended Tasks
and events follow in a later stage. OSEK OS 2.2.3 supplies the current behavior
requirements; AUTOSAR R25-11 remains a future compatibility review.

`LeanCpOs/Task/Model.lean` models activation frames rather than Boolean task
membership. Repeated activation queues another fresh request, not another
simultaneously running instance. An interrupted frame retains its progress and
returns to the front of its priority group. Termination drops the current frame;
successful ChainTask drops it and queues a fresh target request atomically.
Self-chain does not increase the number of outstanding activations.

The current task is an `Option Frame`, so there can be at most one running
frame. The generic `Valid` invariant checks task identities and activation
counts. Dispatch membership, maximum priority and FIFO head selection are
separate proof statements. A nonpreemptive task may keep running while a higher
priority request waits; validity therefore does not require the current task to
always be the highest-priority request. Explicit Schedule only considers
strictly higher-priority tasks, not round-robin peers.

ISR nesting is modeled as an environment boundary: requests can be queued while
inside an ISR, and automatic preemption is considered when the outermost ISR
exits. Held-resource call guards are modeled; resource acquisition, priority
ceilings, hardware interrupt entry and hooks are separate future subsystems.
Startup test helpers inject requests under a deferred-dispatch boundary; they
do not implement the OSEK StartOS service.

`LeanCpOs/Task/Scalar.lean` is a fixed-capacity target adapter. It packs up to
four task configurations and eight total activation requests into scalar words
so that its actual generated C can run without a heap on the target. It rejects
out-of-capacity configurations. The generic model has no such fixed task count.
Their correspondence is checked by differential tests, not a formal refinement
proof. The target context switch and compiler/runtime boundary also remain
outside the Lean proofs. See [task contracts](TASK_CONTROL.md) and
[QEMU execution](QEMU.md).

The original M0 below remains a small educational example and regression suite.

## Decisions

M0 is an executable transition kernel for exactly three static tasks: `low`, `mid`, `high`, with fixed distinct priorities 1, 2, 3. Task IDs at the experimental ABI are 0, 1, 2. Each task can have one outstanding activation, represented by a Boolean. This is deliberately a finite first configuration, not an arbitrary-size scheduler.

`State` has independent `active` membership and `current` task. The invariant `Valid s` means `current = select active`; malformed combinations are representable, so preservation is not guaranteed by the type alone. `taskState` derives Suspended when inactive, Running when active and current, and Ready otherwise. The eligible set includes both Ready and Running tasks. `select` chooses high, then mid, then low, or idle. No duplicate ready queue is maintained in M0.

Transitions are atomic, sequential and at task service boundaries. Activation sets only the target's membership and reschedules; a duplicate or invalid ID preserves the entire input state. Termination removes the current task and reschedules. Idle termination returns a project-defined call-level error; this is not a complete OSEK context matrix. Query results are values, not pointer writes. `None` represents idle/invalid query output, with an error distinguishing the latter.

`Control.returned` carries the logical service response. After activation preempts a caller, actual delivery to that caller must wait until it resumes; M0 has no saved machine continuation. `Control.dispatch` on successful termination says that the caller continuation must be discarded. It is not a normal successful return. The C host demo checks this distinction with nonlocal transfer; machine stacks/registers are a later refinement obligation.

Frame conditions concern activation membership. Derived Running/Ready state can legitimately change for the old and new runner. `unrelated_task_state` proves equality when membership agrees and neither old nor new current task is the observed task. This prevents an incorrectly strong claim that activation cannot change any other task's scheduling state.

## Proof boundary

`select_member` and `select_highest` check the actual selection algorithm over all Boolean memberships and all three task choices by kernel-checked finite case reduction. The scheduler proofs are separate from representational facts such as the size of an Option. `activate_preserves`, `terminate_preserves`, and induction on finite command lists establish reachable validity from the initial empty state. Error/frame theorems apply even where a valid-input assumption is unnecessary; each exact statement is in `Proofs.lean`.

Assumptions are explicitly catalogued in `trace/requirements.json`: static three-task configuration, atomic single-caller transitions, valid inputs for preservation, canonical scalar ABI states, and the trusted tool/runtime boundary. `propext` is Lean's standard propositional extensionality axiom, used by simplification. No new domain-specific axiom is introduced. The audit lists dependencies per theorem; proof checking is performed by Lean's kernel, not by `native_decide`.

The abstract logic's safety properties are checked. No liveness or progress fairness claim is made: repeated high-priority activation can starve lower tasks. “Full preemptive” at M0 means immediate priority reselection at modeled service transitions; there are no asynchronous interrupt events or instruction-level context switches. Generated C behavior is experimentally compared, not formally refined from Lean. Compiler, runtime, FFI, libc, host OS, C control transfer, future assembly and hardware are outside the proved kernel model.

## Milestones

| Stage | Deliverable | Exit gate |
|---|---|---|
| M0 | Three-task logic, proofs, host/actual generated C, trace/evidence | Clean exact-SHA local verification |
| M0-publication | Repository, Actions and Pages | Remote SHA equals local; actual Actions and Pages URLs verified |
| M1 | Configurable Basic Tasks, FIFO/multiple requests, six services | Generic selection/preservation/service proofs; oracle and generated-C comparison |
| M2 | QEMU AArch64 target and minimal HAL | Boot, UART trace, saved register/stack context, restart and termination/chain transfer |
| M3 | Runtime constraints | Allocation/deallocation and stack bounds, reentrancy design, refinement obligations |
| M4 | Incremental OSEK/ATK2 feature expansion | Explicit feature requirements/proofs/tests; no class claim until complete |

## First target / minimal HAL

The selected target is QEMU AArch64 `virt`, `cortex-a53`, one core. The [official QEMU description](https://www.qemu.org/docs/master/system/arm/virt.html) documents this CPU and platform. The verifier records the QEMU/tool versions and command line. The current image uses fixed RAM/UART addresses and semihosted test exit; it does not depend on interrupt-controller or timer behavior. CPU choice and target capacities are project decisions, not OSEK requirements.

The HAL contains reset entry/linker script, stack/BSS initialization, PL011 polled output, fail-stop assertions, and an AAPCS64 context switch. The dispatcher translates the generated scalar result into resume or fresh entry, including non-returning discard after successful termination/chain. Architectural timer/GIC and asynchronous interrupt entry are later work. The scalar subset avoids linking the general Lean runtime; that does not settle freestanding support for richer Lean programs.

## Deferred scope

Extended Tasks/events; resources/priority ceiling and internal resources; alarms/counters/schedule tables; full StartOS/ShutdownOS/application-mode services and hooks; physical ISR entry; multicore; memory/time protection; all standard error precedence and call-level rules beyond the declared task/ISR2 subset. Safety conformance, liveness, WCET and asynchronous interruption safety require different evidence and remain separate.
