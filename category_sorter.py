from typing import List

import nltk
from nltk.corpus import wordnet

autocategories = {"cheese": "cheese",
                  "wipes": "cleaning",
                  "toilet": "cleaning",
                  "washing": "cleaning",
                  "soap": "cleaning",
                  "fish paste": "roe",
                  "spray": "cleaning"}

capture_categories = ["vegetable", "plant_material", "plant", "salad", "fruit", "bakery", "baked_goods", "meat", "poultry",
                      "cheese", "roe", "mexican", "olive oil", "pasta", "sauce", "grain", "salt", "preservative",
                      "dairy_product", "eggs", "spread", "orange juice", "juice", "container", "pizza", "chips", "ice cream", "fish",
                      "seafood", "nutriment", "sweetening", "flour", "porridge", "tea", "coffee", "peanut butter", "jam",
                      "cleaning", "cleansing_agent", "toiletry", "snacks", "sweet"]


def classify_term(item, capture_categories: [str]) -> str:
    """Find a match in a string with several words."""
    items = item.split(" ")
    # the last word is likely to be most meaningful
    items = reversed(items)
    for item in items:
        tmp = do_recursive_classification(item, capture_categories)
        if tmp:
            return tmp
    return None


def classify_grocery_item(item, capture_categories: [str], remaining_recursives: int = 8) -> str:
    """Find the class of the grocery item, or 'misc' if not found."""
    res = do_recursive_classification(item, capture_categories, remaining_recursives)
    if not res:
        res = "misc"
    return res


def do_recursive_classification(item, capture_categories: [str], remaining_recursives: int = 8) -> str:
    if remaining_recursives <= 0:
        return None
    res = None
    if item in autocategories:
        res = autocategories[item]
    if item in capture_categories:
        res = item
    else:
        synsets = wordnet.synsets(item)
        if len(synsets) > 0:
            synset = synsets[0]
            hypernyms = synset.hypernyms()
            if len(hypernyms) > 0:
                for hypernym in hypernyms:
                    tmp = hypernym.name().split('.')[0]
                    if tmp in capture_categories:
                        res = tmp
                        break
                if not res:
                    # No suitable hypernym found. Look for hypernyms of hypernyms
                    for hypernym in hypernyms:
                        tmp = hypernym.name().split('.')[0]
                        tmp_class = do_recursive_classification(tmp, capture_categories, remaining_recursives - 1)
                        if tmp_class:
                            res = tmp_class
                            break

    if not res and " " in item:
        res = classify_term(item, capture_categories)
    return res


def sort_items(items: [str]) -> List[str]:
    nltk.download('wordnet')
    the_list = []
    for item in items:
        classification = classify_grocery_item(item, capture_categories)
        if classification in capture_categories:
            index = capture_categories.index(classification)
            the_list.append((item, index))
        else:
            the_list.append((item, len(capture_categories)))
    the_list = sorted(the_list, key=lambda x: x[1])
    return [x[0] for x in the_list]
