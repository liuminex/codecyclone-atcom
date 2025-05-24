import pandas as pd

'''
Match product name to SKU for better readability
'''

pairs_df = pd.read_csv('frequently_bought_together.csv')

orders_df = pd.read_csv('../data/orders.csv')

sku_name_map = orders_df[['SKU', 'Item title']].drop_duplicates()

sku_to_name = dict(zip(sku_name_map['SKU'], sku_name_map['Item title']))

pairs_df['ProductNameA'] = pairs_df['ProductA'].map(sku_to_name)
pairs_df['ProductNameB'] = pairs_df['ProductB'].map(sku_to_name)

# print top 10
for i in range(10):
    print(f"Pair {i+1}: {pairs_df['ProductNameA'][i]} and {pairs_df['ProductNameB'][i]}")