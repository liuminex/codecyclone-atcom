import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

genai.configure(api_key=GEMINI_API_KEY)

# Load orders.csv globally
orders_df = pd.read_csv('../data/orders.csv', parse_dates=['CreatedDate'])
orders_df = orders_df.dropna(subset=['UserID'])

# Predefined category segments
category_segments = [
    "Beauty Products",
    "Men's Clothing",
    "Women's Clothing",
    "Makeup",
    "Perfumes & Fragrances",
    "Sports & Outdoors",
    "Home & Kitchen",
    "Electronics",
    "Bags & Accessories",
    "Shoes",
    "Kids & Baby",
    "Jewelry",
    "Underwear & Lingerie",
    "Swimwear",
    "Home Decor",
    "Bath & Body",
    "Skin Care",
    "Hair Care",
    "Bedding",
    "Towels",
    "Christmas Decor",
    "Office Supplies",
    "Kitchenware",
    "Dining",
    "Athletic Clothing",
    "Outerwear",
    "Jeans",
    "Pajamas",
    "Socks & Hosiery",
    "Travel Accessories"
]

import re

def determine_user_attributes_gemini(shopping_data_lines):
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = (
        "You're a customer profiling AI. Based on the shopping data below, determine:\n"
        "- Gender (male, female, or undetermined) (not all items need to be male or female - just consider the majority of them)\n"
        "- Price segment (cheap, average, luxury, or undetermined)\n"
        f"- Category segment (only choose one from: {', '.join(category_segments)})\n\n"
        "Shopping history:\n" + "\n".join(shopping_data_lines) +
        "\n\nRespond in JSON format like this:\n"
        '{\n  "gender": "...",\n  "price_segment": "...",\n  "category_segment": "..."\n}'
    )

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Attempt to extract JSON block from raw text using regex
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in Gemini response")

        cleaned_json = json_match.group(0)
        attributes = json.loads(cleaned_json)

        return {
            "gender": attributes.get("gender", "undetermined"),
            "price_segment": attributes.get("price_segment", "average"),
            "category_segment": attributes.get("category_segment", ["other"])
        }

    except Exception as e:
        print(f"Gemini API Error: {e}\nRaw Response:\n{response.text if 'response' in locals() else 'No response'}")
        return {
            "gender": "undetermined",
            "price_segment": "average",
            "category_segment": ["other"]
        }




def get_user_profile(userid):
    user_orders = orders_df[orders_df['UserID'] == userid].copy()

    print(f"Getting profile for user ID: {userid}")

    if user_orders.empty:
        print(f"No orders found for user ID: {userid}")
        return None

    # Determine discounted vs full price items
    user_orders['DiscountAmount'] = (user_orders['OriginalUnitPrice'] - user_orders['FinalUnitPrice']).clip(lower=0)
    user_orders['HasDiscount'] = user_orders['DiscountAmount'] > 0

    # Calculate discount preference
    total_discounted_quantity = user_orders[user_orders['HasDiscount']]['Quantity'].sum()
    total_fullprice_quantity = user_orders[~user_orders['HasDiscount']]['Quantity'].sum()
    total_quantity = total_discounted_quantity + total_fullprice_quantity

    discount_preference = (
        round(total_discounted_quantity / total_quantity, 4)
        if total_quantity > 0 else None
    )

    # Calculate average discount (only for discounted rows)
    discounted = user_orders[user_orders['HasDiscount']]
    if not discounted.empty:
        average_discount = (
            (discounted['DiscountAmount'] / discounted['OriginalUnitPrice'])
            .replace([float('inf'), -float('inf')], pd.NA)
            .dropna()
            .mean()
        )
        average_discount = round(average_discount, 4)
    else:
        average_discount = 0.0

    # Most frequent products by order count
    sku_order_counts = (
        user_orders.groupby('SKU')['OrderNumber']
        .nunique()
        .reset_index(name='TimesOrdered')
    )

    sku_order_counts = sku_order_counts[sku_order_counts['TimesOrdered'] >= 2]
    sku_order_counts = sku_order_counts.sort_values(by='TimesOrdered', ascending=False)

    sku_order_counts = sku_order_counts.merge(
        user_orders[['SKU', 'Item title']].drop_duplicates(), on='SKU', how='left'
    )

    # Order frequency
    user_order_dates = user_orders[['OrderNumber', 'CreatedDate']].drop_duplicates().sort_values(by='CreatedDate')
    user_order_dates['PrevDate'] = user_order_dates['CreatedDate'].shift()
    user_order_dates['DaysBetween'] = (user_order_dates['CreatedDate'] - user_order_dates['PrevDate']).dt.days
    avg_days_between_orders = user_order_dates['DaysBetween'].mean()

    # Seasonality
    user_orders['Month'] = user_orders['CreatedDate'].dt.month
    month_counts = user_orders['Month'].value_counts().sort_index()
    seasonal_trend = (
        f"User orders more in month {month_counts.idxmax()}."
        if month_counts.max() >= 2 * month_counts.mean()
        else "No strong seasonal trend."
    )

    # Top 10 SKUs for profiling
    top_10_skus = sku_order_counts.head(10)['SKU'].tolist()
    top_orders = user_orders[user_orders['SKU'].isin(top_10_skus)]

    unique_rows = top_orders[['Category', 'Brand', 'Item title']].drop_duplicates().astype(str)
    shopping_history_lines = unique_rows.apply(
        lambda row: f"{row['Category']} | {row['Brand']} | {row['Item title']}",
        axis=1
    ).tolist()

    user_attributes = determine_user_attributes_gemini(shopping_history_lines)

    return {
        "UserID": userid,
        "MostFrequentProducts": sku_order_counts[['SKU', 'Item title', 'TimesOrdered']].to_dict(orient='records'),
        "AverageDaysBetweenOrders": round(avg_days_between_orders, 2) if not pd.isna(avg_days_between_orders) else "Only one order",
        "SeasonalTrend": seasonal_trend,
        "UserAttributes": user_attributes,
        "DiscountPreference": discount_preference,
        "AverageDiscount": average_discount
    }





# Example usage
if __name__ == "__main__":

    user_ids = orders_df['UserID'].drop_duplicates().tolist()[:3]
    # 44175
    for userId in user_ids:
        profile = get_user_profile(userId)#["UserAttributes"]
        print(json.dumps(profile, indent=2, ensure_ascii=False))
