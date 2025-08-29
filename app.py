from flask_cors import CORS
from flask import Flask, request, jsonify, g, abort
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

load_dotenv()
import os

from core.pipeline import summarize
from core.providers.models import ChatSession, ChatTurn
from db import db
from auth import auth_required

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "https://sum-lime.vercel.app",  # production
                "https://sum-lime-3f6839ak1-henry-lis-projects-6da959dc.vercel.app", # staging
                "https://sum-lime-git-staging-fixes-henry-lis-projects-6da959dc.vercel.app", # alt for above
            ]
        },
    },
    allow_headers=["Authorization", "Content-Type"],
    methods=["GET", "POST", "OPTIONS"],
    max_age=600,
    supports_credentials=False,  # set True only if you actually use cookies
)


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///chat.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.errorhandler(Exception)
def handle_exception(e):
    # HTTPException already has .code/.name/.description
    if isinstance(e, HTTPException):
        status = e.code or 500
        message = (e.description or "").strip() or e.name or "Error"
    else:
        status = 500
        message = (str(e) or "").strip() or "Internal Server Error"

    payload = {
        "message": message,  # human-readable, short
    }
    return jsonify(payload), status


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
        title_model="gemini",  # avoid changing this default
        llm_anonymous=llm_anonymous,
    )
    return jsonify(result)


@app.route("/api/sessions", methods=["GET"])
@auth_required
def list_sessions():
    sessions = (
        db.session.execute(
            db.select(ChatSession)
            .filter_by(user_id=g.user_id)
            .order_by(ChatSession.last_used.desc())
        )
        .scalars()
        .all()
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
    session_obj = db.session.get(ChatSession, session_id)
    if session_obj is None:
        abort(404)
    turns = session_obj.turns

    def pack_turn(t: ChatTurn):
        outs = t.outputs or []

        summarizer = next(
            (o for o in outs if o.summarizer_prompt is not None), None  # type: ignore
        )  # pyright: ignore
        base = [
            o for o in outs if o.summarizer_prompt is None  # type: ignore
        ]  # pyright: ignore

        responses = []
        if summarizer:
            responses.append({"provider": "summarizer", "content": summarizer.content})
        responses.extend({"provider": o.provider, "content": o.content} for o in base)

        return {
            "turn_id": t.id,
            "created_at": t.created_at.isoformat(),
            "prompt": t.prompt,
            "responses": responses,
        }

    return jsonify([pack_turn(t) for t in turns])  # type: ignore


if __name__ == "__main__":
    app.run(port=5050, debug=True)
