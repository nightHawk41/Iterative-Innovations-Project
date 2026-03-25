import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from app import db
from app.utils.seed import seed_database
from app.models.item_slot import ItemSlot

app = Flask(__name__)
CORS(app)

# Define the path to the SQLite database file
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'vending.db')

# Configure the SQLAlchemy database URI to point to the SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object with the Flask app
db.init_app(app)

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
        return jsonify(summary), 400

    return jsonify(summary), 200

if __name__ == "__main__":
    # Create the database tables
    with app.app_context():
        # Ensure all model metadata is registered before create_all.
        _ = ItemSlot
        db.create_all()

        # Optional startup sync from inventory_config.csv.
        if os.getenv("AUTO_SYNC_INVENTORY_CONFIG", "1") == "1":
            seed_database(update_existing=False)

    app.run(debug=True)