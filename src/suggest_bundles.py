import os
import json
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import re
from collections import defaultdict

# Load environment variables
load_dotenv()

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))

# Load data
orders = pd.read_csv("../data/custom_orders.csv", parse_dates=["CreatedDate"])
inventory = pd.read_csv("../data/custom_inventory.csv")

orders = orders.dropna(subset=["UserID"])

# Normalize seasonality
def parse_seasonality(value):
    months_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    tokens = value.lower().replace(" ", "").split("-")
    if len(tokens) == 1:
        return [months_map.get(tokens[0], None)]
    elif len(tokens) == 2:
        start = months_map.get(tokens[0])
        end = months_map.get(tokens[1])
        if start and end:
            if start <= end:
                return list(range(start, end + 1))
            else:
                return list(range(start, 13)) + list(range(1, end + 1))
    return []

inventory["SeasonMonths"] = inventory["Seasonality"].fillna("").apply(parse_seasonality)

# Product keywords using Gemini
def match_keywords_gemini(name):
    prompt = f"Extract the 5 most relevant keywords that describe this product name: '{name}'. Respond in comma-separated format."
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        keywords = re.split(r",\s*", raw)
        return [k.lower() for k in keywords if k]
    except Exception as e:
        print(f"Keyword extraction error for '{name}': {e}")
        return []

# Cache product keywords
sku_keywords = {
    row["SKU"]: match_keywords_gemini(row["ProductName"])
    for _, row in inventory.iterrows()
}

# Complementary bundles (frequent co-buys)
from itertools import combinations
pair_counts = defaultdict(int)
for _, order_group in orders.groupby("OrderNumber"):
    skus = order_group["SKU"].unique()
    for a, b in combinations(sorted(skus), 2):
        pair_counts[(a, b)] += 1
complementary_bundles = sorted(
    [{"SKU1": a, "SKU2": b, "Count": c} for (a, b), c in pair_counts.items() if c > 1],
    key=lambda x: -x["Count"]
)

# Thematic bundles: group by season
seasonal_bundles = [
    {"SKU": row["SKU"], "TopSeason": row["Seasonality"]}
    for _, row in inventory.iterrows() if isinstance(row["Seasonality"], str)
]

# Cross-sell bundles: top margin products
high_margin = inventory.sort_values(by="Margin", ascending=False).head(10)
cross_sell = high_margin[["SKU", "Margin"]].to_dict(orient="records")

# Personalized bundles
def get_personalized_bundles(user_id):
    user_orders = orders[orders["UserID"] == user_id]
    if user_orders.empty:
        return []

    user_sku_counts = user_orders["SKU"].value_counts()
    top_skus = user_sku_counts.head(5).index.tolist()
    user_inventory = inventory[inventory["SKU"].isin(top_skus)]

    related = []
    for sku in top_skus:
        base_keywords = set(sku_keywords.get(sku, []))
        for other_sku, other_kw in sku_keywords.items():
            if other_sku == sku:
                continue
            if len(base_keywords.intersection(other_kw)) >= 2:
                related.append({"BaseSKU": sku, "RelatedSKU": other_sku})
    return related

# Main bundling function
def suggest_bundles(user_id=None):
    result = {
        "ComplementaryBundles": complementary_bundles[:10],
        "ThematicBundles": seasonal_bundles[:10],
        "CrossSellBundles": cross_sell
    }
    if user_id:
        result["PersonalizedBundles"] = get_personalized_bundles(user_id)
    return result

# Entry point
if __name__ == "__main__":
    example_user_id = orders["UserID"].dropna().unique()[0]
    bundles = suggest_bundles(user_id=example_user_id)
    print(json.dumps(bundles, indent=2, ensure_ascii=False))
