import os
from flask import Blueprint, render_template, jsonify, request
from app.main import scan_and_flag
from app.timetable_parser import parse_pdf_timetable, extract_timetable_info
from app.calendar_client import CalendarClient

web_bp = Blueprint(
    "web",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@web_bp.route("/")
def home():
    return render_template("index.html")


@web_bp.route("/api/scan", methods=["POST"])
def scan_inbox():
    data = request.get_json(force=True)
    max_messages = int(data.get("max_messages", 40))

    results, stats = scan_and_flag(max_messages=max_messages)
    return jsonify({"results": results, "stats": stats})

@web_bp.route("/api/upload_timetable", methods=["POST"])
def upload_timetable():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", file.filename)
        file.save(save_path)

        
        events = parse_pdf_timetable(save_path)
        print("[DEBUG] Parsed Events:", events)

        
        summary = extract_timetable_info(events)

        if not events:
            return jsonify({"error": "No events found"}), 400

        
        return jsonify({
            "success": True,
            "summary": summary,
            "events": events
        })

    except Exception as e:
        import traceback
        print("[ERROR in /api/upload_timetable]:", traceback.format_exc())
        return jsonify({"error": f"Error analyzing timetable: {e}"}), 500



@web_bp.route("/api/add_events", methods=["POST"])
def add_events_to_calendar():
    """
    POST body: { "events": [ { "date": "YYYY-MM-DD", "event": "...", "type":"Exam" }, ... ],
                 "reminder_minutes_before": 60 }
    """
    try:
        data = request.get_json(force=True)
        events = data.get("events", [])
        minutes_before = int(data.get("reminder_minutes_before", 60))

        if not events:
            return jsonify({"error": "No events provided"}), 400

        cal = CalendarClient()
        created = cal.create_events_from_timetable(parsed_events=events, reminders_minutes_before=minutes_before)

        
        summary = [{"id": c.get("id"), "htmlLink": c.get("htmlLink"), "summary": c.get("summary")} for c in created]
        return jsonify({"success": True, "created": summary}), 200

    except Exception as e:
        import traceback
        print("[ERROR in /api/add_events]:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500