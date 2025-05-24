import pandas as pd
from itertools import combinations
from collections import Counter

from user_profiling import get_user_profile

def load_inventory():
    inventory_df = pd.read_csv('../data/custom_inventory.csv')
    sku_to_name = dict(zip(inventory_df['SKU'], inventory_df['ProductName']))
    return inventory_df, sku_to_name


def get_top_skus_by_priority(inventory_df, priority, top_n=10):
    return inventory_df.sort_values(by='SKU').head(top_n)['SKU'].tolist() if priority == "SKU" else []


def sku_bundle_to_name(bundle, sku_to_name):
    return tuple(sku_to_name.get(sku, sku) for sku in bundle)


def get_bundle_complementary(priority=None, depth=5):
    """
    Reads ../data/bought_together.csv (ProductA,ProductB,Count) and returns combinations of 3 products
    (if A and B are bought together and B and C also bought together suggest bundles of the 3 products).
    Find all combinations of 3 products that are bought together, and return a list of the top [depth] combinations
    (top is defined by Count).

    if priority==None: do as normal
    if priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """
    bt_df = pd.read_csv('../data/bought_together.csv')
    inventory_df, sku_to_name = load_inventory()

    # Build product pair graph
    graph = {}
    for _, row in bt_df.iterrows():
        a, b = row['ProductA'], row['ProductB']
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    triplets = set()
    for a in graph:
        for b in graph[a]:
            for c in graph.get(b, []):
                if c in graph[a] and len({a, b, c}) == 3:
                    triplets.add(tuple(sorted([a, b, c])))

    top_skus = get_top_skus_by_priority(inventory_df, priority)
    if top_skus:
        triplets = [t for t in triplets if any(p in top_skus for p in t)]

    bundles = [sku_bundle_to_name(t, sku_to_name) for t in list(triplets)[:depth]]
    return bundles


def get_bundle_seasonal(season=None, priority=None, depth=5):
    """
    season: 3-letter name of a month (eg 'jan')

    Reads ../data/custom_inventory.csv and returns [depth] combinations of 2-3 products that Have seasonality matching the season.
    For example if season='jan' then all products in the bundle have in their seasonality column the value "jan" or somethin that
    conatins "jan" like "dec-feb"
    If season = None, then returns all products that have any seasonality.

    if priority==None: do as normal
    if priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 2-3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """
    inventory_df, sku_to_name = load_inventory()
    df = inventory_df.dropna(subset=['Seasonality'])

    if season:
        df = df[df['Seasonality'].str.contains(season, case=False)]

    top_skus = get_top_skus_by_priority(df, priority)
    bundles = []
    skus = df['SKU'].tolist()

    for bundle in combinations(skus, 3):
        if not top_skus or any(sku in top_skus for sku in bundle):
            bundles.append(sku_bundle_to_name(bundle, sku_to_name))
        if len(bundles) == depth:
            break

    return bundles


def get_bundle_thematic(priority=None, depth=5):
    """
    Reads ../data/custom_inventory.csv and returns [depth] combinations of 2-3 products that have the same ProductCategory.
    If priority==None: do as normal
    If priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 2-3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """
    inventory_df, sku_to_name = load_inventory()
    top_skus = get_top_skus_by_priority(inventory_df, priority)

    bundles = []
    for _, group in inventory_df.groupby('ProductCategory'):
        skus = group['SKU'].tolist()
        for bundle in combinations(skus, 3):
            if not top_skus or any(sku in top_skus for sku in bundle):
                bundles.append(sku_bundle_to_name(bundle, sku_to_name))
            if len(bundles) == depth:
                return bundles
    return bundles


