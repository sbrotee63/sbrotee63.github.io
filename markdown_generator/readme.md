# Markdown generators

These manual helpers write Markdown pages into the site's collections. They are not run by Jekyll. Run them from any directory with Python 3; the input paths are resolved relative to the scripts:

```text
python markdown_generator/publications.py
python markdown_generator/talks.py
python markdown_generator/pubsFromBib.py
```

The matching notebooks call the same scripts, so both entry points behave identically. The TSV generators use Python's standard library. The BibTeX generator additionally requires `pybtex`.

**Files with matching generated names are overwritten.** Replace the example input rows with real content before using these as your source of truth. The bundled TSV rows have `published: false` so running them does not publish template examples.

## Publication TSV

Required columns with non-empty values: `pub_date`, `title`, `venue`, `citation`, `url_slug`.

Optional columns: `excerpt`, `paper_url`, `slides_url`, `category`, `published`.

- Dates use `YYYY-MM-DD`.
- Each date and URL slug combination must be unique.
- Use the configured category keys: `books`, `manuscripts` (journal articles), or `conferences`. Blank categories become `uncategorized`, displayed under Other Publications.
- `published` accepts `true` or `false`; blank or omitted means true.
- Titles and other strings are escaped as YAML without changing quotes, Unicode, or HTML.
- Output uses `/publication/YYYY-MM-DD-url_slug`. The page layout displays citation and downloads; the excerpt is stored once.

## Talk TSV

Required columns with non-empty values: `title`, `url_slug`, `date`.

Optional columns: `type`, `venue`, `location`, `talk_url`, `description`, `published`.

The type defaults to Talk. A date is always emitted, including when the optional location is blank. Publication flags and date/slug uniqueness follow the rules above.

## BibTeX

Put `proceedings.bib` and/or `pubs.bib` beside `pubsFromBib.py`. Missing input files are reported and skipped. Proceedings use `booktitle` and the `conferences` category; journal entries use `journal` and `manuscripts`.

Entries require title, year, the appropriate venue field, and authors. Month/day default to January 1 when omitted. Numeric or abbreviated month names are supported. Invalid entries are reported and skipped.

For the optional talk map, see the repository-root `talkmap.ipynb`.

## Regression checks

Install the test-only dependencies with `python -m pip install PyYAML pybtex`, then run `python markdown_generator/test_generators.py` from the repository root. Tests use disposable directories and do not overwrite site content or contact the geocoding service.
