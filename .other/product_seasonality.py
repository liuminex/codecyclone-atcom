import pandas as pd

# Load orders data
orders_df = pd.read_csv('../data/orders.csv', parse_dates=['CreatedDate'])
orders_df = orders_df.dropna(subset=['SKU', 'CreatedDate'])

# Extract month from order date
orders_df['Month'] = orders_df['CreatedDate'].dt.month

# Function to convert month numbers to month names
month_names = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

def month_num_to_name(num):
    return month_names[num - 1]

# Analyze seasonality per SKU
def get_seasonality(month_counts):
    """
    Given a pandas Series with month counts indexed by month number (1-12),
    determine the most popular contiguous month range where orders are high.
    If no strong seasonality, return "all year".
    """

    # If no orders, return all year
    if month_counts.sum() == 0:
        return "all year"

    avg_orders = month_counts.mean()
    # Threshold for "high" orders can be more than 1.5 * average (tune as needed)
    threshold = avg_orders * 1.5

    # Mark months as popular if above threshold
    popular_months = month_counts[month_counts >= threshold].index.tolist()

    if not popular_months:
        return "all year"

    # Because months are cyclic (December to January), we consider cyclic continuity
    # We'll duplicate the months list to handle wrap-around
    months_cyclic = popular_months + [m + 12 for m in popular_months]

    # Find longest contiguous segment in the cyclic list
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

    # Map back to 1-12 months (mod 12)
    longest_segment_mod = [(m - 1) % 12 + 1 for m in longest_segment]

    # Convert to month names, get min and max
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
seasonality.columns = ['SKU', 'PopularMonths']

# Load inventory.csv
inventory_df = pd.read_csv('../data/inventory.csv')

# Merge with seasonality info
inventory_with_season = inventory_df.merge(seasonality, on='SKU', how='left')

# Fill missing seasonality with 'all year' (for SKUs with no orders)
inventory_with_season['PopularMonths'].fillna('all year', inplace=True)

# Save result
inventory_with_season.to_csv('inventory_with_season.csv', index=False)

print("inventory_with_season.csv created successfully!")
