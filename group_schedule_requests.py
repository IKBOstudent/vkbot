import re
import os
import math
import datetime
import json

weekdays = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]


def parser_for_weeks(s, flag_krome):
    if flag_krome:
        s = s.replace("кр.", "")
    s = s.replace("н.", "")
    s = s.strip()
    weeks = s.split(',')
    for w in range(len(weeks)):
        if "-" in weeks[w]:
            new = weeks[w].split('-')
            weeks[w] = new[0]
            for j in range(int(new[0]) + 1, int(new[1]) + 1):
                weeks.append(j)

    weeks = list(map(int, weeks))
    return weeks


def formatted_message(schedule_data, weekday, col_name, current_week):
    message = ""
    for i in range(1, 7):
        num = str(i)
        subject = schedule_data[col_name][weekday][num]["subject"]
        type_sub = schedule_data[col_name][weekday][num]["type"]
        aud = schedule_data[col_name][weekday][num]["aud"]
        teacher = schedule_data[col_name][weekday][num]["teacher"]

        if subject == "-":
            message += f"\n{num}. -"
        else:
            subject = subject.replace("  ", " ")
            count = 0
            chose = -1
            no_split = False
            no_split_subject = []
            if "(1 п/г)" in subject and "(2 п/г)" in subject:
                no_split = True

            for sub in subject.split("\n"):
                count += 1

                good = True
                match2 = re.findall(r"кр\. [0-9].*н\. ", sub)
                sub = re.sub(r"кр\. [0-9].*н\. ", "", sub).strip()

                match1 = re.findall(r"[0-9].*н\. ", sub)
                sub = re.sub(r"[0-9].*н\. ", "", sub).strip()
                if match2:
                    for match in match2:
                        weeks = parser_for_weeks(match, True)
                        if current_week in weeks:
                            good = False

                elif match1:
                    for match in match1:
                        weeks = parser_for_weeks(match, False)
                        if current_week not in weeks:
                            good = False

                if good:
                    if no_split:
                        chose = 0
                        no_split_subject.append(sub)
                    else:
                        chose = count - 1
                        subject = sub
                        break

            if no_split:
                type_sub = type_sub.split('\n')
                aud = aud.split('\n')
                teacher = teacher.split('\n')
                for j in range(len(no_split_subject)):
                    message += f'\n{num}. {no_split_subject[j]}'

                    a = type_sub[j].replace("  ", " ")
                    message += f' ({a.strip()})'

                    b = aud[j].replace("  ", " ")
                    message += f', ауд. {b.strip()}'

                    c = teacher[j].replace("  ", " ")
                    message += f', ауд. {c.strip()}'

            elif chose != -1:
                message += "\n" + f'{i}. {subject}'
                if type_sub != '-':
                    type_sub = type_sub.split('\n')[chose]
                    type_sub = type_sub.replace("  ", " ")
                    message += f' ({type_sub})'
                if aud != '-':
                    aud = aud.split('\n')[chose]
                    aud = aud.replace("  ", " ")
                    message += f', ауд. {aud}'
                if teacher != '-':
                    teacher = teacher.split('\n')[chose]
                    teacher = teacher.replace("  ", " ")
                    message += f', преп. {teacher}'
            else:
                message += f"\n{num}. -"

    return message


def make_group_schedule_message(group, command):
    group = group.upper()
    print("group", group, command)
    current_week = datetime.datetime.now().date() - \
                   datetime.datetime.strptime("07.02.2022", '%d.%m.%Y').date()
    current_week = math.ceil(current_week.days / 7)
    even_week = current_week % 2 == 0

    today = datetime.datetime.now().weekday()
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).weekday()

    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    for group_data in file_data["groups"]:
        if group_data["group"] == group:
            schedule_data = group_data["timetable"]

            if not schedule_data:
                print("Ошибка группы")
                return ["Ошибка группы"]
            else:
                result = []
                if command == "TOD":
                    message = "Расписание на сегодня\n"
                    col_name = "even" if even_week else "odd"
                    message += formatted_message(schedule_data, weekdays[today], col_name, current_week)
                    result.append(message)

                elif command == "TOM":
                    if tomorrow == 6:
                        message = "Завтра воскресенье"
                    else:
                        message = "Расписание на завтра\n"
                        col_name = "even" if even_week else "odd"
                        if tomorrow == 0:
                            current_week += 1
                            col_name = "odd" if even_week else "even"
                        message += formatted_message(schedule_data, weekdays[tomorrow], col_name, current_week)
                    result.append(message)

                elif command == "THIS WEEK":
                    col_name = "even" if even_week else "odd"
                    for i in range(6):
                        message = ""
                        if i == 0:
                            message += "Расписание на эту неделю"
                        message += "\n\n" + weekdays[i]
                        message += formatted_message(schedule_data, weekdays[i], col_name, current_week)
                        result.append(message)

                elif command == "NEXT WEEK":
                    col_name = "odd" if even_week else "even"
                    for i in range(6):
                        message = ""
                        if i == 0:
                            message += "Расписание на следующую неделю"
                        message += "\n\n" + weekdays[i]
                        message += formatted_message(schedule_data, weekdays[i], col_name, current_week+1)
                        result.append(message)

                elif command in weekdays:  # command - день недели
                    message = f"Расписание на {command}\n"
                    col_name = "even" if even_week else "odd"

                    message += formatted_message(schedule_data, command, col_name, current_week+1)
                    result.append(message)

                else:
                    message = "команда не распознана"
                    result.append(message)

                print(result)
                return result

