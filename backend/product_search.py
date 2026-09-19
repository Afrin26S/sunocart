import json
import os


def _find_products_file():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(here), "data", "products.json"),  # local dev layout
        os.path.join(here, "products.json"),  # Lambda: bundled next to this file
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("products.json not found in any expected location")


PRODUCT_FILE = _find_products_file()

def load_products():
    with open(PRODUCT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def search_products(intent: dict) -> list:
    products = load_products()
    category = (intent.get("category") or "").lower().strip()
    max_price = intent.get("max_price")

    results = []
    for product in products:
        category_match = (not category) or (category in product["category"].lower())
        price_match = (max_price is None) or (product["price"] <= max_price)
        if category_match and price_match:
            results.append(product)
    return results