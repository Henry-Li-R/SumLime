import { useEffect, useState, useRef } from 'react'
import { useAuth } from './auth/useAuth.ts'
import { apiFetch } from './lib/api.ts'

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import rehypeMathCopy from "./math/rehypeMathCopy.ts"
import { MathInline, MathBlock } from "./math/MathWrappers.tsx"

type Session = { id: number; title: string; last_used: string };
type LLMResponse = { provider: string; content: string };
type ChatTurn = {
  turn_id: number;
  created_at: string;
  prompt: string;
  responses: LLMResponse[];
}

const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:5050";


export default function HomeChat() {
  const { user, signOut } = useAuth()

  const [prompt, setPrompt] = useState("");
  const [chatSession, setChatSession] = useState<number | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(() => window.matchMedia("(min-width: 768px)").matches);

  // Per-turn provider selection (default to summarizer if present)
  const [selectedProviderByTurn, setSelectedProviderByTurn] = useState<Record<number, string>>({});
  const pickDefaultProvider = (responses: LLMResponse[]) => {
    const hasSummarizer = responses.find((r) => r.provider === "summarizer");
    return hasSummarizer ? "summarizer" : (responses[0]?.provider ?? "");
  };

  const bottomRef = useRef<HTMLDivElement>(null);

  /* LLM API error handling */
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  // helper: turn unknown errors / bad responses into short strings
  function toUserMessage(err: unknown): string {
    if (!err) return "Something went wrong.";
    if (typeof err === "string") return err;

    // If someone threw an Error()
    if (err instanceof Error) return err.message || "Something went wrong.";

    // Expecting backend JSON: { message, code }
    const anyErr = err as { message?: string; code?: number };
    const msg = anyErr.message || "Something went wrong.";
    return msg;
  }


  useEffect(() => {
    apiFetch(`${API_BASE}/api/sessions`)
      .then((r) => r.json())
      .then(setSessions)
      .catch(() => { });
  }, []);

  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chatTurns]);

  const loadSession = async (id: number) => {
    setChatSession(id);
    try {
      const res = await apiFetch(`${API_BASE}/api/sessions/${id}`);
      if (res.ok) {
        const data: ChatTurn[] = await res.json();
        setChatTurns(data);
        // Initialize per-turn default provider (summarizer first if available)
        setSelectedProviderByTurn(
          Object.fromEntries(
            data.map((t) => [t.turn_id, pickDefaultProvider(t.responses)])
          )
        );
        // After loading a session, ensure scroll to bottom
        setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "auto", block: "end" }), 0);
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

    setPrompt("");
    setIsSending(true);
    setErrorMsg("");

    // Create a temporary turn so UI can stream in provider chunks
    const tempTurnId = Date.now();
    setChatTurns((prev) => [
      ...prev,
      { turn_id: tempTurnId, created_at: new Date().toISOString(), prompt, responses: [] },
    ]);

    try {
      const res = await apiFetch(`${API_BASE}/api/summarize`, {
        method: "POST",
        body: JSON.stringify({
          prompt,
          models: ["gemini", "deepseek"],
          chatSession: chatSession,
          summary_model: "gemini",
          llm_anonymous: true,
        }),
      });

      if (!res.ok || !res.body) {
        let serverMsg = "Request failed.";
        try {
          const maybe = await res.json();
          serverMsg = toUserMessage(maybe);
        } catch {
          // ignore JSON parse errors; keep generic text
        }
        setErrorMsg(serverMsg);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      const accum: Record<string, string> = {};

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const payload = JSON.parse(part.slice("data: ".length));
          if (payload.final) {
            const final = payload.final;
            setChatSession(final.session_id ?? null);
            // Replace temporary turn id with real one and timestamp
            setChatTurns((prev) =>
              prev.map((t) =>
                t.turn_id === tempTurnId
                  ? { ...t, turn_id: final.turn_id, created_at: final.created_at }
                  : t
              )
            );
            // Default provider selection for the new turn
            const finalResponses: LLMResponse[] = Object.entries(accum).map(
              ([provider, content]) => ({ provider, content })
            );
            setSelectedProviderByTurn((prev) => {
              const { [tempTurnId]: _old, ...rest } = prev;
              return {
                ...rest,
                [final.turn_id]: pickDefaultProvider(finalResponses),
              };
            });
            // Refresh sessions list
            try {
              const sessRes = await apiFetch(`${API_BASE}/api/sessions`);
              if (sessRes.ok) {
                const sess = await sessRes.json();
                setSessions(sess);
              }
            } catch (err) {
              console.error(err);
            }
          } else {
            const { provider, chunk } = payload as {
              provider: string;
              chunk: string;
            };
            
            accum[provider] = (accum[provider] || "") + chunk;
            setChatTurns((prev) =>
              prev.map((t) => {
                if (t.turn_id !== tempTurnId) return t;
                const responses = [...t.responses];
                const existing = responses.find((r) => r.provider === provider);
                if (existing) existing.content += chunk;
                else { 
                  responses.push({ provider, content: chunk });
                }
                return { ...t, responses };
              })
            );
          }
        }
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(toUserMessage(err));
    } finally {
      setIsSending(false);
    }
  };


  return (
    <div className={`min-h-screen w-screen bg-gray-50 md:flex gap-4 md:gap-6 lg:gap-8 px-4 md:px-6 lg:px-8 py-6 pt-12`}>
      <header className="fixed top-0 inset-x-0 z-50 bg-white/90 backdrop-blur border-b border-gray-200">
        <div className="h-12 flex items-center justify-between px-4 md:px-6 lg:px-8">
          {/* Left: menu toggle + title */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
              aria-label="Toggle sidebar"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                viewBox="0 0 24 24"
              >
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-sm font-semibold text-gray-700">Menu</h1>
          </div>

          {/* Right: auth info */}
          <div className="flex items-center space-x-4 text-sm text-gray-700">
            {user ? (
              <>
                <span>Signed in as {user.email}</span>
                <button
                  onClick={signOut}
                  className="text-indigo-600 hover:underline"
                >
                  Sign out
                </button>
              </>
            ) : (
              <span>Not signed in</span>
            )}
          </div>
        </div>
      </header>
      <aside className={`fixed top-12 left-0 bottom-0 z-40 bg-white w-64 md:w-80 lg:w-96 transition-transform duration-300 border border-gray-200 rounded-md px-4 md:px-5 py-3 overflow-y-auto ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
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
          <ul className="space-y-2 list-none pl-0">
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
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Output panel */}
        <div className="bg-white p-6 rounded-lg shadow mb-4 flex-1 min-h-0 overflow-y-auto pb-24">

          {/* Chat history for the selected session */}
          {chatTurns.length > 0 ? (
            <div className="mb-6 space-y-3 w-full max-w-none">
              <h2 className="text-lg font-semibold">Chat history</h2>
              {chatTurns.map((t, idx) => (
                <div key={t.turn_id ?? idx} className="border rounded p-3">
                  <div className="text-xs text-gray-500 mb-2">
                    Turn {idx + 1}
                  </div>

                  <div className="mb-2">
                    <div className="text-xs font-semibold text-gray-600">Prompt</div>
                    <div className="whitespace-pre-wrap">{t.prompt}</div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600">Model:</span>
                      <select
                        className="border rounded px-2 py-1 text-sm"
                        value={selectedProviderByTurn[t.turn_id] ?? pickDefaultProvider(t.responses)}
                        onChange={(e) =>
                          setSelectedProviderByTurn((prev) => ({ ...prev, [t.turn_id]: e.target.value }))
                        }
                      >
                        {t.responses.map((r) => (
                          <option key={r.provider} value={r.provider}>
                            {r.provider.toUpperCase()}
                          </option>
                        ))}
                      </select>
                    </div>
                    {(() => {
                      const sel = selectedProviderByTurn[t.turn_id] ?? pickDefaultProvider(t.responses);
                      const r = t.responses.find((x) => x.provider === sel);
                      if (!r) return null;
                      return (
                        <div className="border rounded p-2">
                          <div className="text-xs text-gray-500 mb-1">{r.provider.toUpperCase()}</div>
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
                      );
                    })()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            chatTurns.length === 0 && <p className="text-gray-500">Enter a prompt or pick a chat to get started.</p>
          )}

          {/* LLM API Error Message Section */}
          {errorMsg && (
            <div className="mb-3">
              <div className="flex items-start justify-between rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
                <div className="pr-2">
                  {errorMsg}
                </div>
                <button
                  onClick={() => setErrorMsg(null)}
                  className="ml-2 text-red-700 hover:underline"
                  aria-label="Dismiss error"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Prompt Input Section */}
        <div className="fixed bottom-0 inset-x-0 z-40 bg-gray-50/95 backdrop-blur border-t border-gray-200 px-4 md:px-6 lg:px-8 py-3">
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

        <div ref={bottomRef} />
      </main>
    </div>
  );

}