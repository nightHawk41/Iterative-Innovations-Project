import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from app import db
from app.api import error_response, register_error_handlers
from app.utils.seed import seed_database

# Import all models so db.create_all() registers every table.
from app.models.item_slot import ItemSlot       # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.notification import Notification  # noqa: F401

# Import blueprints.
from app.api.inventory_routes import inventory_bp
from app.api.alerts_routes import alerts_bp
from app.api.transaction_routes import transaction_bp

app = Flask(__name__)
CORS(app)

# Define the path to the SQLite database file
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'vending.db')

# Configure the SQLAlchemy database URI to point to the SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object with the Flask app.
db.init_app(app)

# Register API blueprints.
app.register_blueprint(inventory_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(transaction_bp)

# Register standardized JSON error handlers (400, 404, 405, 500).
register_error_handlers(app)

# This is the route that will be called when the frontend makes a request to /test
@app.route("/test") 
def test_route():
    return {"message": ["Hello", "from", "Flask"]}


@app.route("/api/admin/sync-inventory-config", methods=["POST"])
def sync_inventory_config():
    """Reload item-slot configuration from inventory_config.csv on demand."""
    payload = request.get_json(silent=True) or {}
    summary = seed_database(
        config_path=payload.get("config_path"),
        update_existing=bool(payload.get("update_existing", True)),
    )

    if summary.get("error"):
        return error_response(summary["error"], 400)

    return jsonify(summary), 200

if __name__ == "__main__":
    # Create the database tables
    with app.app_context():
        db.create_all()

        # Optional startup sync from inventory_config.csv.
        if os.getenv("AUTO_SYNC_INVENTORY_CONFIG", "1") == "1":
            seed_database(update_existing=False)

    app.run(debug=True)