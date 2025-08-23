# auth_verify.py
import os, time, uuid, requests, jwt
from jwt import InvalidTokenError
from flask import abort

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")   # e.g. https://<ref>.supabase.co
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/keys"

# simple in-process cache
_JWKS_CACHE = {"keys": None, "ts": 0}
_JWKS_TTL = 60 * 10  # 10 minutes

def _fetch_jwks() -> dict:
    # first try without headers (public by default)
    try:
        resp = requests.get(JWKS_URL, timeout=5)
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    # fallback: try with anon key (matches your curl success)
    if ANON_KEY:
        resp = requests.get(
            JWKS_URL,
            headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("Unable to fetch JWKS")

def _get_jwks() -> dict:
    now = time.time()
    if not _JWKS_CACHE["keys"] or now - _JWKS_CACHE["ts"] > _JWKS_TTL:
        _JWKS_CACHE["keys"] = _fetch_jwks()
        _JWKS_CACHE["ts"] = now
    return _JWKS_CACHE["keys"]

def verify_supabase_jwt(token: str) -> dict:
    # get unverified header to select the right key
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    if not kid:
        raise InvalidTokenError("missing kid")

    jwks = _get_jwks()
    try:
        jwk = next(k for k in jwks["keys"] if k["kid"] == kid)
    except StopIteration:
        # key rotation? refresh once and retry
        _JWKS_CACHE["keys"] = None
        jwks = _get_jwks()
        try:
            jwk = next(k for k in jwks["keys"] if k["kid"] == kid)
        except StopIteration:
            raise InvalidTokenError("kid not found in JWKS")

    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience="authenticated",
        options={"require": ["sub", "exp", "iat"]},
    )
    iss = payload.get("iss", "")
    if SUPABASE_URL not in iss:
        raise InvalidTokenError("issuer mismatch")
    return payload