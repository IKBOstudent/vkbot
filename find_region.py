import os
import json


def find_region(region):
    region = region.lower()
    different_regions = []

    filepath = os.path.abspath(os.curdir) + "/tables/regions.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        regions = json.load(file)

    for ob in regions:
        if region in ob[1].lower():
            different_regions.append(ob)
            if len(different_regions) > 10:
                return different_regions

    return different_regions
