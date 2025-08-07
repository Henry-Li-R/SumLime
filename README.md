# Multi-LLM Playground

A simple web platform to interact with and compare responses from multiple large language models (LLMs), with optional summarization and hallucination detection support.

## 🔧 Core Features

- Send prompts to **any supported LLM**
- Select one or more models to compare outputs
- Summarize or contrast results using another LLM (e.g. GPT-4o)
- Optional: detect hallucinations by cross-checking with other models or web sources

## 💡 Use Cases

- Benchmarking different LLMs for factual reliability, writing style, reasoning, etc.
- Aggregating outputs to improve confidence
- Lightweight multi-model access without manually switching tools
- Fact-checking using model agreement or web validation (optional)

## ⚙️ Stack

| Layer        | Tech                          |
|--------------|-------------------------------|
| Frontend     | React + Tailwind (planned)    |
| Backend      | Flask API                     |
| Models       | OpenAI, Anthropic, DeepSeek, Gemini |
| Storage/Auth | Supabase (planned)            |
| Deployment   | Render/Vercel                 |

## 🚀 Setup (Backend Only)

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
DEEPSEEK_API_KEY=...
GOOGLE_API_KEY=...
```

Start the Flask server:

```bash
flask --app app --debug run
```

## 🧪 Example API Usage

```http
POST /verify
{
  "prompt": "Explain quantum entanglement in simple terms.",
  "models": ["gemini", "deepseek", "claude"]
}
```

Response:
```json
{
  "results": {
    "gemini": "...",
    "deepseek": "...",
    "claude": "..."
  },
  "summary": "All models agree on the general concept, but Claude emphasizes..."
}
```

## 🛣 Roadmap

- [ ] Frontend: multi-select model UI, input panel, output view
- [ ] Cross-LLM summary + contradiction flagging
- [ ] Chat history database
- [ ] Rate limit or token usage tracking
- [ ] Web-based fact-checking (optional module)
- [ ] Markdown + LaTeX formatting toggle
- [ ] Auth + personal prompt history

## 🔍 Related Tools

- Poe (Quora)
- LMArena
- Perplexity (for web-search validation)