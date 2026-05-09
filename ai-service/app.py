"""
Tool-19 — Regulatory Filing Automation
AI Microservice — Flask entry point
"""

import os
import time
import logging

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_talisman import Talisman
from dotenv import load_dotenv

# Blueprint imports
from routes.categorise import categorise_bp
from routes.query import query_bp
from routes.health import health_bp
from routes.generate_report import generate_report_bp
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.analyse_document import analyse_document_bp
from routes.batch_process import batch_process_bp

# =========================
# Load Environment Variables
# =========================
load_dotenv()

# =========================
# Logging Config
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

APP_START_TIME = time.time()


def create_app():

    app = Flask(
        __name__,
        static_folder="static"
    )

    # =========================
    # Security Headers
    # =========================
    Talisman(
        app,
        force_https=False,
        content_security_policy=None,
        x_content_type_options=True,
        x_xss_protection=True,
        referrer_policy="strict-origin-when-cross-origin",
    )

    # =========================
    # CORS Configuration
    # =========================
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")

    CORS(
        app,
        resources={
            r"/*": {
                "origins": allowed_origins
            }
        }
    )

    # =========================
    # App Config
    # =========================
    app.config["START_TIME"] = APP_START_TIME

    # =========================
    # Root Route
    # =========================
    @app.route("/", methods=["GET"])
    def home():

        return jsonify({
            "status": "success",
            "service": "Tool-19 AI Microservice",
            "message": "API is running"
        }), 200

    # =========================
    # Demo Route
    # =========================
    @app.route("/demo", methods=["GET"])
    def demo():

        return jsonify({
            "success": True,
            "project": "Tool-19",
            "title": "Regulatory Filing Automation",
            "status": "All systems operational",
            "modules": [
                "Groq AI Integration",
                "AI Categorisation",
                "Report Generation",
                "Document Analysis",
                "Redis Cache",
                "ChromaDB Vector Search",
                "Async Jobs",
                "Health Monitoring"
            ]
        }), 200

    # =========================
    # Favicon Route
    # =========================
    @app.route("/favicon.ico")
    def favicon():

        favicon_path = os.path.join(
            app.root_path,
            "static"
        )

        favicon_file = os.path.join(
            favicon_path,
            "favicon.ico"
        )

        if not os.path.exists(favicon_file):
            return "", 204

        return send_from_directory(
            favicon_path,
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon"
        )

    # =========================
    # Register Blueprints
    # =========================
    blueprints = [
        describe_bp,
        recommend_bp,
        categorise_bp,
        generate_report_bp,
        query_bp,
        analyse_document_bp,
        batch_process_bp,
        health_bp
    ]

    for bp in blueprints:
        app.register_blueprint(bp)

    logger.info("AI service started successfully.")

    return app


# =========================
# Create Flask App
# =========================
app = create_app()


# =========================
# Main Entry Point
# =========================
if __name__ == "__main__":

    port = int(
        os.getenv("AI_PORT", 5000)
    )

    debug = (
        os.getenv(
            "FLASK_ENV",
            "production"
        ).lower() == "development"
    )

    logger.info(
        f"Starting server on port {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
