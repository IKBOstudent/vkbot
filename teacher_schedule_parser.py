import os
import json
import datetime

weekdays = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]


def teacher_schedule_parser():
    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    schedule_data = {"odd": {}, "even": {}}
    for d in weekdays:
        schedule_data["odd"].update({d: {}})
        schedule_data["even"].update({d: {}})
        for n in "123456":
            schedule_data["odd"][d].update({n: {}})
            schedule_data["even"][d].update({n: {}})
            for f in "group", "subject", "aud":
                schedule_data["odd"][d][n].update({f: '-'})
                schedule_data["even"][d][n].update({f: '-'})

    for group_data in file_data["groups"]:
        for col_name in "odd", "even":
            for wd in weekdays:
                for num in range(1, 7):
                    teacher = group_data["timetable"][col_name][wd][str(num)]["teacher"]
                    if teacher != '-':
                        print(teacher)

