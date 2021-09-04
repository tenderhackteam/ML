import pandas as pd
from typing import Dict
import json
import pickle


def clean_json(json_str: str) -> Dict:
    aska = json_str[::-1]
    edge_inda = - aska.index("}")
    if edge_inda != 0:
        json_str = json_str[:edge_inda] + ']'
    else:
        json_str += ']'
    return json.loads(json_str)


def get_characts(obj):
    characts = set()
    if not pd.isna(obj['Характеристики СТЕ']):
        for charact in clean_json(obj['Характеристики СТЕ']):
            try:
                characts.add((charact['Name'], charact['Value']))
            except KeyError:
                pass
    return characts


def one_based_connected(id: int, topn: int):
    obj = id2obj[id]
    characts = get_characts(obj)
    candidates = {}

    for category in top8[obj['Категория']]:
        category_candidates = categories[category]
        for cand in category_candidates:
            connected_characts = get_characts(id2obj[cand])
            candidates[cand] = (len(characts & connected_characts)) ** (0.5) * 1 / 8

    for category in top5[obj['Категория']]:
        category_candidates = categories[category]
        for cand in category_candidates:
            connected_characts = get_characts(id2obj[cand])
            candidates[cand] = (len(characts & connected_characts)) ** (0.5) * 1 / 5

    for category in top3[obj['Категория']]:
        category_candidates = categories[category]
        for cand in category_candidates:
            connected_characts = get_characts(id2obj[cand])
            candidates[cand] = (len(characts & connected_characts)) ** (0.5) * 1 / 3

    if not pd.isna(obj['Другая продукция в контрактах']) and len(obj['Другая продукция в контрактах'].strip()) > 0:
        st_others = obj['Другая продукция в контрактах']
        edge_inda = -st_others[::-1].index("}")
        if edge_inda != 0:
            st_others = st_others[:edge_inda] + ']'
        else:
            st_others += ']'
        st_data = json.loads(st_others)

        for prod in st_data:
            try:
                connected_obj = prod['OtherSkuId']
                connected_characts = get_characts(decoder[connected_obj])
                candidates[connected_obj] = (len(characts & connected_characts)) ** (0.5)
            except KeyError:
                pass

    sorted_candidates = sorted(candidates, key=lambda x: -candidates[x])
    return sorted_candidates[:topn]


with open('/content/drive/MyDrive/tenderhack/id2obj.pickle', 'rb') as handle:
    id2obj = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/categories.pickle', 'rb') as handle:
    categories = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/connected_keys.pickle', 'rb') as handle:
    connected_keys = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/decoder.pickle', 'rb') as handle:
    decoder = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/top3.pickle', 'rb') as handle:
    top3 = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/top5.pickle', 'rb') as handle:
    top5 = pickle.load(handle)

with open('/content/drive/MyDrive/tenderhack/top8.pickle', 'rb') as handle:
    top8 = pickle.load(handle)

# USAGE EXAMPLE
ids = one_based_connected(34172198, 10)
