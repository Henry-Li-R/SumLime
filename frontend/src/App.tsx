import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import rehypeMathCopy from "../utils/rehypeMathCopy.ts"
import { MathInline, MathBlock } from "../components/MathWrappers.tsx"

type Session = { id: number; title: string; last_used: string };
type LLMResponse = { provider: string; content: string };
type ChatTurn = {
  turn_id: number;
  created_at: string;
  prompt: string;
  responses: LLMResponse[];
}

const API_BASE = "http://localhost:5050";

function App() {
  const [prompt, setPrompt] = useState("");
  const [chatSession, setChatSession] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/sessions`)
      .then((r) => r.json())
      .then(setSessions)
      .catch(() => { });
  }, []);

  const loadSession = async (id: number) => {
    setChatSession(id);
    try {
      const res = await fetch(`${API_BASE}/sessions/${id}`);
      if (res.ok) {
        const data: ChatTurn[] = await res.json();
        setChatTurns(data);
      } else {
        setChatTurns([]);
      }
      setPrompt("");
    } catch {
      setChatTurns([]);
    }
  };

  const fetchSummary = async () => {
    if (!prompt.trim()) return;
    if (isSending) return;
    setIsSending(true);
    console.log("Prompt sent successfully");

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
      // Format `/summarize` response into a ChatTurn and append (preserve model order)
      const selectedModels = ["gemini", "deepseek"]; // [ ]: source from UI state if selectable
      const results = data?.results ?? {};

      const baseResponses = selectedModels
        .map((p) => {
          const content = results[p];
          if (content == null) return null;
          return { provider: p, content } as LLMResponse;
        })
        .filter(Boolean) as LLMResponse[];

      const summaryContent = results.summarizer ?? results.summary ?? null;
      const responses: LLMResponse[] =
        summaryContent != null
          ? [{ provider: "summarizer", content: summaryContent }, ...baseResponses]
          : baseResponses;
      const newTurn: ChatTurn = {
        turn_id: data.turn_id,
        created_at: data.created_at,
        prompt: data.prompt,
        responses,
      };

      setChatTurns((prev) => [...prev, newTurn]);

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
              setChatTurns([]);
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
                  className={`w-full text-left px-3 py-2 rounded border transition ${chatSession === s.id
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
            {chatTurns.length > 0 ? (
              <div className="mb-6 space-y-3 w-full max-w-none">
                <h2 className="text-lg font-semibold">Chat history</h2>
                {chatTurns.map((t, idx) => (
                  <div key={t.turn_id ?? idx} className="border rounded p-3">
                    <div className="text-xs text-gray-500 mb-2">
                      Turn {idx + 1} • {new Date(t.created_at + "Z").toLocaleString()}
                    </div>

                    <div className="mb-2">
                      <div className="text-xs font-semibold text-gray-600">Prompt</div>
                      <div className="whitespace-pre-wrap">{t.prompt}</div>
                    </div>

                    <div className="space-y-3">
                      {t.responses.map((r, i) => (
                        <div key={i} className="border rounded p-2">
                          <div className="text-xs text-gray-500 mb-1">
                            {r.provider.toUpperCase()}
                          </div>
                          <div className="whitespace-pre-wrap">
                            <ReactMarkdown
                              remarkPlugins={[remarkMath]}
                              rehypePlugins={[rehypeKatex, rehypeMathCopy]}
                              components={
                                {
                                  "math-inline": MathInline,
                                  "math-block": MathBlock,
                                } as unknown as import("react-markdown").Components
                              }
                            >
                              {r.content}
                            </ReactMarkdown>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              chatTurns.length === 0 && <p className="text-gray-500">Enter a prompt or pick a chat to get started.</p>
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
