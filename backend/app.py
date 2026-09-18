from flask import Flask, request, jsonify
from flask_cors import CORS

from mock_ai import extract_shopping_intent  # swap for bedrock_ai later
from product_search import search_products
from explain import explain_results

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "SunoCart",
        "team": "Team Suno",
        "mode": "local-mock",
    })


@app.post("/api/shop")
def shop():
    data = request.get_json(silent=True) or {}
    user_text = str(data.get("text", "")).strip()

    if not user_text:
        return jsonify({"error": "Please provide a shopping request."}), 400
    if len(user_text) > 1000:
        return jsonify({"error": "Request is too long."}), 400

    try:
        intent = extract_shopping_intent(user_text)
        products = search_products(intent)
        message = explain_results(products, intent["language"])
        return jsonify({
            "intent": intent,
            "products": products,
            "message": message,
        })
    except Exception as error:
        print("Shopping API error:", error)
        return jsonify({"error": "Unable to process your request."}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)