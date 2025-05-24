import pandas as pd

# Load your data (adjust filename/path)
df = pd.read_csv('../data/orders.csv', sep=',')

assert {'OrderNumber', 'SKU'}.issubset(df.columns), "Missing required columns"


print(df.columns)
# Count total unique products
total_unique_products = df['SKU'].nunique()

print(f"Total unique products in dataset: {total_unique_products}")

# Calculate discount flag and discount amount
df['DiscountAmount'] = (df['OriginalUnitPrice'] - df['FinalUnitPrice']).clip(lower=0)
df['HasDiscount'] = df['DiscountAmount'] > 0

# Filter only discounted products for analysis
discounted_products = df[df['HasDiscount']]

# Group by product and discount flag, aggregate quantity and order count
grouped = df.groupby(['SKU', 'HasDiscount']).agg(
    TotalQuantity=('Quantity', 'sum'),
    OrderCount=('OrderNumber', 'nunique')
).reset_index()

# Pivot to get discounted vs full price side-by-side
pivot = grouped.pivot(index='SKU', columns='HasDiscount', values=['TotalQuantity', 'OrderCount'])

# Fix columns: rename True -> _Discounted, False -> _FullPrice
pivot.columns = [
    f"{col[0]}_Discounted" if col[1] else f"{col[0]}_FullPrice"
    for col in pivot.columns.to_flat_index()
]

# Fill NaN with 0 (in case some products never bought discounted/full price)
pivot = pivot.fillna(0)

# Calculate likelihood ratio: how much more likely a product is bought discounted vs full price
# Using OrderCount ratio here, but can use TotalQuantity similarly
pivot['OrderCount_Ratio_Discounted_vs_FullPrice'] = (
    pivot['OrderCount_Discounted'] / pivot['OrderCount_FullPrice'].replace(0, pd.NA)
).fillna(float('inf'))

# Show only products with discount (i.e., where discounted count > 0)
pivot = pivot[pivot['OrderCount_Discounted'] > 0]

# Print or export results
print(pivot.reset_index())

# Optional: save to csv
# pivot.reset_index().to_csv('discount_analysis_results.csv', index=False)
