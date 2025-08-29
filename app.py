from sqlalchemy.orm import selectinload
from flask_cors import CORS
from flask import Flask, request, jsonify, g, abort
from dotenv import load_dotenv

load_dotenv()
import os

from core.pipeline import summarize
from core.providers.models import ChatSession, ChatTurn
from db import db
from auth import auth_required, set_rls_claims

app = Flask(__name__)

# Allow CORS from configurable origins.  Railway sets FRONTEND_URL to the
# deployed Vercel URL, but fall back to allowing all origins so local testing
# still works without additional configuration.
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
_allow_headers = ["Content-Type", "Authorization"]
if _cors_origins == "*":
    CORS(app, supports_credentials=True, allow_headers=_allow_headers)
else:
    CORS(
        app,
        origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
        supports_credentials=True,
        allow_headers=_allow_headers,
    )

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///chat.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/healthz", methods=["GET"])
def health_check():
    """Liveness probe endpoint used by Railway.

    It avoids touching the database or any external services so that the
    platform can reliably verify the container is running.
    """
    return jsonify({"status": "ok"})


@app.route("/api/summarize", methods=["POST", "OPTIONS"])
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
        title_model="gemini",  # avoid changing this default
        llm_anonymous=llm_anonymous,
    )
    return jsonify(result)


@app.route("/api/sessions", methods=["GET", "OPTIONS"])
@auth_required
def list_sessions():
    sessions = db.session.execute(
        db.select(ChatSession)
        .filter_by(user_id=g.user_id)
        .order_by(ChatSession.last_used.desc())
    ).scalars().all()
    return jsonify(
        [
            {"id": s.id, "title": s.title, "last_used": s.last_used.isoformat()}
            for s in sessions
        ]
    )


@app.route("/api/sessions/<int:session_id>", methods=["GET", "OPTIONS"])
@auth_required
def get_session_messages(session_id: int):
    session_obj = db.session.get(ChatSession, session_id)
    if session_obj is None:
        abort(404)
    turns = session_obj.turns

    def pack_turn(t: ChatTurn):
        outs = t.outputs or []

        summarizer = next(
            (o for o in outs if o.summarizer_prompt is not None), None
        )  # pyright: ignore
        base = [
            o for o in outs if o.summarizer_prompt is None
        ]  # pyright: ignore

        responses = []
        if summarizer:
            responses.append(
                {"provider": "summarizer", "content": summarizer.content}
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
