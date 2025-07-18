from core.providers.deepseek import DeepSeekProvider
#from core.providers.chatgpt import ChatGPTProvider
#from core.providers.claude import ClaudeProvider
from core.providers.gemini import GeminiProvider

MODEL_PROVIDERS = {
    "deepseek": DeepSeekProvider(),
    #"chatgpt": ChatGPTProvider(),
    #"claude": ClaudeProvider(),
    "gemini": GeminiProvider(),
}

def summarize(prompt: str,
              models: list[str],
              summary_model: str = "gemini",
              llm_anonymous: bool = True) -> dict:
    results = {}
    for model in models:
        results[model] = MODEL_PROVIDERS[model].query(prompt)

    summary_input = "\n\n".join(
        [f"{('LLM ' + str(i)) if llm_anonymous else model.upper()}:\n{output}" for i, (model, output) in enumerate(results.items(), start=1)]
    )

    summary_prompt = f"""Compare and summarize the content of the following responses to the same prompt. Focus on similarities, differences in reasoning, and any ambiguities or omissions. Do not evaluate which model is better.

Prompt:\n\n
{prompt}\n\n
LLM responses:\n\n
{summary_input}
"""
    summary = MODEL_PROVIDERS[summary_model].query(summary_prompt)

    return {
        "results": results,
        "summary": summary,
    }
