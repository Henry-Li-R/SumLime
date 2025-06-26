from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Needed for plugin access

@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    response = data.get("response", "")
    
    # Placeholder: dummy output
    result = {
        "claims": [
            {
                "text": "The Eiffel Tower is 900 meters tall",
                "supported": False,
                "score": 0.12
            },
            {
                "text": "The Eiffel Tower is located in Berlin",
                "supported": False,
                "score": 0.18
            }
        ]
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)