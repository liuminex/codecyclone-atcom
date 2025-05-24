import pandas as pd
import numpy as np

# Load inventory and orders
inventory_df = pd.read_csv('../data/inventory.csv')
orders_df = pd.read_csv('../data/custom_orders.csv', parse_dates=['CreatedDate'])

print(f"Inventory columns before update: {inventory_df.columns.tolist()}")
print(f"Orders columns: {orders_df.columns.tolist()}")

# Ensure relevant columns exist in inventory
if 'ProductCategory' not in inventory_df.columns:
    inventory_df['ProductCategory'] = None

if 'ProductName' not in inventory_df.columns:
    inventory_df['ProductName'] = None

if 'Margin' not in inventory_df.columns:
    np.random.seed(42)
    inventory_df['Margin'] = np.round(np.random.uniform(15, 45, size=len(inventory_df)), 2)

# Drop rows with missing SKU or CreatedDate in orders
orders_df = orders_df.dropna(subset=['SKU', 'CreatedDate'])

# Discount calculation
orders_df['DiscountAmount'] = (orders_df['OriginalUnitPrice'] - orders_df['FinalUnitPrice']).clip(lower=0)
orders_df['HasDiscount'] = orders_df['DiscountAmount'] > 0

# Average discount per SKU (only when discounted)
avg_discount = (
    orders_df[orders_df['HasDiscount']]
    .groupby('SKU')['DiscountAmount']
    .mean()
    .reset_index()
    .rename(columns={'DiscountAmount': 'AverageDiscount'})
)

# Calculate OrderCount_Discounted and OrderCount_FullPrice per SKU
grouped = orders_df.groupby(['SKU', 'HasDiscount']).agg(
    OrderCount=('OrderNumber', 'nunique')
).reset_index()

pivot = grouped.pivot(index='SKU', columns='HasDiscount', values='OrderCount').fillna(0)
pivot.columns = ['OrderCount_FullPrice' if not col else 'OrderCount_Discounted' for col in pivot.columns]

# Calculate ratio, avoid division by zero
## OrderCount_Ratio_Discounted_vs_FullPrice: inf means it is bought only on discount, 5 means for every item bought without discount, 5 items are bought with discount
pivot['OrderCount_Ratio_Discounted_vs_FullPrice'] = pivot['OrderCount_Discounted'] / pivot['OrderCount_FullPrice'].replace(0, np.nan)
pivot['OrderCount_Ratio_Discounted_vs_FullPrice'] = pivot['OrderCount_Ratio_Discounted_vs_FullPrice'].fillna(np.inf)
pivot = pivot.reset_index()

# Product info from orders
sku_info = orders_df[['SKU', 'Category', 'Item title']].drop_duplicates()
sku_info = sku_info.rename(columns={'Category': 'ProductCategory', 'Item title': 'ProductName'})

# -------- SEASONALITY CALCULATION --------
# Extract month from order date
orders_df['Month'] = orders_df['CreatedDate'].dt.month

month_names = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

def month_num_to_name(num):
    return month_names[num - 1]

def get_seasonality(month_counts):
    if month_counts.sum() == 0:
        return "all year"
    avg_orders = month_counts.mean()
    threshold = avg_orders * 1.5
    popular_months = month_counts[month_counts >= threshold].index.tolist()
    if not popular_months:
        return "all year"
    months_cyclic = popular_months + [m + 12 for m in popular_months]
    longest_segment = []
    current_segment = [months_cyclic[0]]
    for i in range(1, len(months_cyclic)):
        if months_cyclic[i] == months_cyclic[i-1] + 1:
            current_segment.append(months_cyclic[i])
        else:
            if len(current_segment) > len(longest_segment):
                longest_segment = current_segment
            current_segment = [months_cyclic[i]]
    if len(current_segment) > len(longest_segment):
        longest_segment = current_segment
    longest_segment_mod = [(m - 1) % 12 + 1 for m in longest_segment]
    start_month = month_num_to_name(min(longest_segment_mod))
    end_month = month_num_to_name(max(longest_segment_mod))
    if start_month == end_month:
        return start_month
    else:
        return f"{start_month}-{end_month}"

# Group orders by SKU and month, count orders
sku_month_counts = orders_df.groupby(['SKU', 'Month']).size().reset_index(name='OrderCount')

# Pivot to have months as columns, SKUs as rows
sku_month_pivot = sku_month_counts.pivot(index='SKU', columns='Month', values='OrderCount').fillna(0)

# Calculate seasonality for each SKU
seasonality = sku_month_pivot.apply(get_seasonality, axis=1).reset_index()
seasonality.columns = ['SKU', 'Seasonality']

# ---------------------------------------

# Merge all into inventory
updated_inventory = inventory_df.merge(sku_info, on='SKU', how='left', suffixes=('', '_orders'))
updated_inventory['ProductCategory'] = updated_inventory['ProductCategory_orders'].combine_first(updated_inventory['ProductCategory'])
updated_inventory['ProductName'] = updated_inventory['ProductName_orders'].combine_first(updated_inventory['ProductName'])
updated_inventory.drop(columns=['ProductCategory_orders', 'ProductName_orders'], inplace=True)

updated_inventory = updated_inventory.merge(avg_discount, on='SKU', how='left')
updated_inventory['AverageDiscount'] = updated_inventory['AverageDiscount'].fillna(0)

updated_inventory = updated_inventory.merge(pivot[['SKU', 'OrderCount_Ratio_Discounted_vs_FullPrice']], on='SKU', how='left')
updated_inventory['OrderCount_Ratio_Discounted_vs_FullPrice'] = updated_inventory['OrderCount_Ratio_Discounted_vs_FullPrice'].fillna(0)

updated_inventory = updated_inventory.merge(seasonality, on='SKU', how='left')
updated_inventory['Seasonality'] = updated_inventory['Seasonality'].fillna('all year')

# Round numeric columns to 2 decimals
numeric_cols = updated_inventory.select_dtypes(include=['float64', 'int64']).columns
updated_inventory[numeric_cols] = updated_inventory[numeric_cols].round(2)

# Save
updated_inventory.to_csv('../data/custom_inventory.csv', index=False)
print("✅ Updated inventory saved to custom_inventory.csv")
