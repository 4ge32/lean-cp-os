#!/usr/bin/env python3
"""Generate Lean scheduler C, cross-link a freestanding AArch64 image, boot QEMU.

Usage: python3 scripts/verify_qemu.py OUT_DIRECTORY
No runtime scheduler is reimplemented in C: target runtime uses lean_osek_step.
Missing tools are failures (never a passing skip). Artifacts include the ELF,
actual generated source, build log, UART log, tool versions, and SHA-256 hashes.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'build/qemu').resolve()
OUT.mkdir(parents=True, exist_ok=True)
report = {'id': 'T-QEMU-TASK', 'status': 'failed', 'scenarios': 7,
          'platform': 'AArch64 QEMU virt / cortex-a53 / single core',
          'limitations': ['bounded scalar adapter: 4 tasks, 8 activation frames, priority 0..15',
                          'adapter/model correspondence tested, not formally proved',
                          'AAPCS64 call-boundary switching; no hardware IRQ or SIMD/FPU state',
                          'no compiler, assembly, runtime or machine refinement proof'],
          'commands': []}


def command(args, timeout=90):
    args = list(map(str, args))
    report['commands'].append(args)
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout)
    with (OUT / 'build.log').open('a') as log:
        log.write('$ ' + ' '.join(args) + '\n' + proc.stdout)
    if proc.returncode:
        raise RuntimeError(f'command failed ({proc.returncode}): {args[0]}\n{proc.stdout}')
    return proc.stdout


try:
    (OUT / 'build.log').write_text('')
    prefix = pathlib.Path(command(['lean', '--print-prefix']).strip())
    clang = os.environ.get('LEAN_CLANG', str(prefix / 'bin/clang'))
    lld = os.environ.get('LEAN_LLD', str(prefix / 'bin/ld.lld'))
    qemu = os.environ.get('QEMU_SYSTEM_AARCH64') or shutil.which('qemu-system-aarch64')
    if not qemu:
        local = pathlib.Path('/workspace/qemu-tools/bin/qemu-system-aarch64')
        qemu = str(local) if local.is_file() else None
    if not qemu:
        raise RuntimeError('qemu-system-aarch64 missing: install qemu-system-arm or run scripts/bootstrap_qemu.sh')
    report['tools'] = {name: command([tool, '--version']).splitlines()[0]
                       for name, tool in [('lean', 'lean'), ('clang', clang), ('lld', lld), ('qemu', qemu)]}
    generated = OUT / 'TaskScalar.c'
    command(['lake', 'env', 'lean', '-c', generated, 'LeanCpOs/Task/Scalar.lean'])
    # Pure UInt64 code must not acquire module initialization dependencies.
    if '___closed__' in generated.read_text():
        raise RuntimeError('scalar source now requires generated closed-value initialization; revisit target boundary')
    flags = [clang, '--target=aarch64-none-elf', '-mcpu=cortex-a53', '-mgeneral-regs-only',
             '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables', '-ffunction-sections', '-fdata-sections',
             '-DNDEBUG', '-O2', '-g', '-isystem', prefix / 'include/clang',
             '-I' + str(prefix / 'include'), '-Itarget/aarch64']
    objects = []
    for source in [generated, ROOT / 'target/aarch64/runtime.c', ROOT / 'target/aarch64/tests.c',
                   ROOT / 'target/aarch64/boot.S', ROOT / 'target/aarch64/context.S']:
        obj = OUT / (source.stem + '.o')
        warning_flags = ['-Wall', '-Wextra', '-Werror'] if source != generated else []
        command(flags + warning_flags + ['-c', source, '-o', obj])
        objects.append(obj)
    elf = OUT / 'osek-task.elf'
    command([lld, '-T', ROOT / 'target/aarch64/link.ld', '--gc-sections',
             '-Map=' + str(OUT / 'osek-task.map'), '-o', elf] + objects)
    symbols = command(['nm', str(elf)])
    (OUT / 'symbols.txt').write_text(symbols)
    if ' lean_osek_step' not in symbols or command(['nm', '-u', elf]).strip():
        raise RuntimeError('target must contain generated entry and have no unresolved runtime symbols')
    argv = [qemu, '-machine', 'virt,virtualization=off', '-cpu', 'cortex-a53',
            '-smp', '1', '-m', '128M', '-nographic', '-monitor', 'none', '-nic', 'none',
            '-semihosting-config', 'enable=on,target=native', '-kernel', str(elf)]
    report['commands'].append(argv)
    run = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, timeout=20)
    (OUT / 'uart.log').write_text(run.stdout)
    report['returncode'] = run.returncode
    expected = {
        'preempt-resume-registers-stack': [10, 20, 30, 11],
        'equal-priority-fifo': [10, 40, 11, 20, 30],
        'queued-activations-fresh-entry': [11, 20, 12, 13],
        'chain-self-other-nonreturn': [10, 20, 11, 21],
        'nonpreemptive-explicit-schedule': [10, 11, 12, 20, 30, 13],
        'errors-return-with-state-intact': [10],
        'modeled-isr-defers-dispatch': [10, 11, 12, 20, 13],
    }
    report['checks'] = []
    for name, events in expected.items():
        trace = f'TRACE {name}: ' + ' '.join(map(str, events))
        passed = trace in run.stdout.splitlines() and f'PASS {name}' in run.stdout.splitlines()
        report['checks'].append({'name': name, 'status': 'passed' if passed else 'failed', 'trace': events})
    if run.returncode or 'PASS QEMU: 7 scenarios;' not in run.stdout or any(
            check['status'] != 'passed' for check in report['checks']):
        raise RuntimeError('QEMU did not pass every target scenario\n' + run.stdout)
    report['status'] = 'passed'
    print(run.stdout, end='')
except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
    report['error'] = str(exc)
    if isinstance(exc, subprocess.TimeoutExpired):
        partial = exc.stdout or b''
        (OUT / 'timeout.log').write_text(partial.decode(errors='replace') if isinstance(partial, bytes) else partial)
    print('FAIL T-QEMU-TASK: ' + str(exc))
finally:
    report['sha256'] = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'qemu.json'}
    (OUT / 'qemu.json').write_text(json.dumps(report, indent=2) + '\n')
sys.exit(0 if report['status'] == 'passed' else 1)
