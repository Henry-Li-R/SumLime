import { useState } from "react";
import ReactMarkdown from "react-markdown";

type LLMResponse = {
  results: Record<string, string>,
  summary: string
};

function App() {
  const [page, setPage] = useState(1);
  const [prompt, setPrompt] = useState("");
  const [responses, setResponses] = useState<LLMResponse | null>(null);

  const modelKeys = responses ? Object.keys(responses.results) : [];
  const totalPages = responses ? modelKeys.length + 1 : 1;

  const showSummary = page === 1;
  const currentModel = modelKeys[page - 2]; // page 2 maps to index 0

  const fetchSummary = async () => {
    if (!prompt.trim()) return;

    const res = await fetch("http://localhost:5050/summarize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        models: ["gemini", "deepseek"],
        summary_model: "gemini",
        llm_anonymous: true,
      }),
    });

    const data = await res.json();
    setResponses(data);
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-between px-4 py-6">
      {/* Output panel */}
      <div className="max-w-4xl mx-auto flex-grow">
        <div className="bg-white p-6 rounded-lg shadow mb-4">
          {responses ? (
            showSummary ? (
              <>
                <h2 className="text-xl font-bold mb-2">🧠 Summary</h2>
                <ReactMarkdown>{responses.summary}</ReactMarkdown>
              </>
            ) : (
              <>
                <h2 className="text-xl font-bold mb-2">🤖 {currentModel}</h2>
                <ReactMarkdown>{responses.results[currentModel]}</ReactMarkdown>
              </>
            )
          ) : (
            <p className="text-gray-500">Enter a prompt to get started.</p>
          )}
        </div>

        {/* Pagination */}
        {responses && (
          <div className="flex justify-between items-center text-sm">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
            >
              ◀ Prev
            </button>
            <span>
              Page {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
            >
              Next ▶
            </button>
          </div>
        )}
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
    </div>
  );
}

export default App;
