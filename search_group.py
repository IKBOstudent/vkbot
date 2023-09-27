import os
import json
import datetime


def find_group(group):
    group = group.upper()
    found = False

    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    course = datetime.datetime.now().year % 100 - int(group[-2:])
    if 1 <= course <= 4:
        for group_data in file_data["groups"]:
            if group_data["group"] == group:
                found = True
                break

    return found
