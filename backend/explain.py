def explain_results(products: list, language: str = "en") -> str:
    """
    Turns matched products into a natural comparison sentence.
    Everything here is generated ONLY from the product data itself —
    never invented — so it's a safe, reliable fallback even after
    Bedrock is added later.
    """
    if not products:
        return (
            "माफ़ कीजिए, आपके बजट में कोई उत्पाद नहीं मिला।"
            if language == "hi"
            else "Sorry, no products matched your budget."
        )

    if language == "hi":
        intro = (
            f"आपके बजट में {len(products)} विकल्प मिले।"
            if len(products) > 1
            else "आपके बजट में एक विकल्प मिला।"
        )
        lines = [intro]
        for idx, product in enumerate(products[:2], start=1):
            ordinal = "पहला" if idx == 1 else "दूसरा"
            lines.append(
                f"{ordinal}, {product['name']}, कीमत ₹{product['price']}। {product['description']}"
            )
        if len(products) > 2:
            lines.append(f"और {len(products) - 2} अन्य विकल्प भी हैं।")
        return " ".join(lines)

    intro = f"I found {len(products)} option{'s' if len(products) != 1 else ''} in your budget."
    lines = [intro]
    for idx, product in enumerate(products[:2], start=1):
        ordinal = "First" if idx == 1 else "Second"
        lines.append(f"{ordinal}, {product['name']} at ₹{product['price']}. {product['description']}")
    if len(products) > 2:
        lines.append(f"And {len(products) - 2} more option(s) available.")
    return " ".join(lines)