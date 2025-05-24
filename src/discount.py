def calculate_bundle_discount_flexible_percent(products):
    """
    Calculates a recommended bundle discount for 2 or 3 products.

    Input:
        products: list of dicts with keys:
            - price: float
            - avg_discount_percent: float
            - sale_lift_ratio: float
            - margin_percent: float

    Returns:
        float: Final recommended discount percentage (e.g., 15.0 for 15%)
    """
    n = len(products)
    if n < 2 or n > 3:
        raise ValueError("Please provide exactly 2 or 3 products.")

    total_price = sum(p["price"] for p in products)
    weighted_avg_discount = sum(p["avg_discount_percent"] * p["price"] for p in products) / total_price
    avg_sale_lift = sum(p["sale_lift_ratio"] for p in products) / n
    lift_bonus = 2 * max(0, avg_sale_lift - 1)
    min_margin = min(p["margin_percent"] for p in products)
    margin_protection = max(0, (30 - min_margin) / 100 * 10)

    raw_discount = weighted_avg_discount + lift_bonus - margin_protection
    recommended_discount = round(max(0, raw_discount) / 5) * 5

    return recommended_discount
