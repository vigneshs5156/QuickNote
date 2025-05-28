from fuzzywuzzy import process
import pandas as pd
import json

Menu = {
    'Items': [
        "chicken burger", "veg momos", "french fries", "veg sandwich",
        "chicken juicy burger", "veg pizza", "burrito", "paneer momos",
        "vadapav", "chicken pizza", "hamburger", "club sandwich", "chicken pizza"
    ],
    'Price': [40, 40, 65, 40, 65, 65, 60, 65, 60, 65, 65, 65, 40]
}

# Create a lookup dictionary
menu_lookup = dict(zip(Menu['Items'], Menu['Price']))
menu_df = pd.DataFrame(Menu)

def match_item(item):
    menu_items = Menu['Items']
    match, score = process.extractOne(item.lower(), menu_items)
    return match if score > 50 else item

def get_df(string):
    first = string.find('{')
    last = string.rfind('}')
    json_str = string[first:last+1]
    data = json.loads(json_str)

    df = pd.DataFrame(list(data.items()), columns=['Item', 'Quantity'])
    df['Item'] = df['Item'].apply(match_item)
    df['Price'] = df['Item'].apply(lambda x: menu_lookup.get(x, 0))
    df['Total'] = df['Price'] * df['Quantity']

    return df
