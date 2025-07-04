from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def score_claim(claim, snippets, threshold=0.7):
    claim_vec = model.encode(claim, convert_to_tensor=True)
    for snippet in snippets:
        snippet_vec = model.encode(snippet, convert_to_tensor=True)
        score = util.pytorch_cos_sim(claim_vec, snippet_vec).item()
        if score > threshold:
            return True, score
    return False, 0.0
