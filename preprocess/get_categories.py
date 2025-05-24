import pandas as pd

# Load your data (adjust path and separator if needed)
df = pd.read_csv('../data/custom_orders.csv', sep=',')

# Drop rows where Category or Quantity is missing
df = df.dropna(subset=['Category', 'Quantity'])

# Group by category and sum quantities
category_summary = df.groupby('Category')['Quantity'].sum().sort_values(ascending=False)

# Print results
print("Product quantities sold per category:\n")
for category, quantity in category_summary.items():
    print(f"{category}: {int(quantity)} units")

print(f"\nTotal unique categories: {len(category_summary)}")

# save to CSV
category_summary.to_csv('../data/categories.csv', header=['TotalQuantity'])
