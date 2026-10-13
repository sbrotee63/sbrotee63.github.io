"""Generate publication pages from publications.tsv; run from any directory."""

from pathlib import Path

from generator_utils import (
    document_name,
    frontmatter,
    publication_state,
    read_tsv,
    required,
    write_documents,
)

SCRIPT_DIR = Path(__file__).resolve().parent


def generate(input_path=SCRIPT_DIR / "publications.tsv", output_dir=SCRIPT_DIR.parent / "_publications"):
    rows = read_tsv(input_path, ("pub_date", "title", "venue", "citation", "url_slug"))
    documents = []
    for row in rows:
        published_date = required(row, "pub_date")
        name = document_name(published_date, required(row, "url_slug"))
        fields = {
            "title": required(row, "title"),
            "collection": "publications",
            "category": row.get("category") or "uncategorized",
            "published": publication_state(row),
            "permalink": f"/publication/{name}",
            "date": published_date,
            "venue": required(row, "venue"),
            "citation": required(row, "citation"),
        }
        for column, field in (("excerpt", "excerpt"), ("paper_url", "paperurl"), ("slides_url", "slidesurl")):
            if row.get(column):
                fields[field] = row[column]
        # The shared layout renders citation/download links once. Keep one abstract.
        body = "\n{{ page.excerpt }}\n" if fields.get("excerpt") else ""
        documents.append((name, frontmatter(fields) + body))
    return write_documents(output_dir, documents)


if __name__ == "__main__":
    try:
        print(f"Generated {generate()} publication pages.")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from None
