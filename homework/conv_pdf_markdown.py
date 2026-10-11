from pathlib import Path

from markitdown import MarkItDown


PDF_DIR = Path(__file__).with_name("books")
OUTPUT_DIR = Path(__file__).with_name("books_text")


def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {PDF_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()

    for pdf_path in pdf_files:
        try:
            markdown = converter.convert(str(pdf_path)).text_content
            output_path = OUTPUT_DIR / f"{pdf_path.stem}.md"
            output_path.write_text(markdown, encoding="utf-8")
            print(f"Converted {pdf_path.name} -> {output_path.name}")
        except Exception as error:
            print(f"Failed to convert {pdf_path.name}: {error}")


if __name__ == "__main__":
    main()