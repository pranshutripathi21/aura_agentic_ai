# app/calendar_client.py
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict

TOKEN_PATH = os.environ.get("GOOGLE_CALENDAR_TOKEN_PATH", "./tokens/calendar_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def load_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Calendar token not found at {TOKEN_PATH}. Run scripts/first_auth_calendar.py")
    with open(TOKEN_PATH, "r") as f:
        data = json.load(f)
    creds = Credentials.from_authorized_user_info(data, scopes=SCOPES)
    return creds

class CalendarClient:
    def __init__(self, calendar_id="primary"):
        self.creds = load_credentials()
        self.service = build("calendar", "v3", credentials=self.creds)
        self.calendar_id = calendar_id

    def create_all_day_event(self, date_iso: str, summary: str, description: str = "", reminders: List[Dict] = None):
        """
        Create an all-day event on `date_iso` (YYYY-MM-DD).
        For all-day events, set end date to next day (Google expects end exclusive).
        `reminders` example: [{"method":"popup","minutes":60}, {"method":"email","minutes":1440}]
        """
        start_date = date_iso
        # end is exclusive for full-day events
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        end_date = (dt + timedelta(days=1)).strftime("%Y-%m-%d")

        event = {
            "summary": summary,
            "description": description,
            "start": {"date": start_date},
            "end": {"date": end_date},
            "reminders": {"useDefault": False, "overrides": reminders or [{"method": "popup", "minutes": 60}]}
        }
        created = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return created

    def create_timed_event(self, start_iso: str, end_iso: str, summary: str, description: str = "", timezone: str = "UTC", reminders: List[Dict] = None):
        """
        Create event with dateTime (ISO 8601). Example start_iso: "2025-09-19T09:00:00"
        """
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
            "reminders": {"useDefault": False, "overrides": reminders or [{"method": "popup", "minutes": 60}]}
        }
        created = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return created

    def create_events_from_timetable(self, parsed_events: List[Dict], reminders_minutes_before=60):
        """
        parsed_events: list of dicts with keys: { "date": "YYYY-MM-DD", "event": "...", "type": "Exam"/"Holiday"/"Other" }
        Returns list of created event resources returned by API.
        """
        created = []
        # default reminders: popup X minutes before and email 1 day before
        reminders = [
            {"method": "popup", "minutes": reminders_minutes_before},
            {"method": "email", "minutes": 24 * 60}  # 1 day before via email
        ]
        for e in parsed_events:
            date = e.get("date")
            title = e.get("event") or "Event"
            # you can customize summary based on type
            if e.get("type") == "Exam":
                summary = f"Exam: {title}"
            else:
                summary = title

            # create all-day event
            created_event = self.create_all_day_event(date_iso=date, summary=summary, description=title, reminders=reminders)
            created.append(created_event)
        return created
