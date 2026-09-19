"""
Temporary local AI simulation for SunoCart's VoiceCart feature.

This lets you build and demo the full app TODAY without waiting on
AWS Bedrock access. Once Bedrock is enabled, this function is swapped
for a real bedrock.converse() call — nothing else in app.py changes,
because the contract (return a dict with category/max_price/language)
stays the same. See bedrock_ai.py for that version.

IMPORTANT: real speech recognition returns Hindi text in DEVANAGARI
SCRIPT (e.g. "मुझे"), not Romanized text (e.g. "mujhe"). Both forms
are handled below — Devanagari for real voice input, Romanized for
anyone testing by typing Hinglish.
"""

import re

# Any character in this Unicode range means the text contains Devanagari
# script — the strongest, most reliable signal that this is spoken Hindi.
DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")

# Fallback signal for TYPED Hinglish (Roman letters), e.g. "mujhe chahiye"
HINDI_MARKERS = [
    "mujhe", "chahiye", "andar", "wala", "wali",
    "kharidna", "kharidni", "hazaar", "hazar",
]

CATEGORY_MAP = {
    # English / Romanized Hinglish
    "headphone": "headphones",
    "headphones": "headphones",
    "earphone": "headphones",
    "earphones": "headphones",
    "mixer grinder": "mixer grinder",
    "mixer": "mixer grinder",
    "speaker": "speaker",
    "speakers": "speaker",
    "backpack": "backpack",
    "bag": "backpack",
    "smartwatch": "smartwatch",
    "watch": "smartwatch",
    "kettle": "kettle",
    # Devanagari — what the browser actually transcribes for spoken Hindi
    "हेडफोन्स": "headphones",
    "हेडफोंस": "headphones",
    "हेडफोन": "headphones",
    "इयरफोन": "headphones",
    "मिक्सर": "mixer grinder",
    "मिक्सी": "mixer grinder",
    "स्पीकर": "speaker",
    "बैकपैक": "backpack",
    "बैग": "backpack",
    "स्मार्टवॉच": "smartwatch",
    "वॉच": "smartwatch",
    "घड़ी": "smartwatch",
    "केतली": "kettle",
}


def detect_language(text: str) -> str:
    """Shared language detector: Devanagari script (real voice input) or
    Romanized Hindi markers (typed Hinglish) both count as Hindi. Reused
    by warranty_lookup.py so both features detect language the same way."""
    is_devanagari = bool(DEVANAGARI_RANGE.search(text))
    text_lower = text.lower()
    return "hi" if is_devanagari or any(word in text_lower for word in HINDI_MARKERS) else "en"


def extract_shopping_intent(text: str) -> dict:
    """Very small rule-based stand-in for Bedrock intent extraction."""
    text_lower = text.lower()

    # 1. language
    language = detect_language(text)

    # 2. budget — try a few common phrasings, in order:
    max_price = None

    # a) currency symbol/word BEFORE the number: "₹3000", "rs 3000", "inr 3000"
    price_match = re.search(r"(?:₹|rs\.?|inr)\s?(\d+(?:,\d+)*)", text_lower)

    # b) number BEFORE a postposition, Romanized OR Devanagari:
    #    "2000 ke andar" / "3000 के अंदर" / "2000 rupaye" / "3000 रुपये"
    if not price_match:
        price_match = re.search(
            r"(\d+(?:,\d+)*)\s*(?:ke\s+andar|ke\s+ander|के\s*अंदर|में|तक|rupa?ye|rupees?|रुपये|रुपए)",
            text_lower,
        )

    # c) English keyword BEFORE the number: "under 3000", "below 3000"
    if not price_match:
        price_match = re.search(
            r"(?:under|below|within|less than)\s*(?:₹|rs\.?|inr)?\s?(\d+(?:,\d+)*)",
            text_lower,
        )

    if price_match:
        max_price = int(price_match.group(1).replace(",", ""))

    # 3. category — first matching keyword wins
    category = None
    for keyword, mapped_category in CATEGORY_MAP.items():
        if keyword in text_lower:
            category = mapped_category
            break

    return {
        "category": category,
        "max_price": max_price,
        "language": language,
        "original_text": text,
    }