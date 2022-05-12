import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
# from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from vk_api.utils import get_random_id
import re
import os
import requests
from bs4 import BeautifulSoup
import openpyxl
import json
from weather_requests import make_weather_message
from group_schedule_requests import make_group_schedule_message
from teacher_schedule_requests import make_teacher_schedule_message
from find_teacher import find_teacher
from find_group import find_group
from Client import Client


class Bot:
    def __init__(self, vk, long_poll):
        self.vk = vk
        self.long_poll = long_poll

        self.users = {}

        self.standard_keys = "keyboard/default.json"
        self.group_schedule_keys = "keyboard/group_schedule_keys.json"
        self.teacher_schedule_keys = "keyboard/teacher_schedule_keys.json"
        self.choose_teacher_keys = "keyboard/choose.json"
        self.weather_keys = "keyboard/weather_keys.json"
        self.cancel_keys = "keyboard/cancel.json"

    def send_message(self, user_id, message, keyboard=None):
        try:
            if keyboard:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    keyboard=open(keyboard, "r", encoding="UTF-8").read(),
                    message=message
                )
            else:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    message=message
                )

        except vk_api.ApiError:
            print("Ошибка доступа")

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
                received_msg = event.text
                msg_from = event.user_id

                print(f'New message from {msg_from}, text = {received_msg}')

                if msg_from not in self.users:
                    self.users[msg_from] = Client()

                if re.search(r"[Нн]ачать", received_msg):
                    message = "Этот бот позволяет узнать расписание любой группы и любого преподавателя. " \
                              "\n\nТакже Вы можете узнать погоду на выбранное время в Москве. " \
                              "\n\nЧтобы вернуться в главное меню напишите в чат \"Домой\""
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                if re.search(r"[Оо]тменить", received_msg):
                    self.users[msg_from].mode = 0
                    message = "Вы вернулись в основное меню"
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                good_msg = True

                if self.users[msg_from].mode == 1:  # меню с расписанием
                    good_msg = self.group_schedule_handler(received_msg, msg_from)
                elif self.users[msg_from].mode == 2:  # меню с погодой
                    good_msg = self.weather_handler(received_msg, msg_from)
                elif self.users[msg_from].mode == 3:  # меню с расписанием преподавателя
                    good_msg = self.teacher_schedule_handler(received_msg, msg_from)
                elif self.users[msg_from].mode == 4:  # статус ввода группы
                    group = re.search(r"[а-яА-Я]{4}\-\d\d\-\d\d", received_msg)
                    if group and find_group(group.group(0)):
                        self.users[msg_from].group = group.group(0)
                        message = "Текущая группа: " + group.group(0)
                        self.users[msg_from].mode = 1
                        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
                    else:
                        message = "Такой группы нет(\nПопробуйте еще раз..."
                        self.send_message(msg_from, message, keyboard=self.cancel_keys)
                    continue

                elif self.users[msg_from].mode == 5:  # статус ввода преподавателя
                    if received_msg not in self.users[msg_from].teachers:
                        self.send_message(msg_from, "Такого варианта нет(\nПопробуйте другой...",
                                          keyboard=self.choose_teacher_keys)
                        continue

                    self.users[msg_from].teacher = received_msg
                    message = "Выбранный преподаватель: " + received_msg

                    self.send_message(msg_from, message, keyboard=self.teacher_schedule_keys)
                    self.users[msg_from].mode = 3
                    continue

                if self.users[msg_from].mode == 0 or not good_msg:
                    if re.search(r"расписание", received_msg):
                        self.users[msg_from].mode = 4
                        self.send_message(msg_from, "Введите название группы",
                                          keyboard=self.cancel_keys)

                    elif re.search(r"[Нн]айти", received_msg):
                        self.users[msg_from].mode = 3
                        name = re.sub(r"[Нн]айти\s+", '', received_msg)
                        teachers = find_teacher(name)
                        self.users[msg_from].teachers = teachers
                        print(teachers)

                        if not teachers:
                            self.send_message(msg_from, "Такого преподавателя нет(",
                                              keyboard=self.standard_keys)
                        elif len(teachers) > 1:
                            self.users[msg_from].mode = 5
                            self.make_choose_keys(teachers)
                            self.send_message(msg_from, "Выберите имя преподавателя",
                                              keyboard=self.choose_teacher_keys)
                        else:
                            self.users[msg_from].teacher = name
                            self.send_message(msg_from, "Открываю меню расписания преподавателя",
                                              keyboard=self.teacher_schedule_keys)

                    elif re.search(r"погода", received_msg):
                        self.users[msg_from].mode = 2
                        self.send_message(msg_from, "Открываю меню погоды",
                                          keyboard=self.weather_keys)

                    elif re.search(r"помощь", received_msg):
                        self.users[msg_from].mode = 0
                        message = "Чтобы пользоваться ботом напишите в чат что-нибудь..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

                    else:
                        self.users[msg_from].mode = 0
                        message = "Не понял Вас..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

    def group_schedule_handler(self, msg, msg_from):
        open_schedule = False
        command = ""
        if "сегодня" in msg.lower():
            message = "TOD"
            open_schedule = True
            command = message
        elif "завтра" in msg.lower():
            message = "TOM"
            open_schedule = True
            command = message
        elif "на эту неделю" in msg.lower():
            message = "THIS WEEK"
            open_schedule = True
            command = message
        elif "на следующую неделю" in msg.lower():
            message = "NEXT WEEK"
            open_schedule = True
            command = message
        elif "какая неделя" in msg.lower():
            message = "Идет 15 неделя"
        elif "какая группа" in msg.lower():
            message = "Показываю расписание группы " + self.users[msg_from].group
        else:
            self.users[msg_from].mode = 0
            return False

        if open_schedule:
            self.teacher_schedule_parser(self.users[msg_from].group, command)
        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
        return True

    def teacher_schedule_handler(self, msg, msg_from):
        if "сегодня" in msg.lower():
            command = "TOD"
        elif "завтра" in msg.lower():
            command = "TOM"
        elif "на эту неделю" in msg.lower():
            command = "THIS WEEK"
        elif "на следующую неделю" in msg.lower():
            command = "NEXT WEEK"
        else:
            self.users[msg_from].mode = 0
            return False

        self.teacher_schedule_parser(msg, command)
        self.send_message(msg_from, command, keyboard=self.teacher_schedule_keys)
        return True

    def make_choose_keys(self, teachers):
        teachers.append("Отменить")

        with open(self.choose_teacher_keys, 'w', encoding="utf-8") as file:
            file_data = {"one_time": True, "buttons":[]}

            for i in teachers:
                color = "primary"

                if i == "Отменить":
                    color = "negative"
                new_key = {
                    "action": {
                        "type": "text",
                        "label": i
                    },
                    "color": color
                }
                file_data["buttons"].append([new_key])

            file.seek(0)
            json.dump(file_data, file, indent=4, ensure_ascii=False)


    def weather_handler(self, msg, msg_from):
        if "сейчас" in msg.lower():
            message = "NOW"
        elif "сегодня" in msg.lower():
            message = "TOD"
        elif "завтра" in msg.lower():
            message = "TOM"
        elif "недел" in msg.lower():
            message = "WEEK"
        else:
            self.users[msg_from].mode = 0
            return False

        self.weather_parser(message)

        self.send_message(msg_from, message, keyboard=self.weather_keys)
        return True

    def group_schedule_parser(self, group, command):
        make_group_schedule_message(group, command)

    def teacher_schedule_parser(self, teacher, command):
        make_teacher_schedule_message(teacher, command)

    def weather_parser(self, date):
        make_weather_message(date)


def main():
    with open("file.txt", 'r') as f:
        vk_session = vk_api.VkApi(token=f.readline())

    vk = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)

    vkbot = Bot(vk, long_poll)
    vkbot.start()
    # vkbot.weather_parser("WEEK")
    # vkbot.group_schedule_parser("икбо-08-21")
    # vkbot.teacher_schedule_parser("Берков")
    # vkbot.make_choose_keys(["иванова ев", "иванова са"])


if __name__ == "__main__":
    main()
