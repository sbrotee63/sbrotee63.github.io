"""Regression checks for the manual generators. Requires PyYAML and pybtex."""

import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import unittest
import uuid

import yaml

import publications
import pubsFromBib
import talks

ROOT = Path(__file__).resolve().parent.parent
map_spec = importlib.util.spec_from_file_location("talkmap_helper", ROOT / "talkmap.py")
talkmap_helper = importlib.util.module_from_spec(map_spec)
map_spec.loader.exec_module(talkmap_helper)


def read_page(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def tsv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


class GeneratorRegressionTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "markdown_generator" / (".test-" + uuid.uuid4().hex)
        self.root.mkdir()

    def tearDown(self):
        # Keep recursive cleanup confined to the disposable directory we created.
        self.assertEqual(self.root.resolve().parent, (ROOT / "markdown_generator").resolve())
        self.assertTrue(self.root.name.startswith(".test-"))
        shutil.rmtree(self.root)

    def test_publication_preserves_slides_quotes_unicode_short_fields_and_category_fallback(self):
        source = self.root / "publications.tsv"
        row = {
            "pub_date": "2026-10-12", "title": 'A "quoted" বাংলা paper',
            "venue": "J", "citation": "O'Neil & Brotee", "url_slug": "paper",
            "excerpt": "X", "paper_url": "https://example.org/paper.pdf",
            "slides_url": "https://example.org/slides.pdf", "category": "", "published": "false",
        }
        tsv(source, [row])
        output = self.root / "out"
        self.assertEqual(publications.generate(source, output), 1)
        page_path = output / "2026-10-12-paper.md"
        page = read_page(page_path)
        self.assertEqual(page["title"], row["title"])
        self.assertEqual(page["citation"], row["citation"])
        self.assertEqual(page["excerpt"], "X")
        self.assertEqual(page["slidesurl"], row["slides_url"])
        self.assertEqual(page["paperurl"], row["paper_url"])
        self.assertEqual(page["category"], "uncategorized")
        self.assertFalse(page["published"])
        self.assertIn("{{ page.excerpt }}", page_path.read_text(encoding="utf-8"))

    def test_talk_date_does_not_depend_on_location(self):
        source = self.root / "talks.tsv"
        tsv(source, [{"title": 'A "talk"', "url_slug": "talk", "date": "2026-10-12",
                      "location": "", "type": "", "description": "A short talk."}])
        output = self.root / "out"
        talks.generate(source, output)
        page = read_page(output / "2026-10-12-talk.md")
        self.assertEqual(page["date"], "2026-10-12")
        self.assertEqual(page["type"], "Talk")
        self.assertNotIn("location", page)
        self.assertTrue(page["published"])

    def test_bundled_examples_stay_unpublished(self):
        for module, count, filename in [(publications, 3, "publications.tsv"), (talks, 4, "talks.tsv")]:
            output = self.root / filename
            self.assertEqual(module.generate(ROOT / "markdown_generator" / filename, output), count)
            self.assertTrue(all(read_page(path)["published"] is False for path in output.glob("*.md")))

    def test_missing_inputs_report_clear_results(self):
        with self.assertRaisesRegex(FileNotFoundError, "Input file not found"):
            publications.generate(self.root / "absent.tsv", self.root / "out")
        with contextlib.redirect_stdout(io.StringIO()) as messages:
            self.assertEqual(pubsFromBib.generate(self.root, self.root / "out"), 0)
        self.assertIn("Add proceedings.bib or pubs.bib", messages.getvalue())
        self.assertFalse((self.root / "out").exists())

    def test_duplicate_rows_are_rejected_before_writing(self):
        source = self.root / "talks.tsv"
        row = {"title": "Talk", "url_slug": "same", "date": "2026-10-12"}
        tsv(source, [row, row])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            talks.generate(source, self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_bibtex_categories_dates_and_complete_author_names(self):
        (self.root / "pubs.bib").write_text(
            '@article{journal, title={A {Graph} Paper}, author={Brotee, Shamyo and van Doe, Jane Mary}, '
            'year={2026}, month={12}, day={3}, journal={Journal One}, url={https://example.org/paper}}',
            encoding="utf-8",
        )
        (self.root / "proceedings.bib").write_text(
            '@inproceedings{conference, title={A Conference Paper}, author={Brotee, Shamyo}, '
            'year={2025}, month={Sep}, booktitle={Conference One}}',
            encoding="utf-8",
        )
        output = self.root / "out"
        self.assertEqual(pubsFromBib.generate(self.root, output), 2)
        journal = read_page(output / "2026-12-03-A-Graph-Paper.md")
        conference = read_page(output / "2025-09-01-A-Conference-Paper.md")
        self.assertEqual(journal["category"], "manuscripts")
        self.assertEqual(conference["category"], "conferences")
        self.assertIn("Jane Mary van Doe", journal["citation"])
        self.assertEqual(journal["paperurl"], "https://example.org/paper")
        self.assertIn("https://scholar.google.com/scholar?q=A+Conference+Paper", (output / "2025-09-01-A-Conference-Paper.md").read_text(encoding="utf-8"))

    def test_notebook_and_script_outputs_match_from_repository_root(self):
        generator_dir = self.root / "markdown_generator"
        generator_dir.mkdir()
        for name in ("generator_utils.py", "publications.py", "talks.py", "publications.tsv", "talks.tsv"):
            shutil.copy2(ROOT / "markdown_generator" / name, generator_dir / name)
        previous_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            for notebook_name, module, input_name, collection in [
                ("publications.ipynb", publications, "publications.tsv", "_publications"),
                ("talks.ipynb", talks, "talks.tsv", "_talks"),
            ]:
                notebook = json.loads((ROOT / "markdown_generator" / notebook_name).read_text(encoding="utf-8"))
                with contextlib.redirect_stdout(io.StringIO()):
                    for cell in notebook["cells"]:
                        if cell["cell_type"] == "code":
                            exec("".join(cell["source"]), {})
                direct_output = self.root / ("expected-" + collection)
                module.generate(generator_dir / input_name, direct_output)
                actual = {path.name: path.read_text(encoding="utf-8") for path in (self.root / collection).glob("*.md")}
                expected = {path.name: path.read_text(encoding="utf-8") for path in direct_output.glob("*.md")}
                self.assertEqual(actual, expected)
        finally:
            os.chdir(previous_cwd)

    def test_map_reads_yaml_and_skips_missing_or_unpublished_locations(self):
        fixtures = {
            "one.md": "---\nlocation: 'San Marcos, Texas'\n---\n",
            "two.md": "---\ntitle: No location\n---\n",
            "three.md": '---\nlocation: "London"\npublished: false\n---\n',
            "four.md": "---\nlocation: San Marcos, Texas\n---\n",
        }
        for filename, text in fixtures.items():
            (self.root / filename).write_text(text, encoding="utf-8")
        self.assertEqual(talkmap_helper.load_locations(self.root), ["San Marcos, Texas"])

    def test_bundled_map_has_no_published_locations(self):
        with contextlib.redirect_stdout(io.StringIO()) as messages:
            self.assertEqual(talkmap_helper.generate(ROOT / "_talks", self.root / "out"), 0)
        self.assertIn("No published talks", messages.getvalue())
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
