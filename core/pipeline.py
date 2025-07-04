from .extractor import extract_claims
from .search import search_snippets
from .scorer import score_claim

def analyze_response(response_text):
    """
    Full pipeline: extract claims → search → score → summarize results.
    """
    claims = extract_claims(response_text)
    results = []

    for claim in claims:
        snippets = search_snippets(claim)
        supported, score = score_claim(claim, snippets)
        results.append({
            "text": claim,
            "supported": supported,
            "score": round(score, 3)
        })

    return {"claims": results}
