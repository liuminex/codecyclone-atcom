import pandas as pd

# Load orders data
orders_df = pd.read_csv('../data/orders.csv')

# Drop Brand column if exists
if 'Brand' in orders_df.columns:
    orders_df = orders_df.drop(columns=['Brand'])

# Find SKUs with multiple categories
sku_categories = orders_df.groupby('SKU')['Category'].unique()

# Filter SKUs with multiple categories
multi_cat_skus = sku_categories[sku_categories.apply(len) > 1]

if not multi_cat_skus.empty:
    print("SKUs with multiple categories found. Resolving to first category:")
    for sku, categories in multi_cat_skus.items():
        print(f"SKU: {sku} - Categories: {list(categories)}")
else:
    print("No SKUs with multiple categories found.")

# Map each SKU to its first category
sku_to_category = sku_categories.apply(lambda cats: cats[0])

# Replace categories in orders with the first category for the SKU
orders_df['Category'] = orders_df['SKU'].map(sku_to_category)

# Save the cleaned orders
orders_df.to_csv('../data/custom_orders.csv', index=False)

print("Updated orders saved to custom_orders.csv")
