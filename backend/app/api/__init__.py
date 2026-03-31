from flask import Flask, jsonify


def error_response(message: str, status_code: int):
    """
    Build a consistent JSON error payload used by every API route.
    Format: { "error": "<message>", "status": <code> }

    Usage inside any route:
        return error_response("Slot not found.", 404)
    """
    return jsonify({"error": message, "status": status_code}), status_code


def register_error_handlers(app: Flask) -> None:
    """
    Attach app-level error handlers so that Flask's automatic error responses
    (e.g. 404 on an unknown URL, 405 on a wrong method) also return the
    standardized { "error": ..., "status": ... } format instead of HTML.

    Call this once in server.py after the Flask app is created.
    """

    @app.errorhandler(400)
    def bad_request(exc):
        return error_response(str(exc) or "Bad request.", 400)

    @app.errorhandler(404)
    def not_found(exc):
        return error_response(str(exc) or "Resource not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return error_response(str(exc) or "Method not allowed.", 405)

    @app.errorhandler(500)
    def internal_error(exc):
        return error_response("An unexpected internal error occurred.", 500)
