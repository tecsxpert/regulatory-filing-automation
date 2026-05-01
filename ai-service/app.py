import os

from flask import Flask


def create_app() -> Flask:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    from routes.categorise import bp as categorise_bp
    from routes.generate_report import bp as generate_report_bp
    from routes.health import bp as health_bp
    from routes.models import bp as models_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(categorise_bp)
    app.register_blueprint(generate_report_bp)
    app.register_blueprint(models_bp)

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    create_app().run(host="0.0.0.0", port=port, debug=debug)
