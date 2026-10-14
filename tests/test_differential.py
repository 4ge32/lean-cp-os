#!/usr/bin/env python3
"""Independent array-state oracle; exhausts the finite canonical ABI domain.
Invalid IDs/ops/masks additionally include UINT32_MAX. Both implementations
share the Lean source/compiler/runtime, so differential testing is NOT a proof
of compiler correctness; the Python oracle reduces common-mode blind spots.
"""
import itertools
import json
import pathlib
import subprocess
import sys

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

def oracle(mask, op, ident):
    if mask >= 8:
        return 4 << 8
    active = {i for i in range(3) if mask & (1 << i)}
    current = max(active) if active else None
    status, flow, value = 0, 0, 0
    if op == 0:
        if ident >= 3:
            status = 1
        elif ident in active:
            status = 2
        else:
            active.add(ident)
    elif op == 1:
        if current is None:
            status = 3
        else:
            active.remove(current)
            flow = 1
    elif op == 2:
        value = current + 1 if current is not None else 0
    elif op == 3:
        if ident >= 3:
            status = 1
        else:
            value = 1 if ident not in active else (3 if ident == current else 2)
    else:
        status = 4
    runner = max(active) + 1 if active else 0
    new_mask = sum(1 << i for i in active)
    return new_mask | runner << 4 | status << 8 | flow << 12 | value << 16

# Exhaustive finite operation equivalence classes + scalar boundary samples.
vectors = list(itertools.product(range(8), range(5), [0, 1, 2, 3, 4, 2**32-1]))
vectors += [(m, o, 2**32-1) for m in [8, 255, 2**32-1] for o in range(5)]
vectors += [(m, 2**32-1, 0) for m in range(8)]
# Stateful sequences: each step consumes the preceding oracle state.
sequences = list(itertools.product([(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)], repeat=4))
for sequence in sequences:
    mask = 0
    for op, ident in sequence:
        vectors.append((mask, op, ident))
        mask = oracle(mask, op, ident) & 15
payload = ''.join(f'{m} {o} {i}\n' for m, o, i in vectors)
(OUT / 'vectors.txt').write_text(payload)
expected = [oracle(*v) for v in vectors]
(OUT / 'oracle.txt').write_text(''.join(f'{v}\n' for v in expected))
results = []
for test_id, cmd in [
    ('T-HOST', ['lake', 'env', 'lean', '--run', 'Main.lean']),
    ('T-C-ABI', ['build/c-host']),
]:
    p = subprocess.run(cmd, input=payload, text=True, capture_output=True, timeout=120)
    (OUT / f'{test_id}.stdout').write_text(p.stdout)
    (OUT / f'{test_id}.stderr').write_text(p.stderr)
    try:
        actual = [int(x) for x in p.stdout.splitlines()]
    except ValueError:
        actual = []
    mismatches = [dict(index=i, vector=v, expected=e,
                       actual=actual[i] if i < len(actual) else None)
                  for i, (v, e) in enumerate(zip(vectors, expected))
                  if i >= len(actual) or actual[i] != e]
    ok = p.returncode == 0 and not mismatches and len(actual) == len(expected)
    results.append(dict(id=test_id, status='passed' if ok else 'failed',
                        returncode=p.returncode, cases=len(vectors),
                        mismatches=mismatches[:20], actual_count=len(actual)))
same = (OUT / 'T-HOST.stdout').read_bytes() == (OUT / 'T-C-ABI.stdout').read_bytes()
results.append(dict(id='T-DIFFERENTIAL', status='passed' if same and all(
    r['status'] == 'passed' for r in results) else 'failed', cases=len(vectors)))
summary = dict(canonical_vectors=240, boundary_vectors=23,
               sequences=len(sequences), sequence_length=4, total_vectors=len(vectors), tests=results)
(OUT / 'tests.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
sys.exit(0 if all(r['status'] == 'passed' for r in results) else 1)
