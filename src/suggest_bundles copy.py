import json
import pandas as pd





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

def get_bundle_thematic(priority=None, depth=5):
    """
    Reads ../data/custom_inventory.csv and returns [depth] combinations of 2-3 products that have the same ProductCategory.
    If priority==None: do as normal
    If priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 2-3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """


def get_bundle_cross_sell(priority=None, depth=5):
    """
    Reads ../data/custom_inventory.csv (SKU,Quantity,ProductCategory,ProductName,Margin
        AverageDiscount,OrderCount_Ratio_Discounted_vs_FullPrice,Seasonality)
        and returns [depth] combinations of 2 products. The 2 products must be one with low profit margin and one with high.

    if priority==None: do as normal
    if priority=="SKU": then sort custom_inventory.csv by SKU and return [depth] bundles that each of them contains 3
        products as before but at least one of them must be in the top list of the sorted by SKU list.
    """

def get_bundle_personal_frequently_bought(userId, priority=None, depth=5):
    """
    Gets profile data from userid and finds the two most bought products by the user.
    Then adds another product with them based on priority.
    If priority==None: do as normal, 3rd product is a low margin
    if priority=="SKU": then sort custom_inventory.csv by SKU and 3rd product is the top from the list.
    """


def get_bundle_personal_seasonal(userId, season=None, priority=None, depth=5):
    """
    Gets profile data from userid and finds the seasonality of the user - if exists.
    Then finds top product bought by the user that has the same seasonality.
    Then finds another product with the same seasonality that the user doesnt buy usually.
    Create the 2-product bundle.

    if priority==None: do as normal, 2nd product is random
    if priority=="SKU": then sort custom_inventory.csv by SKU and 2nd product is the top from the list.
    """


def get_bundle_personalized_discounts(userId):
    """
    Gets profile data from userid, anf from there if discount_preference > 0.6 then
    sort products in custom_inventory.csv by SKU and create one bundle of the top 3 products,
    and one bundle of the top 2 producs. Return the 2 bundles.
    """




def evaluate_bundle(bundle):
    """
    Returns expected increase in profit. For example bundle has 2 products, the first would be bought anyway but
    the second wouldnt, but there is also a discount so increase in profits is
    (productA_price + probability_of_selling_product_B * productB_price) * (1 - discount) - productA_price.
    """



def get_all_bundles(userId):
    """
    Find all bundles, evaluate them and choose the best
    """
    bundles = []
    bundles.append(get_bundle_complementary())
    bundles.append(get_bundle_seasonal())
    bundles.append(get_bundle_thematic())
    bundles.append(get_bundle_cross_sell())
    bundles.append(get_bundle_personal_frequently_bought(userId))
    bundles.append(get_bundle_personal_seasonal(userId))
    bundles.append(get_bundle_personalized_discounts(userId))


    for b in bundles:
        if b is not None:
            print(f"Bundle: {b}")

    




if __name__ == "__main__":

    example_user_id = 44175
    get_all_bundles(example_user_id)
