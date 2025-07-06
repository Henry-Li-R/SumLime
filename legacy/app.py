#from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from core.pipeline import analyze_response

app = Flask(__name__)
CORS(app)  # Needed for plugin access
#load_dotenv()  # Load environment variables from .env file


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    response = data.get("response", "")
    result = analyze_response(response)

    return jsonify(result)
