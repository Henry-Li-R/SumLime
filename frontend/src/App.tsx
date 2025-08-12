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
  const [isSending, setIsSending] = useState(false);

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
    if (isSending) return;
    setIsSending(true);

    try {
      const res = await fetch(`${API_BASE}/summarize`, {
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
      });

      const data = await res.json();

      // [ ] find more efficient solution than fetching all
      // chat messages every time
      await loadSession(data.session_id);

      // Also refresh the sessions list so the left panel is up-to-date
      try {
        const sessRes = await fetch(`${API_BASE}/sessions`);
        if (sessRes.ok) {
          const sess = await sessRes.json();
          setSessions(sess);
        }
      } catch (err) {
        console.error(err);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
      setPrompt("");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex px-4 py-6">
      <aside className="flex-none w-72 md:w-80 lg:w-96 bg-white border border-gray-200 rounded-md p-3 overflow-y-auto h-screen">
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
      <main className="flex-1 flex flex-col justify-between ml-4 overflow-y-auto h-screen">
        {/* Output panel */}
        <div className="bg-white p-6 rounded-lg shadow mb-4 flex-grow overflow-y-auto">
          {isSending && (
            <div className="mb-3 text-sm text-gray-500">
              Sending…
            </div>
          )}
          <>
            {/* Chat history for the selected session */}
            {messages.length > 0 ? (
              <div className="mb-6 space-y-3 w-full max-w-none">
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

        {/* Prompt Input Section */}
        <div className="mt-6">
          <input
            type="text"
            placeholder={isSending ? "Sending…" : "Enter your prompt..."}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isSending) {
                fetchSummary();
                console.log("Prompt sent successfully");
              }
            }}
            disabled={isSending}
            className="w-full border border-gray-300 rounded px-4 py-2 shadow disabled:opacity-50"
          />
        </div>
      </main>
    </div>
  );
}

export default App;
