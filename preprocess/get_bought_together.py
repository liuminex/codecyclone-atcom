import pandas as pd


import pandas as pd
from itertools import combinations
from collections import Counter

df = pd.read_csv('../data/custom_orders.csv')

# confirm columns exist
assert {'OrderNumber', 'SKU'}.issubset(df.columns), "Missing required columns"

# group by order number
order_groups = df.groupby('OrderNumber')['SKU'].unique()

pair_counter = Counter()
for skus in order_groups:
    if len(skus) >= 2:
        pairs = combinations(sorted(skus), 2)
        pair_counter.update(pairs)

pair_df = pd.DataFrame(
    [(a, b, count) for (a, b), count in pair_counter.items()],
    columns=['ProductA', 'ProductB', 'Count']
)

# sort
pair_df = pair_df.sort_values(by='Count', ascending=False).reset_index(drop=True)

pair_df.to_csv('../data/bought_together.csv', index=False)

print(pair_df.head(10))



# print with names
print("---------------------------------")

sku_name_map = df[['SKU', 'Item title']].drop_duplicates()

sku_to_name = dict(zip(sku_name_map['SKU'], sku_name_map['Item title']))

pair_df['ProductNameA'] = pair_df['ProductA'].map(sku_to_name)
pair_df['ProductNameB'] = pair_df['ProductB'].map(sku_to_name)

# print top 10
for i in range(10):
    print(f"Pair {i+1}: {pair_df['ProductNameA'][i]} and {pair_df['ProductNameB'][i]}")