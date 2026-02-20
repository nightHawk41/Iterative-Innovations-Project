from flask import Flask

app = Flask(__name__)

# This is the route that will be called when the frontend makes a request to /test
@app.route("/test") 
def test_route():
    return {"message": ["Hello", "from", "Flask"]}

if __name__ == "__main__":
    app.run(debug=True)