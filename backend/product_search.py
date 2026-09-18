import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT_FILE = os.path.join(BASE_DIR, "data", "products.json")


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