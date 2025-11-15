import os
import base64
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText


class GmailClient:
    def __init__(self, token_path=None, credentials_path=None):
        token_path = token_path or os.environ.get("GOOGLE_TOKEN_PATH", "./tokens/token.json")
        credentials_path = credentials_path or os.environ.get("GOOGLE_CREDENTIALS_PATH", "./credentials/credentials.json")

        with open(token_path, "r") as f:
            token_data = json.load(f)

        self.creds = Credentials.from_authorized_user_info(token_data)
        self.service = build("gmail", "v1", credentials=self.creds)

    def send_message(self, to_email, subject, body_text, from_email=None):
        """Send an email using Gmail API."""
        message = MIMEText(body_text)
        message["to"] = to_email
        message["from"] = from_email or os.environ.get("GMAIL_USER_EMAIL")
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return self.service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

    def list_messages(self, query=None, max_results=50):
        """List message IDs from the user's mailbox."""
        res = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return res.get("messages", [])

    def get_message(self, msg_id):
        """Retrieve a specific message by ID."""
        msg = self.service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        snippet = msg.get("snippet", "")
        return {"id": msg_id, "headers": headers, "snippet": snippet}

    def fetch_messages(self, max_results=40):
        """Fetch recent emails and return a list of dicts (subject + snippet)."""
        results = self.service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        email_texts = []

        for msg in messages:
            msg_data = self.service.users().messages().get(
                userId="me", id=msg["id"]
            ).execute()

            headers = msg_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
            snippet = msg_data.get("snippet", "")

            # ✅ Return dict, not string
            email_texts.append({
                "subject": subject,
                "snippet": snippet
            })

        return email_texts
