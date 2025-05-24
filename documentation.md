## Project Documentation

In this project we aim to create discounted bundles of products to increase sales and revenue.
In order to do that we needed to analyze the data, find patterns in customer behavior, and create algorithms to suggest bundles.
We started by extracting features from the data, such as product categories, seasonality, and customer preferences.
The scripts for this are located in the `preprocess` folder. The results are:

- updated invetory.csv [new, extended version of the original inventory.csv file] with final columns:
    - SKU
    - Quantity
    - ProductCategory
    - ProductName
    - Margin (profit margin)
    - Seasonality (range of best selling months, e.g. "apr-aug")
    - AverageDiscount
    - OrderCount_Ratio_Discounted_vs_FullPrice (ratio that shows how many orders were made with discount vs full price)
    - BasePrice (the price of the product without discount)

- updated orders.csv:
    - made every unique SKU have the same category (some had 2 or more different categories)
    - made every unique SKU have the same name (some had 2 or more different names)
    - dropped "Brand" column (not used)

- created categories.csv with columns:
    - Category
    - TotalQuantity (how many products were sold from thius category)
    This file was later fed into Gemini AI to generate a shorter list of general categories used in `src/user_profiling.py`

- created bought_together.csv [only contains product that exist in custom_inventory.csv] with columns:
    - Product1
    - Product2
    - Count (how many times these two products were bought together)

- user_profiling.py returns:
    - user_id
    - most frequently bought products (and how many times)
    - average time interval between purchases for each user
    - user seasonality (if there is a season when the user buys more)
    - gender
    - price segment (cheap, average, luxury)
    - category segment (electronics, clothing, etc.)
    - discount_preference (percentage of orders with discount - max 1.0)
    - average discount (average discount percentage for the user - max 1.0)
    This script is used to parse the nessessary data for generating personalized bundles

> **Important Notice:** For security purposes our API key is not published in the repo. You must rename the `.env2` file to `.env` and provide your own Gemini API key.

Then, we created the script `src/suggest_bundles.py` that uses the data from the above files to suggest bundles based on different algorithms.
There are 6 different bundle types:

- complementary: products that are often bought together
- seasonal: products that are bought in a specific season
- thematic: products that are in the same category (e.g. school supplies)
- cross-sell: random product of low and high margin
- personalized 1: frequently bought by the user - add a third product to the two products that the user buys together frequently
- personalized 2: seasonal by user - find products that the user buys in a specific season (same seasonality and similar category)
- personalized 3: discount preferrers - to people with high discount preference, offer leftover products and high SKU we want to get rid of

A system admin can request for a specific bundle to be generated or not specify anything and the script will auutomatically suggest the
most profitable bundles. All functions have an optional parameter to prioritize leftover products, and products with high SKU.
Another parameter called `cheapness` can be set to suggest bundles with higher or lower discounts.

Another important part of the project is to estimate the revenue and predict future sales.
Using the script `src/revenue_forecast.py`, we can visualize historical revenue over time and predict future revenue using machine learning.
In addition, we can predict improved revenue with bundles using machine learning as well.
The expected increase in revenue was calculated as follows:
- For each bundle, we calculate the expected revenue increase by subtracting the final bundle price from the price of the first product of the bundle,
suggesting that this would be bought anyway. Then we multiply this by 0.1 which is the conversion rate. The final value is multiplied by the forecasted
total orders of each day and the result represents the increse in revenue for that day.

Finally, a GUI can be used to suggest the best bundles, and a chatbot can help you answer any questins about bundling.
The GUI can be launched by running the `src/gui.py` script.

