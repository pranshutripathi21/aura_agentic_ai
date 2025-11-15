# # app/timetable_parser.py
# import csv
# from datetime import datetime, timedelta

# def parse_csv_timetable(path):
#     events = []
#     with open(path, newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             # expects yyyy-mm-dd in date or adjust parsing as needed
#             date_s = row['date']
#             start = datetime.fromisoformat(f"{date_s}T{row['start_time']}")
#             end = datetime.fromisoformat(f"{date_s}T{row['end_time']}")
#             events.append({
#                 "course": row.get("course"),
#                 "start": start,
#                 "end": end,
#                 "location": row.get("location"),
#                 "notes": row.get("notes", "")
#             })
#     return events

# def build_reminders(events, minutes_before=30):
#     reminders = []
#     for ev in events:
#         reminder_time = ev['start'] - timedelta(minutes=minutes_before)
#         reminders.append({
#             "when": reminder_time,
#             "subject": f"Reminder: {ev['course']}",
#             "body": f"{ev['course']} at {ev['start'].strftime('%H:%M')} in {ev['location']}. Notes: {ev.get('notes','')}"
#         })
#     return reminders


















# app/timetable_parser.py
import pdfplumber
from datetime import datetime, timedelta
import re



def parse_pdf_timetable(pdf_path):
    """
    Extracts exam dates and holidays from a semester timetable PDF.
    Expected format:
    Date | Day | Event
    e.g. 19-Sep-2025 Friday Mid-Sem Exam - Mathematics
    """
    events = []
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # 🧠 Debugging output — to inspect actual lines extracted from the PDF
    print("=== DEBUG: Extracted Text from Timetable PDF ===")
    for i, line in enumerate(text.splitlines()[:30], start=1):
        print(f"{i:02d}: {line}")
    print("===============================================")

    # Now we’ll adjust the pattern after checking these lines
    date_pattern = re.compile(r"(\d{2}-[A-Za-z]{3}-\d{4})")

    lines = text.splitlines()
    for line in lines:
        match = date_pattern.search(line)
        if match:
            date_str = match.group(1)
            try:
                date = datetime.strptime(date_str, "%d-%b-%Y")
            except ValueError:
                continue

            if "Exam" in line:
                event_type = "Exam"
            elif "Holiday" in line:
                event_type = "Holiday"
            else:
                event_type = "Other"

            events.append({
                "date": date.strftime("%Y-%m-%d"),
                "event": line.split(match.group(1))[-1].strip(),
                "type": event_type
            })

    return events


def extract_timetable_info(events):
    """
    Builds a readable summary from the extracted events.
    """
    exams = [f"{e['date']} — {e['event']}" for e in events if e['type'] == 'Exam']
    holidays = [f"{e['date']} — {e['event']}" for e in events if e['type'] == 'Holiday']

    return {
        "exams": exams,
        "holidays": holidays,
        "count": {
            "exams": len(exams),
            "holidays": len(holidays)
        }
    }

