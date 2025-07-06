from flask import Flask, request, jsonify
from core.pipeline import verify_claim

app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()
    claim = data.get("claim", "")
    if not claim:
        return jsonify({"error": "Missing 'claim' in request"}), 400
    result = verify_claim(claim)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)