def extract_claims(text):
    """
    Naively split the input text by periods into candidate claims.
    Filters out short or empty fragments.
    """
    raw_sentences = text.split(".")
    return [sent.strip() for sent in raw_sentences if len(sent.strip()) > 10]
