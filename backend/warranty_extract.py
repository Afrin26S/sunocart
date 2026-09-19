import re

DATE_PATTERNS = [
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[A-Za-z]*\s+\d{2,4})\b",
]

WARRANTY_KEYWORDS = ["warranty", "guarantee"]

SKIP_LINE_PATTERN = re.compile(
    r"invoice|bill no|receipt|tax\b|gst|subtotal|total|qty|quantity"
    r"|pvt\.?\s*ltd|private limited|\bllp\b|enterprises|thank you",
    re.IGNORECASE,
)


def guess_invoice_fields(raw_text: str) -> dict:
    """
    Heuristic best-effort guesses from Textract's raw OCR text.
    These are STARTING POINTS ONLY — the user reviews and corrects every
    field before anything is saved to DynamoDB. Nothing here is ever
    saved without explicit user confirmation.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    purchase_date = ""
    for line in lines:
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                purchase_date = match.group(1)
                break
        if purchase_date:
            break

    warranty_text = ""
    for line in lines:
        if any(keyword in line.lower() for keyword in WARRANTY_KEYWORDS):
            warranty_text = line
            break

    product_name_guess = ""
    for line in lines[:8]:
        if len(line) > len(product_name_guess) and not SKIP_LINE_PATTERN.search(line):
            product_name_guess = line
    # strip common leading labels Textract picks up verbatim, e.g. "Item: X" -> "X"
    product_name_guess = re.sub(
        r"^(item|product|description)\s*[:\-]\s*", "", product_name_guess, flags=re.IGNORECASE
    )

    return {
        "product_name": product_name_guess,
        "purchase_date": purchase_date,
        "warranty_text": warranty_text,
        "raw_text": raw_text,
    }