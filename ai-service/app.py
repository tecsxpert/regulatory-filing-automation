"""
Flask Application with Input Sanitisation Middleware & Rate Limiting
Integrates InputSanitiser and Flask-Limiter to protect all endpoints
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from services.input_sanitiser import InputSanitiser
from flask_talisman import Talisman 
import logging

# Initialize Flask app
app = Flask(__name__)
# Day 8 Security Fix — Security Headers
# Talisman(
#     app,
#     content_security_policy=False,
#     x_content_type_options=True,
#     frame_options='DENY',  
#     strict_transport_security=False
# )

# Day 12 — Strengthened Security Headers
Talisman(
    app,
    content_security_policy=False,
    x_content_type_options=True,
    frame_options='DENY',
    strict_transport_security=False,
    referrer_policy='strict-origin-when-cross-origin'
)

@app.after_request
def add_extra_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING SETUP
# ============================================================================

limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=["30 per minute"]  # Default: 30 requests per minute
)


# ============================================================================
# MIDDLEWARE: Input Validation (runs before every request)
# ============================================================================

@app.before_request
def validate_user_input():
    """
    Middleware to validate all incoming request data.
    Runs BEFORE every request to any endpoint.

    Rejects requests with dangerous patterns:
    - HTML/JavaScript tags
    - Prompt injection keywords
    - Email header injection attempts
    """

    # Only validate POST and PUT requests (when users send data)
    if request.method not in ['POST', 'PUT']:
        return None  # Let GET, DELETE, etc. through

    # Get the JSON data from the request
    data = request.get_json(silent=True)

    if not data:
        return None  # No data to validate

    # Validate all fields
    is_valid, error_message = InputSanitiser.validate_all_fields(data)

    # If validation fails, reject the request
    if not is_valid:
        logger.warning(f"⚠️  Input validation failed: {error_message}")
        return jsonify({
            "error": error_message,
            "status": "INPUT_VALIDATION_FAILED"
        }), 400

    # If validation passes, continue to the endpoint
    logger.info(f"✅ Input validation passed for {request.method} {request.path}")
    return None


# ============================================================================
# EXAMPLE ENDPOINTS (for testing)
# ============================================================================

@app.route('/health', methods=['GET'])
@limiter.exempt  # Exempt from rate limiting
def health_check():
    """
    Health check endpoint
    Not rate limited - always available
    """
    return jsonify({
        "status": "healthy",
        "service": "AI Service",
        "input_sanitisation": "enabled",
        "rate_limiting": "enabled",
        "rate_limits": {
            "default": "30 per minute",
            "generate_report": "10 per minute"
        }
    }), 200


@app.route('/describe', methods=['POST'])
@limiter.limit("30 per minute")  # Default rate limit
def describe():
    """
    Example AI endpoint: Describe a filing
    Rate limit: 30 requests per minute

    Request:
    {
        "filing_id": "123",
        "content": "Q1 Compliance Report"
    }

    Response:
    {
        "filing_id": "123",
        "description": "Analysis of filing 123: Q1 Compliance Report",
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        # At this point, input has already been validated by middleware
        filing_id = data.get('filing_id')
        content = data.get('content')

        # Simulate AI processing
        description = f"Analysis of filing {filing_id}: {content}"

        return jsonify({
            "filing_id": filing_id,
            "description": description,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"❌ Error in /describe: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "ERROR"
        }), 500


@app.route('/categorise', methods=['POST'])
@limiter.limit("30 per minute")  # Default rate limit
def categorise():
    """
    Example AI endpoint: Categorise a filing
    Rate limit: 30 requests per minute

    Request:
    {
        "content": "Financial statement for Q1"
    }

    Response:
    {
        "content": "Financial statement for...",
        "category": "REGULATORY",
        "confidence": 0.92,
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        # Input is already validated by middleware
        content = data.get('content')

        # Simulate AI categorisation
        category = "REGULATORY"
        confidence = 0.92

        return jsonify({
            "content": content[:50] + "...",  # Return first 50 chars
            "category": category,
            "confidence": confidence,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"❌ Error in /categorise: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "ERROR"
        }), 500


@app.route('/generate-report', methods=['POST'])
@limiter.limit("10 per minute")  # STRICTER rate limit for expensive operation
def generate_report():
    """
    Example AI endpoint: Generate regulatory report
    Rate limit: 10 requests per minute (stricter because it's expensive)

    Request:
    {
        "filing_id": "123",
        "document_type": "COMPLIANCE"
    }

    Response:
    {
        "filing_id": "123",
        "document_type": "COMPLIANCE",
        "report": "Report for 123 of type COMPLIANCE",
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        # Input is already validated by middleware
        filing_id = data.get('filing_id')
        document_type = data.get('document_type')

        # Simulate report generation (expensive operation)
        report = f"Report for {filing_id} of type {document_type}"

        return jsonify({
            "filing_id": filing_id,
            "document_type": document_type,
            "report": report,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"❌ Error in /generate-report: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "ERROR"
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({
        "error": "Bad request",
        "status": "ERROR"
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status": "ERROR"
    }), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle 429 Rate Limit Exceeded errors"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later.",
        "status": 429,
        "retry_after": 60
    }), 429


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"❌ Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "status": "ERROR"
    }), 500


# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting AI Service with Input Sanitisation & Rate Limiting")
    print("📝 Input Sanitisation: ENABLED")
    print("   - HTML/JavaScript injection prevention")
    print("   - Prompt injection prevention")
    print("   - Email header injection prevention")
    print("\n🚦 Rate Limiting: ENABLED")
    print("   - Default: 30 requests per minute")
    print("   - /generate-report: 10 requests per minute (stricter)")
    print("   - /health: Unlimited (exempt)")
    print("\n📍 Server running on: http://localhost:5000")
    print("💊 Health check: http://localhost:5000/health\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
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
    from routes.models import bp as models_bp

    app.register_blueprint(categorise_bp)
    app.register_blueprint(generate_report_bp)
    app.register_blueprint(models_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    create_app().run(host="0.0.0.0", port=port, debug=debug)
