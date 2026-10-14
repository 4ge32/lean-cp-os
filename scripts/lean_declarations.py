"""Inventory named project declarations for the axiom audit and trace map.

Project declarations use named namespaces and one declaration per line. This
inventory is not a Lean parser or proof checker: Lean checks the generated audit.
"""
import pathlib
import re


def declarations(root=pathlib.Path('LeanCpOs')):
    rows = []
    for path in sorted(root.rglob('*.lean')):
        scopes = []
        for line in path.read_text().splitlines():
            opening = re.fullmatch(r'(namespace|section)(?:\s+([\w.]+))?\s*', line)
            if opening:
                scopes.append((opening[1], opening[2]))
                continue
            if re.fullmatch(r'end(?:\s+[\w.]+)?\s*', line):
                if scopes:
                    scopes.pop()
                continue
            decl = re.match(r'^(?:@\[[^\]]+\]\s*)?(def|abbrev|structure|inductive|theorem)\s+([\w.]+)', line)
            if decl:
                prefix = '.'.join(n for kind, n in scopes if kind == 'namespace' and n)
                rows.append(dict(name=(prefix + '.' if prefix else '') + decl[2],
                                 kind=decl[1], file=str(path),
                                 module='.'.join(path.with_suffix('').parts)))
    names = [row['name'] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate declaration names in project inventory')
    return rows


if __name__ == '__main__':
    import sys
    rows = [row for row in declarations() if row['kind'] == 'theorem']
    if not rows:
        raise SystemExit('No theorem declarations found')
    imports = sorted({row['module'] for row in rows})
    pathlib.Path(sys.argv[1]).write_text(
        ''.join('import ' + module + '\n' for module in imports) + '\n' +
        ''.join('#print axioms ' + row['name'] + '\n' for row in rows))
