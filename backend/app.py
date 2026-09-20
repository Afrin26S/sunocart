import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from mock_ai import extract_shopping_intent  # swap for bedrock_ai later (currently blocked — see notes)
from product_search import search_products
from explain import explain_results
from warranty_extract import guess_invoice_fields
from warranty_lookup import find_warranty

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "SunoCartWarranty")
USER_ID = os.getenv("USER_ID", "demo-user-001")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
CORS(app)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static_frontend")


@app.get("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/style.css")
def serve_css():
    return send_from_directory(FRONTEND_DIR, "style.css")


@app.get("/app.js")
def serve_js():
    return send_from_directory(FRONTEND_DIR, "app.js")

s3_client = boto3.client("s3", region_name=AWS_REGION)
textract_client = boto3.client("textract", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
warranty_table = dynamodb.Table(DYNAMODB_TABLE)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
        return jsonify({"intent": intent, "products": products, "message": message})
    except Exception as error:
        print("Shopping API error:", error)
        return jsonify({"error": "Unable to process your request."}), 500


@app.post("/api/warranty/extract")
def warranty_extract_route():
    """Upload an invoice image -> real S3 -> real Textract -> heuristic guess.
    Nothing is saved yet — the frontend shows these as EDITABLE fields."""
    if "invoice" not in request.files:
        return jsonify({"error": "Please attach an invoice image."}), 400

    file = request.files["invoice"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Please upload a JPG or PNG photo of the invoice."}), 400
    if not S3_BUCKET:
        return jsonify({"error": "S3_BUCKET is not configured in backend/.env"}), 500

    extension = file.filename.rsplit(".", 1)[1].lower()
    s3_key = f"invoices/{USER_ID}/{uuid.uuid4().hex}.{extension}"

    try:
        s3_client.upload_fileobj(file, S3_BUCKET, s3_key)

        textract_response = textract_client.detect_document_text(
            Document={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
        )
        lines = [
            block["Text"]
            for block in textract_response.get("Blocks", [])
            if block["BlockType"] == "LINE"
        ]
        raw_text = "\n".join(lines)

        guessed = guess_invoice_fields(raw_text)
        guessed["s3_key"] = s3_key
        return jsonify(guessed)

    except ClientError as error:
        print("Warranty extract error:", error)
        return jsonify({"error": f"AWS error: {error.response['Error']['Message']}"}), 500


@app.post("/api/warranty/save")
def warranty_save():
    """Save the USER-CONFIRMED fields — never save raw guesses automatically."""
    data = request.get_json(silent=True) or {}
    product_name = str(data.get("product_name", "")).strip()
    purchase_date = str(data.get("purchase_date", "")).strip()
    warranty_text = str(data.get("warranty_text", "")).strip()
    s3_key = str(data.get("s3_key", "")).strip()

    if not product_name:
        return jsonify({"error": "Product name is required."}), 400

    product_id = uuid.uuid4().hex[:8]
    item = {
        "user_id": USER_ID,
        "product_id": product_id,
        "product_name": product_name,
        "purchase_date": purchase_date,
        "warranty_text": warranty_text,
        "invoice_s3_key": s3_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        warranty_table.put_item(Item=item)
        return jsonify(item)
    except ClientError as error:
        print("Warranty save error:", error)
        return jsonify({"error": f"AWS error: {error.response['Error']['Message']}"}), 500


@app.get("/api/warranty/list")
def warranty_list():
    try:
        response = warranty_table.query(KeyConditionExpression=Key("user_id").eq(USER_ID))
        return jsonify({"items": response.get("Items", [])})
    except ClientError as error:
        print("Warranty list error:", error)
        return jsonify({"error": f"AWS error: {error.response['Error']['Message']}"}), 500


@app.post("/api/warranty/ask")
def warranty_ask():
    """Voice/text warranty lookup, e.g. 'Mera mixer ka warranty kab tak hai?'
    Reads whatever is actually saved in DynamoDB — never invents an answer."""
    data = request.get_json(silent=True) or {}
    query_text = str(data.get("text", "")).strip()
    if not query_text:
        return jsonify({"error": "Please ask a question."}), 400

    try:
        response = warranty_table.query(KeyConditionExpression=Key("user_id").eq(USER_ID))
        items = response.get("Items", [])
        result = find_warranty(items, query_text)
        return jsonify(result)
    except ClientError as error:
        print("Warranty ask error:", error)
        return jsonify({"error": f"AWS error: {error.response['Error']['Message']}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

