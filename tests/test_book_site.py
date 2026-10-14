#!/usr/bin/env python3
"""Check URL preservation and all-or-nothing assembly of the published site."""

from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("assemble_site", ROOT / "scripts/assemble_site.py")
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.base = ""
        self.hrefs = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base":
            self.base = attrs["href"]
        elif tag == "a":
            self.hrefs.append(attrs["href"])


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class SiteAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lcpo-book-site-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.history = self.root / "history"
        self.book = self.root / "book"
        self.output = self.root / "published-site"
        files = {
            "index.html": '<!doctype html><meta charset="utf-8"><title>History</title>'
                          '<h1>History</h1><a href="latest.json">Latest</a>'
                          '<a href="commits/abc/runs/1-1/index.html">Evidence</a>',
            "latest.json": '{"path":"commits/abc/runs/1-1/index.html"}\n',
            "runs/1-1/targets.json": '{"targets":["abc"]}\n',
            "commits/abc/runs/1-1/index.html": '<h1>Failed verification</h1>',
            "commits/abc/runs/1-1/compile.stderr": "a failed run is still published\n",
            ".nojekyll": "",
        }
        for name, text in files.items():
            path = self.history / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.book / "theme").mkdir(parents=True)
        (self.book / "index.html").write_text('<h1>Book</h1><a href="verification/index.html">History</a>')
        (self.book / "theme/book.css").write_text("body { color: black; }")
        self.before_history = snapshot(self.history)
        self.before_book = snapshot(self.book)

    def assemble(self):
        site.assemble(self.history, self.book, self.output)

    def test_keeps_historical_urls_and_moves_only_the_index(self):
        self.assemble()
        for name, content in self.before_history.items():
            if name != "index.html":
                self.assertEqual((self.output / name).read_bytes(), content, name)
        self.assertEqual((self.output / "index.html").read_bytes(), self.before_book["index.html"])
        self.assertEqual(snapshot(self.history), self.before_history)
        self.assertEqual(snapshot(self.book), self.before_book)
        links = Links((self.output / "verification/index.html").read_text())
        self.assertEqual(links.base, "../")
        base = urljoin("https://example.org/lean-cp-os/verification/index.html", links.base)
        self.assertIn("index.html", links.hrefs)
        self.assertIn("commits/abc/runs/1-1/index.html", links.hrefs)
        for href in links.hrefs:
            relative = urlparse(urljoin(base, href)).path.removeprefix("/lean-cp-os/")
            self.assertTrue((self.output / relative).is_file(), relative)

    def test_rejects_reserved_book_paths_without_changing_history(self):
        for name in ("commits", "runs", "latest.json", "verification"):
            with self.subTest(name=name):
                path = self.book / name
                path.write_text("would overwrite history")
                with self.assertRaisesRegex(ValueError, "reserved"):
                    self.assemble()
                self.assertFalse(self.output.exists())
                self.assertEqual(snapshot(self.history), self.before_history)
                path.unlink()

    def test_rejects_unexpected_archive_asset_collision(self):
        (self.history / "theme").mkdir()
        with self.assertRaisesRegex(ValueError, "collision"):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_rejects_reusing_output_and_fresh_build_has_no_old_assets(self):
        (self.book / "removed-chapter.html").write_text("old chapter")
        self.assemble()
        original = snapshot(self.output)
        (self.book / "removed-chapter.html").unlink()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.assemble()
        self.assertEqual(snapshot(self.output), original)
        next_output = self.root / "next-site"
        site.assemble(self.history, self.book, next_output)
        self.assertFalse((next_output / "removed-chapter.html").exists())
        self.assertTrue((next_output / "commits/abc/runs/1-1/index.html").is_file())

    def test_copy_failure_never_exposes_a_partial_site(self):
        copytree = shutil.copytree

        def fail_on_theme(source, destination, *args, **kwargs):
            if Path(source).name == "theme":
                raise OSError("simulated full disk")
            return copytree(source, destination, *args, **kwargs)

        with patch.object(site.shutil, "copytree", side_effect=fail_on_theme):
            with self.assertRaisesRegex(OSError, "full disk"):
                self.assemble()
        self.assertFalse(self.output.exists())
        self.assertEqual(snapshot(self.history), self.before_history)
        self.assertEqual(snapshot(self.book), self.before_book)
        self.assertEqual(list(self.root.glob(".assemble-site-*")), [])

    def test_rejects_git_metadata_and_symlinks(self):
        metadata = self.history / ".git"
        metadata.mkdir()
        with self.assertRaisesRegex(ValueError, "Git metadata"):
            self.assemble()
        metadata.rmdir()
        (self.book / "outside").symlink_to(self.history / "latest.json")
        with self.assertRaisesRegex(ValueError, "non-regular"):
            self.assemble()
        self.assertFalse(self.output.exists())

    def test_invalid_input_does_not_modify_sources(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            site.assemble(self.history, self.book, self.history / "output")
        (self.book / "index.html").unlink()
        with self.assertRaisesRegex(ValueError, "Required input"):
            self.assemble()
        self.assertFalse(self.output.exists())
        self.assertEqual(snapshot(self.history), self.before_history)


if __name__ == "__main__":
    unittest.main()
