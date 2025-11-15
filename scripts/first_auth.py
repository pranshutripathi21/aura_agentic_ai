# scripts/first_auth.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    # add more if needed
]

def main():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "./credentials/credentials.json")
    token_path = os.environ.get("GOOGLE_TOKEN_PATH", "./tokens/token.json")
    Path(os.path.dirname(token_path)).mkdir(parents=True, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    # Save credentials
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    print("Saved token to", token_path)

if __name__ == "__main__":
    main()
