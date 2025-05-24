import pandas as pd
import numpy as np
from itertools import product

# Load files
inventory = pd.read_csv("inventory.csv", on_bad_lines='skip')
orders = pd.read_excel("DATA - AI-Powered Bundling & Pricing Strategist.xlsx")

# Normalize SKU as string
inventory["SKU"] = inventory["SKU"].astype(str)
orders["SKU"] = orders["SKU"].astype(str)

# Assign random profit margins to each inventory item
np.random.seed(42)
inventory["ProfitMarginPercent"] = np.random.randint(5, 36, size=len(inventory))

# Merge to get category info with margin and quantity
merged = pd.merge(orders[["SKU", "Category"]], inventory, on="SKU", how="inner")
merged = merged.drop_duplicates(subset="SKU")

# Build bundles per category
bundles = []

for category, group in merged.groupby("Category"):
    # Low and high margin split
    low_margin = group[group["ProfitMarginPercent"] <= group["ProfitMarginPercent"].quantile(0.25)]
    high_margin = group[group["ProfitMarginPercent"] >= group["ProfitMarginPercent"].quantile(0.75)]

    # Sort high-margin items by stock quantity
    high_margin = high_margin.sort_values(by="Quantity", ascending=False)

    # Pair each low-margin with up to 3 high-margin options
    for _, low in low_margin.iterrows():
        for _, high in high_margin.head(3).iterrows():
            if low["SKU"] != high["SKU"]:
                bundles.append({
                    "Category": category,
                    "LowMarginSKU": low["SKU"],
                    "HighMarginSKU": high["SKU"],
                    "LowMarginPercent": low["ProfitMarginPercent"],
                    "HighMarginPercent": high["ProfitMarginPercent"],
                    "HighStockQty": high["Quantity"]
                })

# Convert to DataFrame
bundle_df = pd.DataFrame(bundles)

# Compute profitability score (margin * stock for high-margin product)
bundle_df["EstimatedProfitScore"] = bundle_df["HighStockQty"] * bundle_df["HighMarginPercent"]

# Sort by score and return top 20
top_20_profitable_bundles = bundle_df.sort_values(by="EstimatedProfitScore", ascending=False).head(20)

# Optional: Export to Excel
top_20_profitable_bundles.to_excel("top_20_profitable_bundles.xlsx", index=False)

# Show result
print(top_20_profitable_bundles.head())
