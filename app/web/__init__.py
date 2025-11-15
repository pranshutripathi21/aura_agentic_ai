# app/web/__init__.py
from flask import Flask
from app.web.routes import web_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(web_bp)
    return app
