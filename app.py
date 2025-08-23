from sqlalchemy.orm import selectinload
from flask_cors import CORS
from flask import Flask, request, jsonify, g
from dotenv import load_dotenv
load_dotenv()
import os

from core.pipeline import summarize
from core.providers.models import ChatSession, ChatTurn
from db import db
from auth import auth_required

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST"])

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chat.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/api/summarize", methods=["POST"])
@auth_required
def summarize_prompts():
    data = request.get_json()
    prompt = data.get("prompt", "")
    models = data.get(
        "models",
        [
            "gemini",
        ],
    )
    chat_session = data.get("chatSession", None)
    summary_model = data.get("summary_model", "gemini")
    llm_anonymous = data.get("llm_anonymous", True)

    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400

    result = summarize(
        prompt,
        models,
        chat_session=chat_session,
        summary_model=summary_model,
        title_model="gemini", # avoid changing this default
        llm_anonymous=llm_anonymous,
    )
    return jsonify(result)

@app.route("/api/sessions", methods=["GET"])
@auth_required
def list_sessions():
    sessions = (
        ChatSession.query
        .filter_by(user_id=g.user_id)
        .order_by(ChatSession.last_used.desc()).all()
    )
    return jsonify(
        [
            {"id": s.id, "title": s.title, "last_used": s.last_used.isoformat()}
            for s in sessions
        ]
    )

@app.route("/api/sessions/<int:session_id>", methods=["GET"])
@auth_required
def get_session_messages(session_id: int):
    turns = ChatSession.query.get(session_id).turns

    def pack_turn(t: ChatTurn):
        outs = t.outputs or []

        summarizer = next((o for o in outs if o.provider == "summarizer"), None) # pyright: ignore
        base = [o for o in outs if o.provider not in ("user", "summarizer")] # pyright: ignore

        responses = []
        if summarizer:
            responses.append(
                {"provider": summarizer.provider, "content": summarizer.content}
            )
        responses.extend({"provider": o.provider, "content": o.content} for o in base)

        return {
            "turn_id": t.id,
            "created_at": t.created_at.isoformat(),
            "prompt": t.prompt,
            "responses": responses,
        }

    return jsonify([pack_turn(t) for t in turns])


if __name__ == "__main__":
    app.run(debug=True, port=5050)
