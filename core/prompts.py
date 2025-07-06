# Deprecated
def get_verification_prompt(claim: str) -> str:
    """Build a prompt given a factual claim."""
    return f"""You are a fact-checking assistant.
Assess whether the claim is supported.

Claim: "{claim}"

Reply with "Supported", "Not Supported", or "Uncertain", followed by a short explanation.
"""