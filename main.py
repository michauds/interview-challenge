# -*- coding utf-8 -*-
import re
import json

PRODUCTS_FILE = 'products.txt'
LISTINGS_FILE = 'listings.txt'
MATCHES_FILE = 'matches.txt'


class Inventory:
    def __init__(self, product_list=None):
        self.product_list = []
        self.manufacturer_index = {}

        if product_list:
            for item in product_list:
                self.add_product(item)

    def items_by_manufacturer(self, manufacturer):
        return self.manufacturer_index.get(manufacturer, [])

    def add_product(self, product):
        self.product_list.append(product)
        try:
            self.manufacturer_index[product.manufacturer].append(product)
        except KeyError:
            self.manufacturer_index[product.manufacturer] = [product]

class Product:
    def __init__(self, manufacturer, model, product_name, announced_date, family):
        self.product_name = product_name
        self.manufacturer = manufacturer
        self.model = model
        self.announced_date = announced_date
        self.family = family

    def __repr__(self):
        return ('Product<manufacturer={},model={},'
                'product_name={}>'.format(self.manufacturer,
                                          self.model,
                                          self.product_name))


class Listing:
    def __init__(self, title, manufacturer, currency, price):
        self.title = title
        self.manufacturer = manufacturer
        self.currency = currency
        self.price = price

    def __repr__(self):
        return 'Listing<title={}>'.format(self.title)


class Matcher:

    @staticmethod
    def manufacturer_match(manufacturer_list, listing):
        """
        Takes a list of manufacturers (idealy provided from the inventory) and
        matches against the one in provided listing
        :param manufacturer_list:
        :param listing:
        :return: Capitalized string of the matched manufacturer or None
        """
        matched_brands = []
        for brand in manufacturer_list:
            matched = re.match(brand, listing.title, flags=re.IGNORECASE)

            if matched:
                matched_brands.append(brand)

        if len(matched_brands) == 1:
            return matched_brands[0]
        return None

    @staticmethod
    def product_name_match(product, listing):
        """
        Attempts to find all the parts of the product name in the listing's
        title.
        :param product:
        :param listing:
        :return: True if the entire product name is present in listing
        """
        pn_keywords = [kw.upper() for kw in re.split('[_-]', product.product_name)]

        product_regex = ''

        for kw in pn_keywords:
            product_regex = product_regex + '(' + kw + ')' + '{1}.*'

        compiled_regex = re.compile(product_regex, flags=re.IGNORECASE)

        regex_match = re.match(compiled_regex, listing.title)

        return regex_match, 80

    @staticmethod
    def find_match(product_list, listing):
        """
        Applies the list of matchers against the list of products provided
        in `product_list` and the listing.

        Each potential match is given a score, yet only the best match is
        returned.
        :param product_list:
        :param listing:
        :return: the closest matching instance of Product to
        the provided listing or None
        """
        potential_fits = []

        for product in sorted(product_list, key=lambda x:x.product_name):
            # We order the list by length of product name. Logic here is that
            # the longer product name would be more specific

            match, confidence_bonus = Matcher.product_name_match(product, listing)

            if match:
                potential_fits.append(product)

        if potential_fits:
            # Since we've ordered the list of products by product_name
            # we can assume the last element of the list is the most specific
            # and therefore the best match
            return potential_fits[-1]
        return None


def load_products(products_fp):
    products = []
    for line in products_fp:
        try:
            product_json = json.loads(line.strip())
            new_product = Product(product_json['manufacturer'],
                                  product_json['model'],
                                  product_json['product_name'],
                                  product_json['announced-date'],
                                  product_json.get('family'))

            products.append(new_product)

        except json.JSONDecodeError:
            print('Error deserializing {}, not a valid json string'.format(line))

    return products

def load_listings(listings_fp):
    listings = []
    for line in listings_fp:
        listing_json = json.loads(line.strip())
        new_listing = Listing(listing_json['title'],
                              listing_json['manufacturer'],
                              listing_json['currency'],
                              listing_json['price'])

        listings = list.append(new_listing)

    return listings


if __name__ == '__main__':
    with open(PRODUCTS_FILE) as products_fp, \
            open(LISTINGS_FILE) as listings_fp:
        product_list = load_products(products_fp)

        # Since there's only 20k listings, I took the luxury of loading
        # everything into RAM, however at a larger scale, it would be
        # better to read only a single row at a time.
        listing_list = load_listings(listings_fp)

    matches = {}
    inventory = Inventory(product_list)

    for listing in listing_list:
        inv_manufacturers = list(inventory.manufacturer_index.keys())
        listing_manufacturer = Matcher.manufacturer_match(inv_manufacturers,
                                                          listing)

        potential_items = inventory.items_by_manufacturer(listing_manufacturer)

        if not potential_items:
            continue

        matched_item = Matcher.find_match(potential_items, listing)

        if matched_item:
            matches[listing.title] = matched_item.__dict__

    with open(MATCHES_FILE, 'w') as matches_fp:
        matches_fp.write(json.dumps(matches))
