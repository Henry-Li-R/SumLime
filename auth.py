# auth.py
import os
import uuid
import functools
import jwt
from flask import request, g, abort
from jwt import PyJWKClient, InvalidTokenError
from sqlalchemy import text

from db import db
from core.providers.models import (
    Profile,
)  # Profile(id UUID PK), ChatSession uses user_id UUID FK

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

_jwk_client = PyJWKClient(JWKS_URL)


def _verify_supabase_jwt(token: str) -> dict:
    signing_key = _jwk_client.get_signing_key_from_jwt(token).key
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["ES256"],
        audience="authenticated",
        options={"require": ["exp", "iat", "sub"]},
    )

    # Optional issuer check
    iss = payload.get("iss", "")
    if SUPABASE_URL not in iss:
        raise InvalidTokenError("Issuer mismatch")
    return payload


def auth_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # CORS preflight requests hit the endpoint with the OPTIONS method and
        # without authorization headers.  Skip authentication so that browsers
        # can complete the preflight successfully.
        if request.method == "OPTIONS":
            return ("", 204)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            abort(401)
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = _verify_supabase_jwt(token)
        except Exception as e:
            print(str(e))
            abort(401)

        g.user_id = payload["sub"]  # UUID string from Supabase Auth
        ensure_profile_exists(g.user_id)

        set_rls_claims(g.user_id) # For RLS use

        return fn(*args, **kwargs)

    
    return wrapper


def ensure_profile_exists(user_id_str: str) -> None:
    # Convert to UUID for the ORM model if you used UUID(as_uuid=True)
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        abort(400)  # malformed sub

    # Fast path: GET by PK; SQLAlchemy 2.x: db.session.get
    exists = db.session.get(Profile, user_uuid)
    if exists:
        return
    # When user signs up, they exist in auth.users, and not yet in Profile
    db.session.add(Profile(id=user_uuid))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # If another request raced and created it, ignore

# Allow db operations with RLS on
def set_rls_claims(user_id: str):
    # Minimal claims for auth.uid() and auth.role()
    db.session.execute(
        text("select set_config('request.jwt.claim.sub', :sub, true)"),
        {"sub": user_id},
    )
    db.session.execute(
        text("select set_config('request.jwt.claim.role', 'authenticated', true)")
    )
