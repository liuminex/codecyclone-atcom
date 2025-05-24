import pandas as pd

# Load orders data
orders_df = pd.read_csv('../data/orders.csv')

# Drop Brand column if it exists
if 'Brand' in orders_df.columns:
    orders_df = orders_df.drop(columns=['Brand'])

# === Step 1: Resolve multiple categories per SKU ===
# Find SKUs with multiple categories
sku_categories = orders_df.groupby('SKU')['Category'].unique()
multi_cat_skus = sku_categories[sku_categories.apply(len) > 1]

if not multi_cat_skus.empty:
    print("SKUs with multiple categories found. Resolving to first category:")
    for sku, categories in multi_cat_skus.items():
        print(f"SKU: {sku} - Categories: {list(categories)}")
else:
    print("No SKUs with multiple categories found.")

# Map each SKU to its first category
sku_to_category = sku_categories.apply(lambda cats: cats[0])
orders_df['Category'] = orders_df['SKU'].map(sku_to_category)

# === Step 2: Resolve multiple names per SKU ===
# Find SKUs with multiple product names
sku_names = orders_df.groupby('SKU')['Item title'].unique()
multi_name_skus = sku_names[sku_names.apply(len) > 1]

if not multi_name_skus.empty:
    print("\nSKUs with multiple product names found. Resolving to first name:")
    for sku, names in multi_name_skus.items():
        print(f"SKU: {sku} - Names: {list(names)}")
else:
    print("No SKUs with multiple product names found.")

# Map each SKU to its first name
sku_to_name = sku_names.apply(lambda names: names[0])
orders_df['Item title'] = orders_df['SKU'].map(sku_to_name)

# Save the cleaned orders
orders_df.to_csv('../data/custom_orders.csv', index=False)

print("\nUpdated orders saved to custom_orders.csv")
