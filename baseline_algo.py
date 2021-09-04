import pandas as pd
import json
from typing import Dict


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


data = pd.read_excel('/content/drive/MyDrive/tenderhack/dataset_base.xlsx')  # FILEPATH
id2obj = {}
categories = {}
connected = {}
for iterr, st in data.iterrows():
    id2obj[st['Идентификатор СТЕ']] = st

    if st['Категория'] not in categories:
        categories[st['Категория']] = []
    categories[st['Категория']].append(st['Идентификатор СТЕ'])

    if st['Категория'] not in connected:
        connected[st['Категория']] = {}
    if not pd.isna(st['Другая продукция в контрактах']) and len(st['Другая продукция в контрактах'].strip()) > 0:
        st_others = st['Другая продукция в контрактах']
        st_others = clean_json(st_others)
        for prod in st_others:
            try:
                connected_cat = id2obj[prod['OtherSkuId']]['Категория']
                if connected_cat not in connected[st['Категория']]:
                    connected[st['Категория']][connected_cat] = 0
                connected[st['Категория']][connected_cat] += 1
            except KeyError:
                pass

connected_keys = list(connected.keys())
num_cat = enumerate(connected_keys)
decoder = {category: i for i, category in num_cat}


class ComponentGetter():
    def __init__(self, topn: int):
        self.topn = topn

        self.V = [[] for i in range(len(connected))]
        self.Visited = [False] * len(connected)
        self.ncomp = 0

        for category1 in connected:
            helpers = sorted(list(connected[category1].keys()), key=lambda x: -connected[category1][x])
            for category2 in helpers[:topn]:
                if category2 != category1:
                    self.V[decoder[category1]].append(decoder[category2])

        for i in range(0, len(connected)):
            if not self.Visited[i]:
                self.ncomp += 1
                self.DFS(i, self.ncomp)

        self.components = [[] for i in range(self.ncomp)]
        for i in range(len(self.Visited)):
            self.components[self.Visited[i] - 1].append(connected_keys[i])
        self.comp_dict = {}
        for component in self.components:
            for element in component:
                self.comp_dict[element] = component

    def DFS(self, start, number):
        self.Visited[start] = number
        for v in self.V[start]:
            if not self.Visited[v]:
                self.DFS(v, number)

    def get_categories(self, category: str):
        return self.comp_dict[category]


top3 = ComponentGetter(3)
top5 = ComponentGetter(5)
top8 = ComponentGetter(8)


def one_based_connected(id: int, topn: int):
    obj = id2obj[id]
    characts = get_characts(obj)
    candidates = {}

    for category in top8.get_categories(obj['Категория']):
        category_candidates = categories[category]
        for cand in category_candidates:
            connected_characts = get_characts(id2obj[cand])
            candidates[cand] = (len(characts & connected_characts)) ** (0.5) * 1 / 8

    for category in top5.get_categories(obj['Категория']):
        category_candidates = categories[category]
        for cand in category_candidates:
            connected_characts = get_characts(id2obj[cand])
            candidates[cand] = (len(characts & connected_characts)) ** (0.5) * 1 / 5

    for category in top3.get_categories(obj['Категория']):
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


# USAGE EXAMPLE
ids = one_based_connected(34172198, 10)
