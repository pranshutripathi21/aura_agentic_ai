# app/web/__init__.py
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.register_blueprint(web_bp)
    return app
