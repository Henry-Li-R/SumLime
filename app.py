from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import Flask, request, jsonify

from dotenv import load_dotenv
load_dotenv()

from core.pipeline import summarize
from db import db

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST"])

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route("/summarize", methods=["POST"])
def summarize_prompts():
    data = request.get_json()
    prompt = data.get("prompt", "")
    models = data.get("models", ["gemini",])
    chat_session = data.get("chatSession", None)
    summary_model = data.get("summary_model", "gemini")
    llm_anonymous = data.get("llm_anonymous", True)
    
    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400
    
    result = summarize(prompt, 
                       models,
                       chat_session,
                       summary_model,
                       llm_anonymous,
                       )
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5050)