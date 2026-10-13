"""Generate publication pages from the optional proceedings.bib and pubs.bib inputs."""

from datetime import date, datetime
from pathlib import Path
import re
from urllib.parse import quote_plus

from generator_utils import document_name, frontmatter, write_documents

SCRIPT_DIR = Path(__file__).resolve().parent
PUBLIST = {
    "proceeding": {
        "file": "proceedings.bib",
        "venuekey": "booktitle",
        "venue-pretext": "In the proceedings of ",
        "category": "conferences",
        "collection": {"name": "publications", "permalink": "/publication/"},
    },
    "journal": {
        "file": "pubs.bib",
        "venuekey": "journal",
        "venue-pretext": "",
        "category": "manuscripts",
        "collection": {"name": "publications", "permalink": "/publication/"},
    },
}


def clean_text(value):
    return value.replace("{", "").replace("}", "").replace("\\", "")


def publication_date(fields):
    year = int(fields["year"])
    month_text = fields.get("month", "1").strip()
    month = int(month_text) if month_text.isdigit() else datetime.strptime(month_text[:3], "%b").month
    day = int(fields.get("day", "1"))
    return date(year, month, day).isoformat()


def person_name(person):
    parts = person.first_names + person.middle_names + person.prelast_names + person.last_names + person.lineage_names
    return " ".join(parts)


def generate(input_dir=SCRIPT_DIR, output_dir=SCRIPT_DIR.parent / "_publications"):
    input_dir = Path(input_dir)
    sources = []
    for settings in PUBLIST.values():
        source = input_dir / settings["file"]
        if source.is_file():
            sources.append((source, settings))
        else:
            print(f"Skipping missing BibTeX input: {source}")
    if not sources:
        print("Add proceedings.bib or pubs.bib to markdown_generator before running this generator.")
        return 0

    try:
        from pybtex.database.input import bibtex
    except ImportError:
        raise SystemExit("Install pybtex to read BibTeX files: python -m pip install pybtex") from None

    documents = []
    for source, settings in sources:
        bibdata = bibtex.Parser().parse_file(str(source))
        for bib_id, entry in bibdata.entries.items():
            fields = entry.fields
            try:
                title = clean_text(fields["title"])
                published_date = publication_date(fields)
                slug = re.sub(r"[^a-zA-Z0-9_-]", "", title.replace(" ", "-"))
                slug = re.sub("-+", "-", slug).strip("-")
                name = document_name(published_date, slug)
                venue = settings["venue-pretext"] + clean_text(fields[settings["venuekey"]])
                authors = ", ".join(person_name(person) for person in entry.persons["author"])
                if not authors:
                    raise ValueError("author list is empty")
                citation = f'{authors}. "{title}." {venue}, {fields["year"]}.'
                metadata = {
                    "title": title,
                    "collection": settings["collection"]["name"],
                    "category": settings["category"],
                    "permalink": settings["collection"]["permalink"] + name,
                    "date": published_date,
                    "venue": venue,
                    "citation": citation,
                }
                if fields.get("note"):
                    metadata["excerpt"] = fields["note"]
                if fields.get("url"):
                    metadata["paperurl"] = fields["url"]
                body = "\n{{ page.excerpt }}\n" if metadata.get("excerpt") else ""
                if not metadata.get("paperurl"):
                    body += f'\nUse [Google Scholar](https://scholar.google.com/scholar?q={quote_plus(title)}){{:target="_blank" rel="noopener"}} for full citation.\n'
                documents.append((name, frontmatter(metadata) + body))
            except (KeyError, ValueError) as error:
                print(f"Skipping invalid BibTeX entry {bib_id}: {error}")
    return write_documents(output_dir, documents)


if __name__ == "__main__":
    try:
        print(f"Generated {generate()} publication pages.")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from None