def get_bundle_cross_sell(priority=None, depth=5):
    """
    Reads ../data/custom_inventory.csv (SKU,Quantity,ProductCategory,ProductName,Margin
        AverageDiscount,OrderCount_Ratio_Discounted_vs_FullPrice,Seasonality)
        and returns [depth] combinations of 2 products. The 2 products must be one with low profit margin and one with high.

    if priority==None: do as normal
    if priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """
    inventory_df, sku_to_name = load_inventory()
    sorted_df = inventory_df.sort_values(by='Margin')
    low_margin = sorted_df.head(len(sorted_df)//2)['SKU'].tolist()
    high_margin = sorted_df.tail(len(sorted_df)//2)['SKU'].tolist()

    top_skus = get_top_skus_by_priority(inventory_df, priority)

    bundles = []
    for low in low_margin:
        for high in high_margin:
            if low != high:
                if not top_skus or low in top_skus or high in top_skus:
                    bundles.append(sku_bundle_to_name((low, high), sku_to_name))
                if len(bundles) == depth:
                    return bundles
    return bundles


def get_bundle_personal_frequently_bought(user_profile, priority=None, depth=5):
    """
    Gets profile data from userid and finds the two most bought products by the user.
    Then adds another product with them based on priority.
    If priority==None: do as normal, 3rd product is a low margin
    if priority=="SKU": then sort custom_inventory.csv by SKU and 3rd product is the top from the list.
    """
    orders = pd.read_csv('../data/custom_orders.csv')
    inventory_df, sku_to_name = load_inventory()

    user_orders = user_profile['MostFrequentProducts']

    """
    user profile is like: {
        "UserID": userid,
        "MostFrequentProducts": sku_order_counts[['SKU', 'Item title', 'TimesOrdered']].to_dict(orient='records'),
        "AverageDaysBetweenOrders": round(avg_days_between_orders, 2) if not pd.isna(avg_days_between_orders) else "Only one order",
        "SeasonalTrend": seasonal_trend,
        "UserAttributes": user_attributes,
        "DiscountPreference": discount_preference,
        "AverageDiscount": average_discount
    }
    """
    top_skus = [item['SKU'] for item in user_orders if 'SKU' in item]
    # keep top 2 that exist in inventory_df
    top_skus = [sku for sku in top_skus if sku in inventory_df['SKU'].values][:2]

    if len(top_skus) < 2:
        return []

    if priority == "SKU":
        third_product = inventory_df.sort_values(by='SKU').iloc[0]['SKU']
    else:
        third_product = inventory_df.sort_values(by='Margin').iloc[0]['SKU']

    return [sku_bundle_to_name((top_skus[0], top_skus[1], third_product), sku_to_name)]


def get_bundle_personal_seasonal(user_profile, season=None, priority=None, depth=5):
    """
    Gets profile data from userid and finds the seasonality of the user - if exists.
    Then finds top product bought by the user that has the same seasonality.
    Then finds another product with the same seasonality that the user doesn't buy usually.
    Create the 2-product bundle.

    if priority==None: do as normal, 2nd product is random
    if priority=="SKU": then sort custom_inventory.csv by SKU and 2nd product is the top from the list.
    """
    # Load data
    inventory_df = pd.read_csv('../data/custom_inventory.csv')
    orders = pd.read_csv('../data/custom_orders.csv')

    user_id = user_profile.get("UserID")
    user_seasonality = season or user_profile.get('SeasonalTrend', None)
    if not user_seasonality:
        return []

    print(f"User {user_id} seasonal preference: {user_seasonality}")

    # from all products in user_profile['MostFrequentProducts'] find the one that has the same seasonality
    user_products = user_profile['MostFrequentProducts']
    user_skus = [item['SKU'] for item in user_products if 'SKU' in item]
    user_top_product = None
    for sku in user_skus:
        product_row = inventory_df[inventory_df['SKU'] == sku]
        if not product_row.empty and user_seasonality in product_row['Seasonality'].values[0]:
            user_top_product = sku
            break
    if not user_top_product:
        print(f"No top product found for user {user_id} with seasonality {user_seasonality}.")
        return []
    print(f"User {user_id} top product for seasonality {user_seasonality}: {user_top_product}")

    # Find another product with the same seasonality that the user doesn't buy
    seasonal_products = inventory_df[inventory_df['Seasonality'].str.contains(user_seasonality, case=False)]
    seasonal_products = seasonal_products[~seasonal_products['SKU'].isin(user_skus)]
    if seasonal_products.empty:
        print(f"No other products found for user {user_id} with seasonality {user_seasonality}.")
        return []
    if priority == "SKU":
        second_product = seasonal_products.sort_values(by='SKU').iloc[0]['SKU']
    else:
        second_product = seasonal_products.sort_values(by='Margin').iloc[0]['SKU']

    return [first_product, second_product]



def get_bundle_personalized_discounts(user_profile):
    """
    Gets profile data from userid, and from there if discount_preference > 0.6 then
    sort products in custom_inventory.csv by SKU and create one bundle of the top 3 products,
    and one bundle of the top 2 producs. Return the 2 bundles.
    """
    inventory_df, sku_to_name = load_inventory()

    bundles = []

    if user_profile['DiscountPreference'] > 0.6:
        sorted_skus = inventory_df.sort_values(by='SKU')['SKU'].tolist()
        bundles.append(sku_bundle_to_name(tuple(sorted_skus[:3]), sku_to_name))
        bundles.append(sku_bundle_to_name(tuple(sorted_skus[:2]), sku_to_name))

    return bundles

def evaluate_bundle(bundle, cheapness=0.5):

    inventory_df = pd.read_csv('../data/custom_inventory.csv')

    """
    cheapness: 0 means zero discount, 1 means maximum discount (leaves only 10% profit margin for us)
    """

    # Create lookup by product name
    name_to_row = {row['ProductName']: row for _, row in inventory_df.iterrows()}

    conversion_rate = 0.05 # rate at which we expect to sell the bundle

    products = []

    print(f"Evaluating bundle:")
    for product in bundle:
        print(f"\t- {product}")

    for product in bundle:
        product_name = product if isinstance(product, str) else product[0]

        if product_name not in name_to_row:
            raise ValueError(f"Product '{product_name}' not found in inventory.")

        row = name_to_row[product_name]

        ratio = row['OrderCount_Ratio_Discounted_vs_FullPrice']
        if ratio == float('inf'):
            ratio = 9999999

        products.append({
            "price": row['BasePrice'],
            "avg_discount_percent": row['AverageDiscount']/100,
            "discount_pref_ratio": ratio,
            "margin": row['Margin']/100
        })

    if len(products) < 2 or len(products) > 3:
        raise ValueError("Bundles must contain exactly 2 or 3 products.")

    # You need to define this elsewhere
    first_product_price, total_price, max_discount = calculate_bundle_discount_flexible_percent(products)

    #print(f"\tBundle evaluation: First product price = ${first_product_price:.2f}")
    #print(f"\tTotal price of bundle = ${total_price}")
    #print(f"\tMaximum discount = {max_discount}")

    new_price_total = total_price * (1 - cheapness * max_discount)

    added_profit = new_price_total - first_product_price

    added_profit *= conversion_rate  # Adjust profit by conversion rate

    #print(f"\tNew total price after discount = ${new_price_total:.2f}")
    #print(f"\tBundle profit evaluation: First product price = ${first_product_price:.2f}")
    print(f"\tExpected profit gain = ${added_profit:.2f}")

    return added_profit

def calculate_bundle_discount_flexible_percent(products):
    """
    Calculates a recommended bundle discount for 2 or 3 products.
    """
    n = len(products)
    if n < 2 or n > 3:
        raise ValueError("Please provide exactly 2 or 3 products.")

    first_product_price = products[0]["price"]

    total_price = sum(p["price"] for p in products)
    margin_sell = sum(p["price"]*(1-p['margin']) for p in products) # price if all margins were 0 (cost of production)

    raw_margin = total_price - margin_sell

    desired_margin = 0.1
    discounted_price = margin_sell / (1-desired_margin)

    max_discount = (total_price - discounted_price) / total_price

    return first_product_price, total_price, max_discount

def get_all_bundles(userId):

    bundles = []

    print(f"Fetching complementary bundles...")
    next_bundles = get_bundle_complementary(priority="SKU", depth=5)
    for b in next_bundles:
        added_profit = evaluate_bundle(b, cheapness=0.5)
        bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'complementary'})

    print(f"Fetching seasonal bundles...")
    next_bundles = get_bundle_seasonal(season="jan", priority="SKU", depth=5)
    for b in next_bundles:
        added_profit = evaluate_bundle(b, cheapness=0.5)
        bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'seasonal'})

    print(f"Fetching thematic bundles...")
    next_bundles = get_bundle_thematic(priority="SKU", depth=5)
    for b in next_bundles:
        added_profit = evaluate_bundle(b, cheapness=0.5)
        bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'thematic'})

    print(f"Fetching cross-sell bundles...")
    next_bundles = get_bundle_cross_sell(priority="SKU", depth=5)
    for b in next_bundles:
        added_profit = evaluate_bundle(b, cheapness=0.5)
        bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'cross-sell'})

    if userId is None:
        print("No user profile provided, skipping personalized bundles.")
    else:

        this_user_profile = get_user_profile(userId)
        #print(f"User profile for UserID {userId}: {this_user_profile}")

        print(f"Fetching personalized frequently bought bundles...")
        next_bundles = get_bundle_personal_frequently_bought(this_user_profile, priority="SKU", depth=5)
        for b in next_bundles:
            added_profit = evaluate_bundle(b, cheapness=0.5)
            bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'personal_frequent'})

        print(f"Fetching personalized seasonal bundles...")
        next_bundles = get_bundle_personal_seasonal(this_user_profile, season="jan", priority="SKU", depth=5)
        for b in next_bundles:
            added_profit = evaluate_bundle(b, cheapness=0.5)
            bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'personal_seasonal'})

        print(f"Fetching personalized discounts bundles...")
        next_bundles = get_bundle_personalized_discounts(this_user_profile)
        for b in next_bundles:
            added_profit = evaluate_bundle(b, cheapness=0.5)
            bundles.append({'bundle':b, 'added_profit':added_profit, 'bundle_type': 'personal_discount'})
    
    # Sort bundles by added profit
    bundles.sort(key=lambda x: x['added_profit'], reverse=True)
    print(f"Total bundles found: {len(bundles)}")
    print(f"Top bundles by added profit:")

    total_added_profit = 0
    for b in bundles[:20]:
        print(f"\n\tBundle: {b['bundle']}, Added Profit: ${b['added_profit']:.2f}, Type: {b['bundle_type']}")
        total_added_profit += b['added_profit']

    avg_added_profit = get_average_added_profit(bundles)
    return bundles, avg_added_profit


def get_average_added_profit(example_user_id):
    _, avg = get_all_bundles(example_user_id)
    return avg


if __name__ == "__main__":
    example_user_id = 44175
    get_all_bundles(example_user_id)
