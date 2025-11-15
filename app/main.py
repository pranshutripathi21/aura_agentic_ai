# # app/main.py
# import os
# from dotenv import load_dotenv
# from app.gmail_client import GmailClient
# from app.timetable_parser import parse_csv_timetable, build_reminders
# from app.reminder_scheduler import ReminderScheduler
# from app.agents.email_agent import classify_emails

# load_dotenv()

# def upload_and_schedule(timetable_path):
#     gmail = GmailClient()
#     events = parse_csv_timetable(timetable_path)
#     reminders = build_reminders(events, minutes_before=30)
#     sched = ReminderScheduler(gmail)
#     sched.schedule_reminders(reminders)
#     sched.start()
#     print("Scheduled reminders. Press Ctrl+C to exit.")
#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         sched.shutdown()

# from app.gmail_client import GmailClient
# from app.agents.email_agent import classify_emails

# def scan_and_flag(max_messages=40):
#     gmail = GmailClient()
#     emails = gmail.fetch_messages(max_results=max_messages)

#     analyzed_count = 0
#     skipped_count = 0
#     results = []

#     for e in emails:
#         subject = e["subject"]
#         snippet = e["snippet"]

#         # Only analyze if it contains relevant keywords
#         keywords = ["exam", "test", "assignment", "intern", "interview", "placement"]
#         if not any(k.lower() in (subject + snippet).lower() for k in keywords):
#             results.append({
#                 "subject": subject,
#                 "snippet": snippet,
#                 "analysis": "Skipped (no relevant keywords found)"
#             })
#             skipped_count += 1
#             continue

#         # Send to AI model
#         try:
#             analysis = classify_emails(subject, snippet)
#             results.append({
#                 "subject": subject,
#                 "snippet": snippet,
#                 "analysis": analysis
#             })
#             analyzed_count += 1
#         except Exception as ex:
#             results.append({
#                 "subject": subject,
#                 "snippet": snippet,
#                 "analysis": f"Error analyzing email: {ex}"
#             })

#     stats = {"analysis": analyzed_count, "skipped": skipped_count}
#     return results, stats


# if __name__ == "__main__":
#     import argparse
#     p = argparse.ArgumentParser()
#     p.add_argument("--upload", help="path to timetable CSV")
#     p.add_argument("--scan", action="store_true", help="scan inbox and classify")
#     args = p.parse_args()
#     if args.upload:
#         upload_and_schedule(args.upload)
#     elif args.scan:
#         scan_and_flag()
#     else:
#         print("Use --upload PATH or --scan")








import os
import argparse
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify


from app.gmail_client import GmailClient
from app.agents.email_agent import classify_emails
from app.timetable_parser import extract_timetable_info  # PDF parser
from app.timetable_parser import parse_pdf_timetable
from app.reminder_scheduler import ReminderScheduler


load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    """Main frontend page."""
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def scan_inbox_api():
    """API endpoint for scanning emails (same logic as CLI)."""
    try:
        data = request.get_json()
        max_messages = data.get("max_messages", 40)

        results, stats = scan_and_flag(max_messages=max_messages)
        return jsonify({"results": results, "stats": stats})
    except Exception as e:
        print("[ERROR in /api/scan]:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze_timetable", methods=["POST"])
def analyze_timetable():
    """API endpoint for analyzing uploaded timetable PDFs."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"[DEBUG] File saved to {filepath}")

        info = extract_timetable_info(filepath)
        print(f"[DEBUG] Extracted info: {info}")

        if not info or (not info.get("exams") and not info.get("holidays")):
            return jsonify({"error": "No exam or holiday information found."}), 400

        return jsonify(info)

    except Exception as e:
        import traceback
        print("[ERROR in /api/analyze_timetable]:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def upload_and_schedule(timetable_path):
    """Used from CLI for analyzing timetable PDFs."""
    events = parse_pdf_timetable(timetable_path)
    summary = extract_timetable_info(events)
    print("\n📅 Timetable Summary:")
    print("Exams:")
    for e in summary["exams"]:
        print(" -", e)
    print("\nHolidays:")
    for h in summary["holidays"]:
        print(" -", h)



def scan_and_flag(max_messages=40):
    """Fetches Gmail messages and classifies important ones."""
    gmail = GmailClient()
    emails = gmail.fetch_messages(max_results=max_messages)

    analyzed_count = 0
    skipped_count = 0
    results = []

    for e in emails:
        subject = e["subject"]
        snippet = e["snippet"]

        keywords = ["exam", "test", "assignment", "intern", "interview", "placement"]
        if not any(k.lower() in (subject + snippet).lower() for k in keywords):
            results.append({
                "subject": subject,
                "snippet": snippet,
                "analysis": "Skipped (no relevant keywords found)"
            })
            skipped_count += 1
            continue

        try:
            analysis = classify_emails(subject, snippet)
            results.append({
                "subject": subject,
                "snippet": snippet,
                "analysis": analysis
            })
            analyzed_count += 1
        except Exception as ex:
            results.append({
                "subject": subject,
                "snippet": snippet,
                "analysis": f"Error analyzing email: {ex}"
            })

    stats = {"analysis": analyzed_count, "skipped": skipped_count}
    return results, stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", help="Path to timetable CSV")
    parser.add_argument("--scan", action="store_true", help="Scan inbox and classify")
    parser.add_argument("--web", action="store_true", help="Launch web interface")
    args = parser.parse_args()

    if args.upload:
        upload_and_schedule(args.upload)
    elif args.scan:
        scan_and_flag()
    elif args.web:
        print("🚀 Starting Flask web interface at http://127.0.0.1:5000")
        app.run(debug=True)
    else:
        print("Use one of: --upload PATH | --scan | --web")
