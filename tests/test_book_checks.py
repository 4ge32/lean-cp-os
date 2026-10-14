#!/usr/bin/env python3
"""Exercise the Book validator with broken content, not just the current Book."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_book.py"
SPEC = importlib.util.spec_from_file_location("check_book", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class BookChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lcpo-book-checks-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "docs/book"
        self.source.mkdir(parents=True)
        self.example = self.root / "examples/book/example.lean"
        self.example.parent.mkdir(parents=True)
        self.example.write_text("#guard (1 : Nat) == 1\n")
        (self.source / "SUMMARY.md").write_text("# Summary\n\n- [Start](intro.md)\n")
        self.chapter = self.source / "intro.md"
        self.chapter.write_text("# Start\n\n```lean\n{{#include ../../examples/book/example.lean}}\n```\n")
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "searchindex.js").write_text("{}")
        (self.site / "index.html").write_text('<h1 id="start">Start</h1><a href="chapter.html#second">Next</a>')
        (self.site / "chapter.html").write_text('<h1 id="second">Second</h1><a href="index.html#start">Start</a>')

    def append_source(self, text):
        with self.chapter.open("a") as file:
            file.write("\n" + text + "\n")

    def append_html(self, text):
        with (self.site / "index.html").open("a") as file:
            file.write(text)

    def test_valid_sources_and_generated_links_pass(self):
        self.append_source("[Example](https://github.com/4ge32/lean-cp-os/blob/main/examples/book/example.lean)")
        self.append_source("[Examples](https://github.com/4ge32/lean-cp-os/tree/main/examples/book)")
        self.append_html('<a href="/lean-cp-os/chapter.html#second">Project root</a>')
        self.append_html('<a href="#start">Same page</a><a href="https://example.org/unfetched">External</a>')
        self.assertEqual(checker.source_errors(self.root), [])
        self.assertEqual(checker.html_errors(self.site), [])

    def test_detects_missing_local_and_repository_links(self):
        self.append_source("[Missing](absent.md)")
        self.append_source("[Missing source](https://github.com/4ge32/lean-cp-os/blob/main/Absent.lean)")
        self.append_source("[Missing directory](https://github.com/4ge32/lean-cp-os/tree/main/absent)")
        errors = "\n".join(checker.source_errors(self.root))
        self.assertIn("broken link absent.md", errors)
        self.assertIn("missing repository path Absent.lean", errors)
        self.assertIn("missing repository path absent", errors)

    def test_rejects_assets_that_replace_mdbook_navigation(self):
        (self.source / "book.js").write_text("// custom code would replace navigation")
        self.assertTrue(any("shadows a generated mdBook asset" in error
                            for error in checker.source_errors(self.root)))

    def test_detects_missing_and_escaping_includes(self):
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("outside the repository")
        self.addCleanup(outside.unlink)
        self.append_source("{{#include missing.txt}}")
        self.append_source("{{#include ../../../" + outside.name + "}}")
        errors = "\n".join(checker.source_errors(self.root))
        self.assertIn("missing/unsafe include missing.txt", errors)
        self.assertIn("missing/unsafe include ../../../", errors)

    def test_requires_summary_coverage_and_executable_example_expectations(self):
        (self.source / "orphan.md").write_text("# Unlisted chapter\n")
        self.example.write_text("#eval 1\n")
        (self.example.parent / "unused.lean").write_text("#guard true\n")
        errors = "\n".join(checker.source_errors(self.root))
        self.assertIn("orphan.md: not listed", errors)
        self.assertIn("example.lean: no executable expectations", errors)
        self.assertIn("unused.lean: not included", errors)

    def test_detects_missing_html_pages_assets_and_anchors(self):
        self.append_html('<a href="missing.html">Missing page</a><img src="missing.svg">')
        self.append_html('<a href="chapter.html#absent">Missing anchor</a><a href="#absent">Same page</a>')
        errors = "\n".join(checker.html_errors(self.site))
        self.assertIn("missing missing.html", errors)
        self.assertIn("missing missing.svg", errors)
        self.assertIn("missing anchor chapter.html#absent", errors)
        self.assertIn("missing anchor #absent", errors)

    def test_only_history_index_is_deferred_until_site_assembly(self):
        self.append_html('<a href="verification/index.html">History</a>')
        self.assertEqual(checker.html_errors(self.site), [])
        self.assertTrue(any("missing verification/index.html" in error
                            for error in checker.html_errors(self.site, complete=True)))
        self.append_html('<a href="verification/missing.html">Not deferred</a>')
        self.assertTrue(any("missing verification/missing.html" in error
                            for error in checker.html_errors(self.site)))

    def test_checks_history_index_using_its_base_url(self):
        history = self.site / "verification"
        history.mkdir()
        (self.site / "latest.json").write_text("{}")
        (history / "index.html").write_text(
            '<base href="../"><h1>History</h1><a href="index.html#start">Book</a>'
            '<a href="latest.json">Latest</a>')
        self.append_html('<a href="verification/index.html">History</a>')
        self.assertEqual(checker.html_errors(self.site, complete=True), [])
        (self.site / "latest.json").unlink()
        self.assertTrue(any("verification/index.html: missing latest.json" in error
                            for error in checker.html_errors(self.site, complete=True)))

    def test_absolute_project_base_resolves_assets_inside_the_site(self):
        (self.site / "404.html").write_text(
            '<base href="/lean-cp-os/"><h1>Not found</h1>'
            '<a href="chapter.html#second">Chapter</a><script src="searchindex.js"></script>')
        self.assertEqual(checker.html_errors(self.site), [])

    def test_normalizes_project_root_links_before_checking_anchors(self):
        (self.site / "nested").mkdir()
        self.append_html('<a href="/lean-cp-os/nested/../chapter.html#absent">Missing anchor</a>')
        self.assertTrue(any("missing anchor" in error for error in checker.html_errors(self.site)))

    def test_detects_site_escape_and_missing_search_index(self):
        self.append_html('<a href="../outside.html">Escaping link</a>')
        (self.site / "searchindex.js").unlink()
        errors = "\n".join(checker.html_errors(self.site))
        self.assertIn("link leaves site", errors)
        self.assertIn("search index is missing", errors)

    @unittest.skipUnless(shutil.which("lake"), "Install pinned Lean to run the real compiler failure test")
    def test_real_lean_failure_makes_the_cli_fail(self):
        # Run the real CLI in a tiny independent Lake package. A previously
        # successful example becomes false without editing the project itself.
        script = self.root / "scripts/check_book.py"
        script.parent.mkdir()
        shutil.copy2(SCRIPT, script)
        (self.root / "lakefile.toml").write_text('name = "book-check-fixture"\nversion = "0.1.0"\n')
        shutil.copy2(ROOT / "lean-toolchain", self.root / "lean-toolchain")
        command = [sys.executable, str(script)]
        valid = subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=120)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        self.example.write_text("#guard (1 : Nat) == 2\n")
        invalid = subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=120)
        self.assertNotEqual(invalid.returncode, 0, invalid.stdout + invalid.stderr)
        self.assertIn("example.lean", invalid.stderr)
        self.assertNotIn("Book links, includes and examples checked", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
