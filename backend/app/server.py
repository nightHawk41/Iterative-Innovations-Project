import os
from flask import Flask
from flask_cors import CORS
from app import db

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

if __name__ == "__main__":
    # Create the database tables
    with app.app_context():
        db.create_all()
    app.run(debug=True)