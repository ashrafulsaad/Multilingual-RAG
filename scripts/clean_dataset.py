"""Clean raw text files into normalized, language-tagged JSONL records."""

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path


def detect_language(text: str) -> str:
    bangla = len(re.findall(r"[\u0980-\u09ff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if bangla and latin:
        return "Mixed"
    if bangla:
        return "Bangla"
    return "English"


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?im)^(?:source|copyright|advertisement|menu)\s*:?.*$", " ", text)
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_folder(input_dir: Path, output_file: Path, min_chars: int = 20) -> int:
    seen: set[str] = set()
    records: list[dict[str, str]] = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".txt":
            continue
        text = clean_text(path.read_text(encoding="utf-8", errors="replace"))
        if len(text) < min_chars or text in seen:
            continue
        seen.add(text)
        records.append({"text": text, "language": detect_language(text), "source": str(path)})
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--min-chars", type=int, default=20)
    args = parser.parse_args()
    print(f"Wrote {clean_folder(args.input_dir, args.output_file, args.min_chars)} records")


if __name__ == "__main__":
    main()