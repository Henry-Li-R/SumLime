import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

type Session = { id: number; title: string; last_used: string };
type Message = { role: string; provider: string | null; content: string; timestamp: string };

const API_BASE = "http://localhost:5050";

function App() {
  const [prompt, setPrompt] = useState("");
  const [chatSession, setChatSession] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/sessions`)
      .then((r) => r.json())
      .then(setSessions)
      .catch(() => {});
  }, []);

  const loadSession = async (id: number) => {
    setChatSession(id);
    try {
      const res = await fetch(`${API_BASE}/sessions/${id}`);
      if (res.ok) {
        const data: Message[] = await res.json();
        setMessages(data);
      } else {
        setMessages([]);
      }
      // Clear compare results when switching sessions
      setPrompt("");
    } catch {
      setMessages([]);
    }
  };

  const fetchSummary = async () => {
    if (!prompt.trim()) return;

    fetch(`${API_BASE}/summarize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        models: ["gemini", "deepseek"],
        chatSession: chatSession,
        summary_model: "gemini",
        llm_anonymous: true,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        // [ ] find more efficient solution than fetching all
        // chat messages every time
        loadSession(data.session_id);

        // Also refresh the sessions list so the left panel is up-to-date
        fetch(`${API_BASE}/sessions`)
          .then((r) => r.json())
          .then(setSessions)
          .catch(() => {});

      })
      .catch((err) => {
        console.error(err);
      });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex px-4 py-6">
      <aside className="w-1/2 bg-white border border-gray-200 rounded-md overflow-y-auto p-3">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-700">Chats</h2>
          <button
            className="text-xs px-2 py-1 border rounded hover:bg-gray-50"
            onClick={() => {
              setChatSession(null);
              setMessages([]);
              setPrompt("");
            }}
            title="Start a new chat"
          >
            + New
          </button>
        </div>

        {sessions.length === 0 ? (
          <div className="text-xs text-gray-500">No chats yet.</div>
        ) : (
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  onClick={() => loadSession(s.id)}
                  className={`w-full text-left px-3 py-2 rounded border transition ${
                    chatSession === s.id
                      ? "bg-gray-100 border-gray-300"
                      : "bg-white border-gray-200 hover:bg-gray-50"
                  }`}
                  title={new Date(s.last_used).toLocaleString()}
                > 
                  <div className="text-sm font-medium truncate">{s.title}</div>
                  <div className="text-[11px] text-gray-500">
                    {new Date(s.last_used).toLocaleString()}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </aside>
      <main className="flex-1 flex flex-col justify-between ml-4">
        {/* Output panel */}
        <div className="max-w-4xl mx-auto flex-grow">
          <div className="bg-white p-6 rounded-lg shadow mb-4">
            <>
              {/* Chat history for the selected session */}
              {messages.length > 0 ? (
                <div className="mb-6 space-y-3">
                  <h2 className="text-lg font-semibold">Chat history</h2>
                  {messages.map((m, idx) => (
                    <div key={idx} className="border rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">
                        {m.role.toUpperCase()} {m.provider ? `• ${m.provider}` : ""} • {new Date(m.timestamp).toLocaleString()}
                      </div>
                      <div className="whitespace-pre-wrap">
                        <ReactMarkdown>{m.content}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                messages.length === 0 && <p className="text-gray-500">Enter a prompt or pick a chat to get started.</p>
              )}
            </>
          </div>
        </div>

        {/* Prompt Input Section */}
        <div className="max-w-4xl mx-auto mt-6">
          <input
            type="text"
            placeholder="Enter your prompt..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                fetchSummary();
                console.log("Prompt sent successfully");
              }
            }}
            className="w-full border border-gray-300 rounded px-4 py-2 shadow"
          />
        </div>
      </main>
    </div>
  );
}

export default App;
