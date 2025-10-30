"""Clean and preprocess text documents from Confluence and save as JSON files."""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def clean_text(text: str) -> str:
    """Remove HTML, URLs, normalize whitespace, and strip text."""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'https?://\S+', '', text)  # remove URLs
    text = re.sub(r'\s+', ' ', text)  # normalize whitespace
    return text.strip()

def extract_date_from_filename(filename: str) -> str:
    """Try to extract a date in format YYYY.MM.DD from filename."""
    match = re.search(r'(\d{4}\.\d{2}\.\d{2})', filename)
    return match.group(1) if match else None

def generate_brief(text: str, max_words: int = 30) -> str:
    """Create a short summary from the first N words."""
    words = text.split()
    brief = ' '.join(words[:max_words])
    if len(words) > max_words:
        brief += '...'
    return brief

def process_all_files(input_dir: str, output_dir: str):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in input_dir.rglob("*.txt"):
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

            cleaned_content = clean_text(raw_text)
            file_date = extract_date_from_filename(file_path.name)
            file_name = file_path.stem

            result = {
                "source": str(file_path),
                "date": file_date,
                "name": file_name,
                "content": cleaned_content,
                "brief": generate_brief(cleaned_content)
            }

            # Save each file as its own JSON
            output_file = output_dir / f"{file_name}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ Processed {file_path.name} → {output_file.name}")

        except Exception as e:
            print(f"❌ Failed to process {file_path.name}: {e}")

if __name__ == "__main__":
    process_all_files(
        r"C:\Users\alice.dang\OPSWAT\Tri Cuong Stephen Luong - All Documentation",
        r"C:\Users\alice.dang\OPSWAT\Processed_JSON"
    )
