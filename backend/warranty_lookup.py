import re

from mock_ai import detect_language, CATEGORY_MAP

# Filler/question words to ignore when matching a spoken query against saved
# product names — Romanized and Devanagari versions of the same common words.
STOPWORDS = {
    "mera", "meri", "mere", "ka", "ki", "ke", "kab", "tak", "hai", "warranty",
    "kitne", "din", "baki", "chahiye", "batao", "kya", "khatam", "hoga",
    "my", "the", "is", "when", "does", "till", "what", "warranty's", "until",
    "मेरा", "मेरी", "मेरे", "का", "की", "के", "कब", "तक", "है", "वारंटी",
    "कितने", "दिन", "बाकी", "चाहिए", "बताओ", "क्या", "खत्म", "होगा",
}


def _keywords(text: str) -> set:
    words = re.findall(r"[\w\u0900-\u097F]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def _normalize_category(text: str):
    """Maps English OR Devanagari product words to the same canonical
    category, so a Hindi voice query can match an English-named catalog
    item (e.g. 'मिक्सर' -> 'mixer grinder', matching 'Mixer' in the name)."""
    text_lower = text.lower()
    for keyword, mapped in CATEGORY_MAP.items():
        if keyword in text_lower:
            return mapped
    return None


def _strip_label(text: str) -> str:
    """Avoid a doubled label — saved warranty_text often already starts with
    'Warranty:' verbatim from the invoice (e.g. 'Warranty: 2 years on motor')."""
    return re.sub(r"^(warranty|guarantee)\s*[:\-]\s*", "", text, flags=re.IGNORECASE).strip()


def find_warranty(items: list, query_text: str) -> dict:
    """
    Rule-based match between a spoken/typed question and saved warranty
    records. Never invents details — only reports what's actually stored,
    and says so plainly when nothing matches.
    """
    language = detect_language(query_text)
    query_keywords = _keywords(query_text)
    query_category = _normalize_category(query_text)

    best_item = None
    best_score = 0
    for item in items:
        product_name = item.get("product_name", "")
        product_keywords = _keywords(product_name)
        item_category = _normalize_category(product_name)

        score = len(query_keywords & product_keywords)
        if query_category and item_category and query_category == item_category:
            score += 5  # strong boost: handles cross-script matches (Hindi query, English name)

        if score > best_score:
            best_score = score
            best_item = item

    if not best_item or best_score == 0:
        message = (
            "माफ़ कीजिए, मुझे इस नाम का कोई सामान नहीं मिला। कृपया दोबारा कोशिश करें।"
            if language == "hi"
            else "Sorry, I couldn't find a saved item matching that. Please try again."
        )
        return {"found": False, "message": message, "language": language}

    product_name = best_item.get("product_name", "")
    purchase_date = best_item.get("purchase_date") or ("पता नहीं" if language == "hi" else "unknown")
    warranty_text = best_item.get("warranty_text") or (
        "कोई वारंटी जानकारी दर्ज नहीं है" if language == "hi" else "no warranty details recorded"
    )
    warranty_text = _strip_label(warranty_text)

    if language == "hi":
        message = f"{product_name} की खरीद {purchase_date} को हुई थी। इसकी वारंटी है: {warranty_text}"
    else:
        message = f"{product_name} was purchased on {purchase_date}. Warranty: {warranty_text}"

    return {"found": True, "message": message, "language": language, "item": best_item}