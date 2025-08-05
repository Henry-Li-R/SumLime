from flask_cors import CORS
from flask import Flask, request, jsonify
from core.pipeline import summarize

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST"])

@app.route("/summarize", methods=["POST"])
def summarize_prompts():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Missing 'prompt' in request"}), 400
    result = summarize(prompt, ["deepseek", "gemini"])
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5050)