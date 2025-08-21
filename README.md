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
GEMINI_API_KEY=...
```

Start the Flask server:

```bash
flask --app app --debug run
```

## 🧪 Example API Usage



## 🛣 Roadmap

- [ ] Frontend: multi-select model UI, input panel (with dynamic sending...visual response), output view (clear separation of user prompt and model responses)
- [ ] Cross-LLM summary
- [ ] SSE streaming (messages + claim updates)
- [ ] Chat history database
- [ ] Rate limit or token usage tracking
- [ ] LaTeX copy-paste
- [ ] Auth + personal prompt history

## 🔍 Related Tools

- Poe
- LMArena