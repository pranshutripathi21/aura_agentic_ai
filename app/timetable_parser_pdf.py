# app/timetable_parser_pdf.py
import re
import fitz  # PyMuPDF
from dateutil import parser as dateparser
from typing import List, Dict, Tuple
import datetime

# Patterns for dates (will be passed to dateutil for parsing)
DATE_REGEXES = [
    # dd/mm/yyyy or dd-mm-yyyy or d/m/yy
    r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
    # 12 March 2025 or March 12, 2025
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ ,.\d]*(?:\d{1,2},? ?\d{4})?\b",
    # ISO dates 2025-11-18
    r"\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b"
]

# Lowercased keywords indicating exam/holiday lines
EXAM_KEYWORDS = ["exam", "test", "midterm", "final", "endsem", "end sem", "end-sem", "semester exam"]
HOLIDAY_KEYWORDS = ["holiday", "vacation", "break", "off", "no class", "public holiday", "festive", "recess"]

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Return the full textual content (joined) from a PDF file bytes using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_text = []
    for page in doc:
        page_text = page.get_text("text")
        if page_text:
            all_text.append(page_text)
    doc.close()
    return "\n".join(all_text)

def find_dates_in_line(line: str) -> List[str]:
    """Return a list of candidate date substrings found in the line using regex patterns."""
    found = []
    for rx in DATE_REGEXES:
        for m in re.findall(rx, line, flags=re.IGNORECASE):
            # normalize whitespace and trailing punctuation
            s = m.strip(" ,.;:()[]")
            if s:
                found.append(s)
    return list(dict.fromkeys(found))  # deduplicate preserving order

def try_parse_date(s: str) -> str:
    """Try to parse a date-like string into ISO format YYYY-MM-DD. Returns None on failure."""
    try:
        # dateutil parser is flexible — prefer dayfirst try if ambiguous with slashes
        if re.match(r"^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$", s):
            # attempt dayfirst then fallback
            dt = dateparser.parse(s, dayfirst=True, fuzzy=True)
        else:
            dt = dateparser.parse(s, fuzzy=True)
        if isinstance(dt, datetime.datetime):
            return dt.date().isoformat()
        elif isinstance(dt, datetime.date):
            return dt.isoformat()
    except Exception:
        return None
    return None

def parse_timetable_text(text: str) -> Dict[str, List[Dict]]:
    """
    Heuristic parser:
    - Scans text line-by-line
    - If a line contains exam keywords, find candidate dates in the same line (or nearby)
      and treat as exam entries (subject is remaining words)
    - If a line contains holiday keywords, same for holidays
    Returns: {"exams": [...], "holidays": [...]}
    Each entry: {"date": "YYYY-MM-DD", "subject": "...", "reason": "...", "raw_line": "..."}
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    exams = []
    holidays = []
    n = len(lines)

    for i, line in enumerate(lines):
        low = line.lower()

        # Check for explicit exam keywords
        if any(k in low for k in EXAM_KEYWORDS):
            # look for date in this line first
            date_candidates = find_dates_in_line(line)
            parsed_date = None
            parsed_date_iso = None
            if date_candidates:
                for dc in date_candidates:
                    pd = try_parse_date(dc)
                    if pd:
                        parsed_date_iso = pd
                        parsed_date = dc
                        break
            # if not found, look ahead a few lines
            if not parsed_date_iso:
                for j in range(i+1, min(i+4, n)):
                    dcands = find_dates_in_line(lines[j])
                    for dc in dcands:
                        pd = try_parse_date(dc)
                        if pd:
                            parsed_date_iso = pd
                            parsed_date = dc
                            break
                    if parsed_date_iso:
                        break

            subject = line
            # clean subject by removing date substrings found
            for dc in date_candidates:
                subject = subject.replace(dc, "")
            subject = re.sub(r'\s{2,}', ' ', subject).strip(" -:,.")
            exams.append({
                "date": parsed_date_iso if parsed_date_iso else None,
                "subject": subject,
                "raw_line": line
            })
            continue

        # Check for holidays
        if any(k in low for k in HOLIDAY_KEYWORDS):
            date_candidates = find_dates_in_line(line)
            parsed_date_iso = None
            parsed_date = None
            if date_candidates:
                for dc in date_candidates:
                    pd = try_parse_date(dc)
                    if pd:
                        parsed_date_iso = pd
                        parsed_date = dc
                        break
            # also look ahead/back for possible date lines
            if not parsed_date_iso:
                # look back up to 2 lines
                for j in range(max(0, i-2), i):
                    dcands = find_dates_in_line(lines[j])
                    for dc in dcands:
                        pd = try_parse_date(dc)
                        if pd:
                            parsed_date_iso = pd
                            parsed_date = dc
                            break
                    if parsed_date_iso:
                        break
            reason = line
            for dc in date_candidates:
                reason = reason.replace(dc, "")
            reason = re.sub(r'\s{2,}', ' ', reason).strip(" -:,.")
            holidays.append({
                "date": parsed_date_iso if parsed_date_iso else None,
                "reason": reason or None,
                "raw_line": line
            })
            continue

    # Postprocess: remove duplicates by date+subject/reason
    def dedup_entries(entries: List[Dict], key_fields: Tuple[str] = ("date", "subject")):
        seen = set()
        out = []
        for e in entries:
            key = tuple(e.get(k) for k in key_fields)
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
        return out

    exams = dedup_entries(exams, ("date", "subject"))
    holidays = dedup_entries(holidays, ("date", "reason"))
    return {"exams": exams, "holidays": holidays}

# convenience: parse uploaded file bytes
def parse_timetable_pdf_bytes(file_bytes: bytes) -> Dict[str, List[Dict]]:
    text = extract_text_from_pdf_bytes(file_bytes)
    return parse_timetable_text(text)
