# Multi-LLM Playground

A simple web platform to interact with and compare responses from multiple large language models (LLMs), with optional summarization and hallucination detection support.

## 🔧 Core Features

- Send prompts to **any supported LLM**
- Select one or more models to compare outputs
- Summarize or contrast results using another LLM (e.g. GPT-4o)

## 💡 Use Cases

- Benchmarking different LLMs for factual reliability, writing style, reasoning, etc.
- Aggregating outputs to improve confidence
- Lightweight multi-model access without manually switching tools

## ⚙️ Stack

| Layer        | Tech                          |
|--------------|-------------------------------|
| Frontend     | React + Tailwind              |
| Backend      | Flask API                     |
| Models       | OpenAI, Anthropic, DeepSeek, Gemini |
| Storage/Auth | Supabase            |
| Deployment   | Render/Vercel                 |

## 📦 Currently Available Models

Enabled in `core/pipeline.py`:

- DeepSeek (`deepseek-chat`)
- Gemini (`gemini-2.0-flash-lite`) — also used as the default summarizer and title model

## 🚀 Setup (Backend Only)

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
DEEPSEEK_API_KEY=...
GEMINI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
DATABASE_URL=sqlite:///chat.db
```

Start the Flask server:

```bash
flask --app app --debug run
```

## 🧪 Example API Usage

All `/api/*` endpoints require a Supabase JWT in the `Authorization` header.

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" \
  -X POST http://localhost:5050/api/summarize \
  -d '{
    "prompt": "Compare the strengths of Rust vs Go.",
    "models": ["gemini", "deepseek"],
    "summary_model": "gemini",
    "llm_anonymous": true
  }'
```


## 🛣 Roadmap
- [+] Cross-LLM summary
- [+] LaTeX copy-paste
- [+] SSE streaming (messages + claim updates)
- [ ] Rate limit or token usage tracking
- [ ] Settings for choosing models (ordered list), summarizer on/off; handling different settings across sessions or settings changes inside session, db persistence potentially required
- [+] Retries upon transient API errors
- [ ] Option to pause generating response
- [ ] Improve scalability with long or many chat sessions (e.g. delete unused chat sessions)
- [ ] Settings panel (e.g. delete all chat sessions, system instructions)


## 🔍 Related Tools

- Poe
- LMArena
