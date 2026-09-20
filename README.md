# SunoCart 🎙️

**A voice-first shopping and warranty assistant — built for people who find shopping apps hard to use, starting with my own grandmother.**

Built solo by **Team Suno** for [First Commit](https://www.wemakedevs.org/aws/first-commit) — WeMakeDevs × AWS Bharat Builds Tour.

🔗 **Live app:** https://fzklqgngx6.execute-api.ap-south-1.amazonaws.com/
📝 **Blog / build story:** _(add your AWS Builder Center link here once published)_

---

## The problem

My dadi wants to buy a mixer grinder. She knows exactly what she needs — "something good for the house, under ₹2,000" — and saying that out loud is easy. Typing it into a shopping app, reading spec sheets, and comparing options is not. Months later, when something breaks, the invoice is buried somewhere and nobody remembers if it's still under warranty.

Voice search already exists in major shopping apps — this project doesn't pretend otherwise. What it adds is the part that doesn't exist yet: understanding a budget as a real filter, explaining a product in plain language, and remembering what you bought — across *any* seller, not just one platform — so you can ask about it again by voice, months later.

## What it does

**VoiceCart** — speak a request in Hindi or English ("mujhe 2000 ke andar mixer chahiye"), get results filtered by category and budget, with a spoken, comparative explanation instead of a bare product grid.

**WarrantyWallet** — upload a photo of any invoice, from any seller. The app extracts the product name, purchase date, and warranty details, shows them for confirmation (nothing is ever saved without the user reviewing it first), and saves the record. Later, ask about it by voice: *"Mera mixer ka warranty kab tak hai?"*

The two features share one underlying idea: discover → buy → save the invoice → ask about it whenever you need to. One connected product, not two separate demos.

## AWS architecture

| Service | Role |
|---|---|
| **AWS Lambda** | Runs the entire Flask backend (via a WSGI adapter) and serves the frontend directly |
| **Amazon API Gateway** | HTTP API routing all traffic to Lambda over HTTPS |
| **Amazon S3** | Private storage for uploaded invoice images |
| **Amazon Textract** | Extracts raw text from invoice photos (`detect_document_text`) |
| **Amazon DynamoDB** | Stores confirmed warranty records (`user_id` partition key, `product_id` sort key) |
| **AWS IAM** | Scoped execution role for the Lambda function |

**On Bedrock:** Amazon Bedrock access was blocked at the AWS account level days before submission. Per the organizers' own guidance that Bedrock isn't required for this track, the intent-extraction (`mock_ai.py`) and invoice-structuring (`warranty_extract.py`) layers run as rule-based modules instead, built with the same input/output contract a Bedrock call would use — a one-line swap once access clears.

## Project structure
SunoCart/
├── backend/
│ ├── app.py # Flask app — all API routes
│ ├── lambda_function.py # Lambda entry point (wraps app.py via aws-wsgi)
│ ├── mock_ai.py # Rule-based intent + language detection
│ ├── product_search.py # Catalog filtering
│ ├── explain.py # Spoken comparison-sentence generation
│ ├── warranty_extract.py # Heuristic invoice field extraction
│ ├── warranty_lookup.py # Voice warranty lookup / matching
│ └── requirements.txt
├── frontend/
│ ├── index.html
│ ├── style.css
│ └── app.js
├── data/
│ └── products.json # Sample product catalog
└── .gitignore


## Running it locally

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env`:
AWS_REGION=ap-south-1
S3_BUCKET=<your-invoices-bucket>
DYNAMODB_TABLE=SunoCartWarranty
USER_ID=demo-user-001


Run the backend:
```bash
python app.py
```

In a second terminal:
```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`. Voice input/output requires a Chromium-based browser (Chrome or Edge).

## Known limitations (honest, not hidden)

- Single shared demo account (`demo-user-001`) — no per-user auth yet; Amazon Cognito would be the natural next step
- Rule-based AI layer rather than Bedrock, due to an account-level access restriction (see above)
- Invoice extraction supports single-page JPG/PNG only — no multi-page or PDF yet
- Sample product catalog, not a live Amazon integration — deliberate scope cut for the hackathon timeframe

## What's next

Swap in real Bedrock once access clears, add per-user accounts via Cognito, support more Indian languages, and extend WarrantyWallet to multi-page/PDF invoices via Textract's async APIs.

---

Built solo, over one hackathon, by [Afrin Shahnaz](https://github.com/Afrin26S) — Team Suno. #BharatBuilds