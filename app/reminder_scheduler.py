# app/reminder_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

class ReminderScheduler:
    def __init__(self, gmail_client):
        self.scheduler = BackgroundScheduler()
        self.gmail = gmail_client

    def schedule_reminders(self, reminders):
        for i, r in enumerate(reminders):
            run_time = r['when']
            if run_time > datetime.now():
                self.scheduler.add_job(self._send_email, 'date', run_date=run_time, args=[r], id=f"reminder_{i}")

    def _send_email(self, reminder):
        self.gmail.send_message(
            to_email=os.environ.get("GMAIL_USER_EMAIL"),
            subject=reminder['subject'],
            body_text=reminder['body']
        )

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()
