"""Clean and preprocess documentation data from JSONL that is script from OPSWAT Website file."""
import json
import re
from pathlib import Path

def clean_doc_data(doc):
    """Clean one documentation record by removing tags, HTML, and unwanted sections."""
    cleaned = {
        "url": doc.get("url"),
        "title": doc.get("title"),
    }

    # --- Clean Headings ---
    ignore_keywords = ["cookie", "privacy", "consent", "preferences"]
    cleaned["headings"] = []

    for h in doc.get("headings", []):
        text = h.get("text", "")
        # Skip ignored keywords
        if not text or any(k in text.lower() for k in ignore_keywords):
            continue

        # Remove HTML tags and tag-like prefixes
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"tag:[^\s>]+>?", "", text, flags=re.IGNORECASE)
        text = text.strip()

        if text:
            cleaned["headings"].append({"text": text})

    # --- Clean Links ---
    valid_links = []
    for link in doc.get("links_out", []):
        text = link.get("text", "").strip()
        href = link.get("href", "")
        if text and href and not any(
            k in href.lower() for k in ["cookie", "privacy", "onetrust", "legal"]
        ):
            valid_links.append({"href": href, "text": text})
    cleaned["links_out"] = valid_links

    # --- Clean Text ---
    text = doc.get("text", "") or ""

    # Remove HTML and tag-like patterns
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"tag:[^\s>]+>?", "", text, flags=re.IGNORECASE)

    # Remove cookie/legal/privacy sections
    text = re.sub(
        r"(This Website Uses Cookies|Privacy Preference Center|Cookie Policy).*",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Normalize whitespace
    text = re.sub(r"\n{2,}", "\n", text).strip()
    cleaned["text"] = text

    # --- Add summary ---
    if not text:
        cleaned["summary"] = "No documentation text found."
    elif any(w in text.lower() for w in ["install", "configure", "deploy", "setup"]):
        cleaned["summary"] = "Installation and configuration documentation."
    else:
        cleaned["summary"] = "General documentation content."

    return cleaned


def main():
    input_path = Path("opswat_docs.jsonl")
    output_path = Path("opswat_docs_cleaned.jsonl")

    if not input_path.exists():
        print("❌ File opswat_docs.jsonl not found.")
        return

    print(f"🔍 Cleaning data from {input_path} ...")

    total = 0
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                cleaned_doc = clean_doc_data(doc)
                outfile.write(json.dumps(cleaned_doc, ensure_ascii=False) + "\n")
                total += 1
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipped invalid JSON line: {e}")

    print(f"✅ Done! Cleaned {total} documents → {output_path}")


if __name__ == "__main__":
    main()
