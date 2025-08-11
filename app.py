from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import Flask, request, jsonify
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from core.pipeline import summarize
from db import db
from core.providers.models import ChatSession, ChatMessage

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

@app.route("/sessions", methods=["GET"])
def list_sessions():
    sessions = ChatSession.query.order_by(ChatSession.last_used.desc()).all()
    return jsonify([
        {"id": s.id, "title": s.title, "last_used": s.last_used.isoformat() + "Z"}
        for s in sessions
    ])

@app.route("/sessions/<int:session_id>", methods=["GET"])
def get_session_messages(session_id):
    msgs = (
        ChatMessage.query
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    return jsonify([
        {
            "role": m.role,
            "provider": m.provider,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() + "Z"
        }
        for m in msgs
    ])

if __name__ == "__main__":
    app.run(debug=True, port=5050)