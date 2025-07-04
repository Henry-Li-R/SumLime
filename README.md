


# Hallucination Detection API (MVP)

This project is a minimal implementation of a hallucination detection service for AI-generated text (e.g., ChatGPT responses). The goal is to identify factual claims in an AI response and verify whether they are supported by real-world data available via web search.

## 💡 Project Goal

To build a working prototype of a hallucination detection API that can be integrated into tools like ChatGPT as a plugin.

## 🔁 Processing Pipeline

1. Split response into claims
2. Search web for each claim (stub for now)
3. Compute similarity score
4. Return support status per claim

## 🧪 Example Output

```json
{
  "claims": [
    {
      "text": "The Eiffel Tower is 900 meters tall",
      "supported": false,
      "score": 0.12
    },
    {
      "text": "The Eiffel Tower is located in Berlin",
      "supported": false,
      "score": 0.18
    }
  ]
}
```

## 🔌 API Endpoint

**POST** `/check`  
Request body:
```json
{ "response": "ChatGPT output text here." }
```

## 🔧 Stack

- Python + Flask
- `sentence-transformers`
- (Planned) SerpAPI or DuckDuckGo search for live snippets
- (Planned) Claim extractor based on NER or factuality model

## 📦 Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then visit: `http://localhost:5000/check`

## 🛠 Future Work

- Smarter claim extraction (factual NER or GPT-assisted)
- Real web search integration
- Improve scoring mechanism (alignment-aware)
- Deploy as a public ChatGPT plugin (Render or Railway) or as a standalone API
- Add logging, error handling, and test coverage

## 📄 License

Apache 2.0 — see `LICENSE`