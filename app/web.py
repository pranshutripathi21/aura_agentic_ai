# app/web.py
import os
from flask import Flask, Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from app.timetable_parser_pdf import parse_timetable_pdf_bytes

load_dotenv()

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    @app.route("/")
    def index():
        # If you have index.html in templates, render it; else static file
        try:
            return render_template("index.html")
        except Exception:
            # fallback: serve a tiny page
            return "<p>Student Assistant running. Use the frontend index.html.</p>"

    @app.route("/api/upload_timetable", methods=["POST"])
    def upload_timetable():
        """
        Accepts a multipart/form-data upload with key 'file' (PDF).
        Returns JSON: {"exams": [...], "holidays": [...]}
        """
        if "file" not in request.files:
            return jsonify({"error": "no file part"}), 400
        f = request.files["file"]
        if f.filename == "":
            return jsonify({"error": "no selected file"}), 400

        filename = secure_filename(f.filename)
        # Save temporarily (optional); we can also read bytes directly
        file_bytes = f.read()
        try:
            parsed = parse_timetable_pdf_bytes(file_bytes)
        except Exception as e:
            return jsonify({"error": "parsing_failed", "detail": str(e)}), 500

        return jsonify(parsed), 200

    # optional: health endpoint
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
