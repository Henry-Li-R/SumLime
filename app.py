from sqlalchemy.orm import selectinload
from flask_cors import CORS
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from core.pipeline import summarize
from core.providers.models import ChatSession, ChatTurn
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
        title_model="gemini",
        llm_anonymous=llm_anonymous,
    )
    return jsonify(result)


@app.route("/sessions", methods=["GET"])
def list_sessions():
    sessions = ChatSession.query.order_by(ChatSession.last_used.desc()).all()
    return jsonify(
        [
            {"id": s.id, "title": s.title, "last_used": s.last_used.isoformat() + "Z"}
            for s in sessions
        ]
    )


@app.route("/sessions/<int:session_id>", methods=["GET"])
def get_session_messages(session_id: int):

    turns = (
        ChatTurn.query.filter_by(session_id=session_id)
        .order_by(ChatTurn.created_at.asc())  # chronological
        .options(selectinload(ChatTurn.outputs))  # avoid N+1 # pyright: ignore
        .all()
    )

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
