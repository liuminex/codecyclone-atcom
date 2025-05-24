import pandas as pd
from itertools import combinations
from collections import Counter

df = pd.read_csv('../data/orders.csv')

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

pair_df.to_csv('frequently_bought_together.csv', index=False)

print(pair_df.head(10))


