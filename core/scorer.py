from sentence_transformers import CrossEncoder
from sentence_transformers import util

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def score_claim(claim, snippets, threshold=0.7):
    pairs = [(claim, snippet) for snippet in snippets]
    scores = model.predict(pairs)
    max_score = max(scores)
    max_score = float(max_score)
    return (max_score > threshold), max_score
