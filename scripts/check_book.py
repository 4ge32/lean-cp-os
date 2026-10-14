#!/usr/bin/env python3
"""Check Book source links/includes, runnable Lean examples and generated links.

The published verification index is supplied by assemble_site.py, so the one
deferred link is allowed in a standalone Book build. Pass --complete-site when
checking an assembled publication. External URLs are not fetched.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/book'
REPO_PREFIX = 'https://github.com/4ge32/lean-cp-os/blob/main/'
TREE_PREFIX = 'https://github.com/4ge32/lean-cp-os/tree/main/'
LINK = re.compile(r'!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
INCLUDE = re.compile(r'\{\{#include\s+([^}\s]+)\s*\}\}')
EXAMPLE_INCLUDE = re.compile(r'\{\{#include\s+([^}\s]+\.lean)\s*\}\}')
GENERATED_ASSETS = {'book.js', 'searcher.js', 'searchindex.js', 'searchindex.json',
                    'elasticlunr.min.js', 'toc.js', 'toc.html', 'index.html',
                    'print.html', '404.html'}


def beneath(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def source_errors(root=ROOT):
    source = root / 'docs/book'
    errors = []
    included_examples = set()
    for name in sorted(GENERATED_ASSETS):
        if (source / name).exists():
            errors.append(f'docs/book/{name}: shadows a generated mdBook asset; use assets/')
    summary = source / 'SUMMARY.md'
    if not summary.is_file():
        return ['Missing docs/book/SUMMARY.md']
    listed = set()
    for target in LINK.findall(summary.read_text()):
        listed.add((source / unquote(urlsplit(target).path)).resolve())
    for page in sorted(source.rglob('*.md')):
        text = page.read_text()
        if page.name != 'SUMMARY.md' and page.resolve() not in listed:
            errors.append(f'{page.relative_to(root)}: not listed in SUMMARY.md')
        for include in INCLUDE.findall(text):
            # mdBook supports line/anchor selectors after the file name.
            target = (page.parent / include.split(':', 1)[0]).resolve()
            if not beneath(target, root) or not target.is_file():
                errors.append(f'{page.relative_to(root)}: missing/unsafe include {include}')
        for include in EXAMPLE_INCLUDE.findall(text):
            included_examples.add((page.parent / include).resolve())
        for raw in LINK.findall(text):
            parts = urlsplit(raw)
            if raw.startswith(REPO_PREFIX) or raw.startswith(TREE_PREFIX):
                prefix = REPO_PREFIX if raw.startswith(REPO_PREFIX) else TREE_PREFIX
                relative = unquote(urlsplit(raw[len(prefix):]).path)
                target = root / relative
                if not beneath(target, root) or not target.exists():
                    errors.append(f'{page.relative_to(root)}: missing repository path {relative}')
            elif not parts.scheme and not parts.netloc and parts.path:
                path = unquote(parts.path)
                if path == 'verification/index.html':
                    continue
                target = (page.parent / path).resolve()
                if not beneath(target, root) or not target.exists():
                    errors.append(f'{page.relative_to(root)}: broken link {raw}')
    examples = set((root / 'examples/book').glob('*.lean'))
    if not examples:
        errors.append('No runnable Book examples found')
    for example in sorted(examples):
        if example.resolve() not in included_examples:
            errors.append(f'{example.relative_to(root)}: not included in the Book')
        if '#guard' not in example.read_text():
            errors.append(f'{example.relative_to(root)}: no executable expectations (#guard)')
    return errors


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.base = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'base':
            self.base = attrs.get('href')
        else:
            for attr in ('href', 'src'):
                if attrs.get(attr):
                    self.links.append(attrs[attr])


def html_errors(directory, complete=False):
    directory = directory.resolve()
    errors = []
    pages = {}
    if not (directory / 'index.html').is_file():
        return [f'{directory}: missing index.html']
    if not (directory / 'searchindex.js').is_file() and not (directory / 'searchindex.json').is_file():
        errors.append('Book search index is missing')
    # Historical reports contain independently generated links; their immutable
    # bytes and locations are tested by test_book_site.py. Check Book navigation.
    for file in sorted(directory.rglob('*.html')):
        relative = file.relative_to(directory)
        if relative.parts[0] in ('commits', 'runs'):
            continue
        pages[file] = Page(file.read_text())
    for file, page in pages.items():
        base = file.parent
        if page.base:
            parsed_base = urlsplit(page.base)
            if parsed_base.scheme or parsed_base.netloc:
                continue
            if parsed_base.path.startswith('/lean-cp-os/'):
                base = directory / parsed_base.path[len('/lean-cp-os/'):]
            elif parsed_base.path.startswith('/'):
                base = directory / parsed_base.path.lstrip('/')
            else:
                base = (base / parsed_base.path).resolve()
        for raw in page.links:
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                continue
            path = unquote(parts.path)
            if path.startswith('/lean-cp-os/'):
                target = directory / path[len('/lean-cp-os/'):]
            elif path.startswith('/'):
                target = directory / path.lstrip('/')
            else:
                target = (base / path).resolve() if path else file
            if path.endswith('/') or target.is_dir():
                target = target / 'index.html'
            target = target.resolve()
            if not beneath(target, directory):
                errors.append(f'{file.relative_to(directory)}: link leaves site: {raw}')
                continue
            if not complete and target == directory / 'verification/index.html':
                continue
            if not target.exists():
                errors.append(f'{file.relative_to(directory)}: missing {raw}')
                continue
            fragment = unquote(parts.fragment)
            if fragment and target.suffix == '.html' and target in pages and fragment not in pages[target].ids:
                errors.append(f'{file.relative_to(directory)}: missing anchor {raw}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-examples', action='store_true', help='Skip execution, for an unchanged build already checked')
    parser.add_argument('--html', type=Path, help='Check links/assets/anchors in a generated Book')
    parser.add_argument('--complete-site', action='store_true', help='Require the published verification index too')
    args = parser.parse_args()
    errors = source_errors()
    if args.html:
        errors.extend(html_errors(args.html, args.complete_site))
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    if not args.skip_examples:
        for example in sorted((ROOT / 'examples/book').glob('*.lean')):
            command = ['lake', 'env', 'lean', str(example.relative_to(ROOT))]
            try:
                result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
            except (FileNotFoundError, subprocess.TimeoutExpired) as error:
                print(f'{example.name}: {error}; run lake build with the pinned Lean toolchain first', file=sys.stderr)
                return 1
            if result.returncode:
                print(result.stdout + result.stderr, file=sys.stderr)
                return result.returncode
            print(f'PASS {example.relative_to(ROOT)}')
    print('Book links, includes' + (', HTML' if args.html else '') + (' and examples' if not args.skip_examples else '') + ' checked.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
