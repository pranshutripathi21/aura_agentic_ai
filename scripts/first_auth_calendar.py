# scripts/first_auth_calendar.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Where to save token
TOKEN_PATH = "./tokens/calendar_token.json"
CREDENTIALS_PATH = "./credentials/credentials.json"

# recommended scope to insert events; adjust if needed
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    # "https://www.googleapis.com/auth/calendar"  # full access if you prefer
]

def main():
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(f"Put your OAuth client JSON at {CREDENTIALS_PATH}")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    # run local server for authorization
    creds = flow.run_local_server(port=41491, prompt="consent", authorization_prompt_message="")
    # Save credentials to token path
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    print(f"Saved token to {TOKEN_PATH}")

if __name__ == "__main__":
    main()
