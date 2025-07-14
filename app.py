from flask import Flask, request, jsonify
from core.pipeline import summarize

app = Flask(__name__)

@app.route("/summarize", methods=["POST"])
def summarize_prompts():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400
    result = summarize(prompt)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)