# app/agents/email_agent.py
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Initialize the LLM only once
llm = ChatGroq(
    groq_api_key=api_key,
    model = "llama-3.1-8b-instant"
)

# Define keywords to filter important mails
IMPORTANT_KEYWORDS = [
    "exam", "assignment", "deadline", "submission", 
    "internship", "interview", "viva", "results", "schedule", "project"
]

def classify_emails(gmail_client, max_messages=40):
    """Fetch emails, filter relevant ones, and analyze only those."""
    email_texts = gmail_client.fetch_messages(max_results=max_messages)

    prompt_template = """You are an academic assistant AI.
Summarize this student-related email and classify it as one of:
- IMPORTANT (if action needed soon)
- POTENTIALLY_IMPORTANT (if useful but not urgent)
- IRRELEVANT (if unrelated to academics)

Email content:
Subject: {subject}
Snippet: {snippet}

Return JSON format:
{{
  "category": "<category>",
  "summary": "<short summary>"
}}"""

    prompt = PromptTemplate.from_template(prompt_template)
    results = []

    for email in email_texts:
        subject = email["subject"].lower()
        snippet = email["snippet"].lower()

        # ✅ Check if the email contains relevant keywords
        if any(word in subject or word in snippet for word in IMPORTANT_KEYWORDS):
            full_prompt = prompt.format(subject=subject, snippet=snippet)

            try:
                response = llm.invoke(full_prompt)
                analysis = response.content
            except Exception as e:
                analysis = f"Error analyzing email: {e}"

            results.append({
                "subject": email["subject"],
                "snippet": email["snippet"],
                "analysis": analysis
            })
        else:
            # Skip irrelevant emails (no API call)
            results.append({
                "subject": email["subject"],
                "snippet": email["snippet"],
                "analysis": "Skipped (no relevant keywords found)."
            })

    return results
