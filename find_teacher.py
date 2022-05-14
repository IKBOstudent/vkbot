import os
import json


def find_teacher(teacher):
    teacher = teacher.lower()
    different_teachers = []

    filepath = os.path.abspath(os.curdir) + "/tables/teachers.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        teachers = json.load(file)

    for t in teachers["teachers"]:
        if teacher in t.lower():
            if t not in different_teachers:
                different_teachers.append(t)

    return different_teachers
