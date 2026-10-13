"""Small, shared helpers for the manual Markdown generators."""

import csv
import json
from datetime import date
from pathlib import Path


def read_tsv(path, required_columns):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        missing = set(required_columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(sorted(missing))}")
        return [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
        ]


def required(row, key):
    value = row.get(key, "").strip()
    if not value:
        raise ValueError(f"A row is missing its required {key} value.")
    return value


def publication_state(row):
    value = row.get("published", "true").strip().lower() or "true"
    if value not in {"true", "false"}:
        raise ValueError("The published column must be true or false.")
    return value == "true"


def document_name(date_text, slug):
    date.fromisoformat(date_text)
    if not slug or any(character in slug for character in '/\\') or slug in {".", ".."}:
        raise ValueError("url_slug must be a non-empty filename component.")
    return f"{date_text}-{slug}"


def frontmatter(fields):
    # JSON scalars are valid YAML and preserve quotes, Unicode, and line breaks.
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()]
    return "---\n" + "\n".join(lines) + "\n---\n"


def write_documents(output_dir, documents):
    output_dir = Path(output_dir)
    names = [name for name, _ in documents]
    if len(names) != len(set(names)):
        raise ValueError("Input rows have duplicate date/url_slug combinations.")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in documents:
        (output_dir / f"{name}.md").write_text(content, encoding="utf-8")
    return len(documents)
