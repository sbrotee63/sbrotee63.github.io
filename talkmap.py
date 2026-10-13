"""Rebuild the optional talk map from published talks, regardless of working directory.

Install PyYAML, geopy, and getorg before using this manual helper.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_locations(talks_dir):
    try:
        import yaml
    except ImportError:
        raise SystemExit("Install PyYAML to read talk metadata: python -m pip install PyYAML") from None
    locations = set()
    for source in sorted(Path(talks_dir).glob("*.md")):
        text = source.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        metadata = yaml.safe_load(parts[1]) or {}
        if metadata.get("published") is False:
            continue
        location = metadata.get("location")
        if isinstance(location, str) and location.strip():
            locations.add(location.strip())
    return sorted(locations)


def generate(talks_dir=ROOT / "_talks", output_dir=ROOT / "talkmap"):
    locations = load_locations(talks_dir)
    if not locations:
        print("No published talks with locations; the map was not regenerated.")
        return 0
    try:
        import getorg
        from geopy import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
    except ImportError:
        raise SystemExit("Install map dependencies: python -m pip install geopy getorg") from None

    geocode = RateLimiter(
        Nominatim(user_agent="sbrotee63.github.io-talkmap", timeout=10).geocode,
        min_delay_seconds=1,
    )
    location_dict = {}
    for location in locations:
        result = geocode(location)
        if result is None:
            print(f"No coordinates found for {location}; skipping.")
            continue
        location_dict[location] = result
    if not location_dict:
        print("No coordinates found; the map was not regenerated.")
        return 0

    output_dir = Path(output_dir)
    getorg.orgmap.output_html_cluster_map(
        location_dict, folder_name=str(output_dir), hashed_usernames=False
    )
    map_path = output_dir / "map.html"
    text = map_path.read_text(encoding="utf-8")
    text = text.replace("http://server.arcgisonline.com/", "https://server.arcgisonline.com/")
    text = text.replace("<title>Leaflet debug page</title>", "<title>Talk locations</title>")
    map_path.write_text(text, encoding="utf-8")
    return len(location_dict)


if __name__ == "__main__":
    print(f"Mapped {generate()} locations.")
