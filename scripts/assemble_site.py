#!/usr/bin/env python3
"""Combine an immutable history export and a fresh mdBook build for Pages.

Usage: assemble_site.py HISTORY BOOK OUTPUT

Run this *after* publish_history.py has pushed evidence-history. Neither input
is modified; OUTPUT must not exist. Book assets never enter the history branch.
"""

import argparse
from pathlib import Path
import re
import shutil
import tempfile


RESERVED = {"commits", "runs", "latest.json", "verification", ".git"}
REPLACED = {"index.html", ".nojekyll"}


def validate_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Expected a real input directory: {root}")
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Refusing non-regular input: {path}")
        if path.name == ".git":
            raise ValueError(f"Refusing Git metadata in Pages input: {path}")


def history_page(document: str) -> str:
    # The archive index uses root-relative-to-document links. A base preserves
    # their URLs when this page moves down into verification/.
    if re.search(r"<base\b", document, re.IGNORECASE):
        raise ValueError("History index already contains a base element")
    base = '<base href="../">'
    head = re.search(r"<head(?:\s[^>]*)?>", document, re.IGNORECASE)
    doctype = re.search(r"<!doctype[^>]*>", document, re.IGNORECASE)
    offset = head.end() if head else doctype.end() if doctype else 0
    document = document[:offset] + base + document[offset:]
    heading = re.search(r"<h1\b", document, re.IGNORECASE)
    if heading is None:
        raise ValueError("History index has no main heading")
    navigation = ('<nav aria-label="Book"><a href="index.html">'
                  '← Lean CP OS Book</a></nav>')
    return document[:heading.start()] + navigation + document[heading.start():]


def assemble(history: Path, book: Path, output: Path) -> None:
    validate_tree(history)
    validate_tree(book)
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists; refusing stale assets: {output}")
    history, book, output = history.resolve(), book.resolve(), output.resolve()
    paths = (history, book, output)
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError("History, Book and output directories must be separate")
    for path in (history / "index.html", history / "latest.json", book / "index.html"):
        if not path.is_file():
            raise ValueError(f"Required input is missing: {path}")
    if (history / "verification").exists():
        raise ValueError("History already contains the reserved verification directory")
    for entry in book.iterdir():
        if entry.name in RESERVED:
            raise ValueError(f"Book uses a reserved history path: {entry.name}")
        if (history / entry.name).exists() and entry.name not in REPLACED:
            raise ValueError(f"Book/history path collision: {entry.name}")
        if entry.name in REPLACED and not entry.is_file():
            raise ValueError(f"Expected a regular Book file: {entry}")
    relocated = history_page((history / "index.html").read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    # A failed copy leaves the archive, Book and final output untouched. Build
    # beside the destination so the final rename stays on the same filesystem.
    with tempfile.TemporaryDirectory(prefix=".assemble-site-", dir=output.parent) as tmp:
        staged = Path(tmp) / "site"
        shutil.copytree(history, staged)
        (staged / "verification").mkdir()
        (staged / "verification/index.html").write_text(relocated, encoding="utf-8")
        for entry in book.iterdir():
            target = staged / entry.name
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
        (staged / ".nojekyll").write_text("", encoding="utf-8")
        if output.exists():
            raise ValueError(f"Output appeared during assembly: {output}")
        staged.rename(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("history", type=Path)
    parser.add_argument("book", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        assemble(args.history, args.book, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Site assembly failed: {error}\n")
    print(f"Book and verification history assembled in {args.output}")


if __name__ == "__main__":
    main()
