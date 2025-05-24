import pandas as pd
from itertools import combinations
from collections import Counter

# Load order data
df = pd.read_csv('../data/custom_orders.csv')

# Confirm required columns exist
assert {'OrderNumber', 'SKU'}.issubset(df.columns), "Missing required columns"

# Group SKUs by order number
order_groups = df.groupby('OrderNumber')['SKU'].unique()

# Count SKU pairs
pair_counter = Counter()
for skus in order_groups:
    if len(skus) >= 2:
        pairs = combinations(sorted(skus), 2)
        pair_counter.update(pairs)

# Convert pair counter to DataFrame
pair_df = pd.DataFrame(
    [(a, b, count) for (a, b), count in pair_counter.items()],
    columns=['ProductA', 'ProductB', 'Count']
)

# Load inventory and get valid SKUs
inventory_df = pd.read_csv('../data/custom_inventory.csv')
valid_skus = set(inventory_df['SKU'])

# Filter out pairs where either SKU is not in inventory
pair_df = pair_df[
    pair_df['ProductA'].isin(valid_skus) & pair_df['ProductB'].isin(valid_skus)
]

# Sort pairs by count
pair_df = pair_df.sort_values(by='Count', ascending=False).reset_index(drop=True)

# Save results
pair_df.to_csv('../data/bought_together.csv', index=False)
print(pair_df.head(10))

# Print with product names
print("---------------------------------")

# Map SKU to product name
sku_name_map = df[['SKU', 'Item title']].drop_duplicates()
sku_to_name = dict(zip(sku_name_map['SKU'], sku_name_map['Item title']))

pair_df['ProductNameA'] = pair_df['ProductA'].map(sku_to_name)
pair_df['ProductNameB'] = pair_df['ProductB'].map(sku_to_name)

# Print top 10 pairs with names
for i in range(min(10, len(pair_df))):
    print(f"Pair {i+1}: {pair_df['ProductNameA'][i]} and {pair_df['ProductNameB'][i]}")
