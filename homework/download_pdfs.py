import csv
import re
from pathlib import Path
from urllib.request import Request, urlopen


CSV_FILE = Path(__file__).with_name("books.csv")
OUTPUT_DIR = Path(__file__).with_name("books")


def filename_for(title):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("._")
    return f"{name or 'book'}.pdf"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with CSV_FILE.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or not {"title", "pdf_url"}.issubset(reader.fieldnames):
            raise ValueError("CSV must have 'title' and 'pdf_url' columns.")

        for row in reader:
            title = (row.get("title") or "").strip()
            url = (row.get("pdf_url") or "").strip()
            if not title or not url:
                print(f"Skipping row with missing title or PDF URL: {row}")
                continue

            destination = OUTPUT_DIR / filename_for(title)
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

            try:
                with urlopen(request, timeout=30) as response:
                    data = response.read()

                if b"%PDF-" not in data[:1024]:
                    raise ValueError("Downloaded content is not a PDF.")

                destination.write_bytes(data)
                print(f"Saved {destination}")
            except Exception as error:
                print(f"Failed to download {title}: {error}")


if __name__ == "__main__":
    main()