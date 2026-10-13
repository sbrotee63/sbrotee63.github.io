"""Generate talk pages from talks.tsv; run from any directory."""

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


def generate(input_path=SCRIPT_DIR / "talks.tsv", output_dir=SCRIPT_DIR.parent / "_talks"):
    rows = read_tsv(input_path, ("title", "url_slug", "date"))
    documents = []
    for row in rows:
        talk_date = required(row, "date")
        name = document_name(talk_date, required(row, "url_slug"))
        fields = {
            "title": required(row, "title"),
            "collection": "talks",
            "published": publication_state(row),
            "type": row.get("type") or "Talk",
            "permalink": f"/talks/{name}",
            "date": talk_date,
        }
        for field in ("venue", "location"):
            if row.get(field):
                fields[field] = row[field]
        body = ""
        if row.get("talk_url"):
            body += f"\n[More information here]({row['talk_url']})\n"
        if row.get("description"):
            body += f"\n{row['description']}\n"
        documents.append((name, frontmatter(fields) + body))
    return write_documents(output_dir, documents)


if __name__ == "__main__":
    try:
        print(f"Generated {generate()} talk pages.")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from None
