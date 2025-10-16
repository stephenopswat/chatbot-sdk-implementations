#!/usr/bin/env python3
# Fetch Google Docs, split by headings, emit JSONL sections for RAG.
# Usage examples at bottom.

import json, os, sys, pathlib, re
from typing import Dict, List, Iterable, Optional
from datetime import datetime
from tqdm import tqdm

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]

TOKEN_PATH = "token.json"        # created on first run
CREDS_PATH = "credentials.json"  # download from Google Console

def _auth():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # type: ignore[name-defined]
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds

def drive_service(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def docs_service(creds):
    return build("docs", "v1", credentials=creds, cache_discovery=False)

def list_docs(drive, folder_id: Optional[str], query: Optional[str]) -> Iterable[Dict]:
    """Yield Drive files (Google Docs only)."""
    base_q = "mimeType='application/vnd.google-apps.document' and trashed=false"
    if folder_id:
        base_q += f" and '{folder_id}' in parents"
    if query:
        base_q += f" and ({query})"  # e.g., name contains 'SDK'
    page_token = None
    while True:
        resp = drive.files().list(
            q=base_q,
            fields="nextPageToken, files(id, name, modifiedTime, owners, webViewLink)",
            pageToken=page_token,
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            yield f
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

def _text_from_elements(elements) -> str:
    out = []
    for e in elements or []:
        tr = e.get("textRun")
        if tr and "content" in tr:
            out.append(tr["content"])
    return "".join(out)

def _heading_level(paragraph_style: Dict) -> Optional[int]:
    style = (paragraph_style or {}).get("namedStyleType")
    if not style:
        return None
    m = re.match(r"HEADING_(\d+)", style)
    return int(m.group(1)) if m else None

def doc_sections(docs, doc_id: str) -> List[Dict]:
    """Return list of sections split by headings (H1–H3)."""
    d = docs.documents().get(documentId=doc_id).execute()
    title = d.get("title", "")
    body = d.get("body", {})
    content = body.get("content", [])

    sections = []
    current = {"heading": "INTRO", "level": 1, "text": []}

    for el in content:
        if "paragraph" in el:
            p = el["paragraph"]
            text = _text_from_elements(p.get("elements"))
            level = _heading_level(p.get("paragraphStyle", {}))
            # ignore empty whitespace Google Docs often appends
            if level and level <= 3:
                # flush previous
                if current["text"]:
                    sections.append(current)
                current = {"heading": text.strip() or f"HEADING_{level}", "level": level, "text": []}
            else:
                if text.strip():
                    current["text"].append(text)
        elif "table" in el:
            # Optional: flatten tables to text rows
            rows = []
            for r in el["table"].get("tableRows", []):
                cells = []
                for c in r.get("tableCells", []):
                    cells.append(_text_from_elements(sum([p.get("elements", []) for p in c.get("content", []) if "paragraph" in p], [])))
                rows.append(" | ".join(x.strip() for x in cells if x))
            if rows:
                current["text"].append("\n".join(rows))

    if current["text"]:
        sections.append(current)

    # normalize output
    out = []
    for i, s in enumerate(sections):
        txt = " ".join(s["text"]).strip()
        if not txt:
            continue
        out.append({
            "section_index": i,
            "section_heading": s["heading"],
            "section_level": s["level"],
            "text": txt,
        })
    return out

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Import Google Docs → JSONL sections")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--folder", help="Drive folder ID to scan")
    src.add_argument("--q", help="Drive files list query, e.g. name contains 'SDK'")
    ap.add_argument("--out", required=True, help="Output JSONL path")
    ap.add_argument("--limit", type=int, default=None, help="Max docs")
    args = ap.parse_args()

    creds = _auth()
    drv = drive_service(creds)
    dcs = docs_service(creds)

    count = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for file in tqdm(list_docs(drv, args.folder, args.q), desc="Docs"):
            if args.limit and count >= args.limit:
                break
            count += 1
            doc_id = file["id"]
            name = file.get("name")
            updated = file.get("modifiedTime")
            web = file.get("webViewLink") or f"https://docs.google.com/document/d/{doc_id}/edit"
            try:
                secs = doc_sections(dcs, doc_id)
            except HttpError as e:
                print(f"[WARN] Skipping {doc_id} ({name}): {e}", file=sys.stderr)
                continue
            for s in secs:
                rec = {
                    "_id": f"GDoc:{doc_id}#{s['section_index']:03d}",
                    "text": s["text"],
                    "source": "gdocs",
                    "doc_id": doc_id,
                    "title": name,
                    "section_heading": s["section_heading"],
                    "section_level": s["section_level"],
                    "url": web,
                    "updated_at": updated,
                    "doc_ids": [doc_id],       # matches your index example
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
