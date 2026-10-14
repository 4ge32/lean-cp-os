#!/usr/bin/env python3
import json,pathlib,re,sys
out=pathlib.Path(sys.argv[1]); rows=[]
for p in pathlib.Path('build').glob('*.c'):
    text=p.read_text()
    rows.append(dict(file=str(p),alloc_ctor=len(re.findall(r'\blean_alloc_ctor\(',text)),inc=len(re.findall(r'\blean_inc(?:_ref)?\(',text)),dec=len(re.findall(r'\blean_dec(?:_ref)?\(',text))))
frames=[]
for p in pathlib.Path('build').glob('*.su'):
    for line in p.read_text().splitlines():
        fields=line.split('\t')
        if len(fields)>=3:
            frames.append(dict(function=fields[0],bytes=int(fields[1]),kind=fields[2]))
result=dict(generated_source_counts=rows,stack_frames=frames,stack_claim='Compiler per-function frame estimates only; excludes runtime and call-chain maximum. No WCET/stack-bound proof.',allocation='M0/general host code uses Lean runtime allocations. Whole-module source counts may include unreachable boxed wrappers. The bounded QEMU scalar image links without heap/runtime symbols; see qemu/symbols.txt and qemu/qemu.json. No allocation claim for general Lean code.',reentrancy='Single-core serialized service boundary. Modeled ISR nesting defers dispatch; physical interrupt entry, concurrent entry and allocator IRQ safety are not implemented or proved.')
(out/'runtime.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='stack_frames'},indent=2))
