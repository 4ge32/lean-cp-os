# Generated C and runtime boundary

## Configurable task control and the QEMU target

The new `LeanCpOs/Task/Model.lean` is the arbitrary-configuration specification.
Its proofs apply to the stated model invariants and service contracts. The
bounded `LeanCpOs/Task/Scalar.lean` represents the same operations with UInt64
fields, and exports `lean_osek_step`. The target adapter is compared with the
generic model and independent Python oracle; no refinement proof connects them.

The AArch64 image compiles the **actual generated C** from Scalar.lean using
Lean's packaged Clang and `lean/lean.h`. Function-section garbage collection
removes unused boxed wrappers. The verifier rejects generated closed-value
initialization dependencies, requires the exported Lean entry in the ELF, and
checks that the image has no unresolved symbols. This scalar image does not
link the heap-based general Lean runtime. It does not establish that arbitrary
Lean programs can run freestanding without that runtime.

`target/aarch64/context.S` saves x19–x30 and SP at AAPCS64 call boundaries;
all target C uses `-mgeneral-regs-only`. Each task has its own stack. The C
dispatcher obeys the generated Lean result, preserving interrupted contexts
and replacing successfully terminated/chained activations with fresh entry
contexts. UART traces check registers, local stack data, FIFO, restart, chain,
nonpreemptive scheduling, errors and modeled ISR deferral. Physical IRQ entry,
SIMD/FPU state and asynchronous switching are outside this port.

See [QEMU instructions and precise limits](QEMU.md) and
[the task-control contract](TASK_CONTROL.md). Neither the scalar adapter,
compiler, C pointers, assembly nor hardware behavior is formally refined from
the generic Lean proofs. Host and target tests complement those proofs.

## Original M0 host example

`LeanCpOs/Bridge.lean` exports `lean_cp_step` with three `UInt32` values and a `UInt64` result. `c/bridge.h` fixes the experimental bit layout. Task states/results are not pointer-based AUTOSAR API types. `initialize_LeanCpOs_Bridge` and the Lean runtime initializer run once before calls; C owns and releases the initializer result. Scalar arguments/results have no cross-boundary reference ownership, but the implementation uses Lean objects internally.

The build regenerates `Model.c` and `Bridge.c` using `lake env lean -c`, compiles them with the pinned Lean `leanc` at `-O2 -fstack-usage`, compiles host-only C with GCC, and links the actual generated objects with `leanc` and the packaged runtime. Logs record each command; `report.json` hashes source, generated C, object files, binaries, `.olean` files, headers and tool/runtime binaries.

`runtime.json` counts generated allocation/increment/decrement call sites and retains compiler per-function stack usage. These are code-shape observations, not dynamic call counts or complete path costs. Current generated C contains `lean_alloc_ctor`, `lean_inc` and `lean_dec`. Decrementing an object can trigger cascading reference-count releases in the runtime. No bound for this chain has been proved; no zero-allocation, WCET or total stack bound is claimed. Finite task membership does not by itself establish bounds for the compiler/runtime paths.

The pure transition functions do not share mutable kernel state. This does not establish C/Lean runtime initialization thread safety, allocator interrupt safety, reentrancy or application synchronization. The `control_flow.c` test explicitly uses globals and is not reentrant. IRQ and concurrent entry are outside M0. The separate AArch64 port above uses hand-written context-switch assembly.

Both Lean host execution and compiled C share the Lean compiler/runtime; their agreement is not independent compiler verification. Python's set-based oracle adds an independent behavioral comparison for tested inputs. Encoding correctness, arbitrary UInt32 boundary behavior, compiler preservation, C undefined-behavior freedom, runtime correctness, host OS and hardware remain trusted/tested boundaries.

## Bootstrap-host adaptation

The original bootstrap environment reported virtual PIDs that did not correspond to numeric `/proc/<pid>/exe` entries. Unmodified Lean 4.19.0 therefore failed to locate its executable there. `tools/proc_self_compat.c` supplies an **optional host-only** readlink adapter: only the current process's numeric executable lookup is redirected to `/proc/self/exe`. It does not alter Lean definitions, theorem reduction, the kernel or C generation. The exact adapter binary hash is captured when used. The current cloud environment and normal GitHub runners do not need it. Enable it only if that specific host lookup problem is reproduced.

```sh
gcc -shared -fPIC -O2 tools/proc_self_compat.c -ldl -o /tmp/lean-cp-proc.so
export LD_PRELOAD=/tmp/lean-cp-proc.so
```

The bundled Clang does not find all host libc headers in this environment, so host C is compiled with GCC; generated C compilation and final linking use the pinned Lean tools. No tool binary or runtime proof checker is patched.
