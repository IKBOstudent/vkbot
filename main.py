import urllib3
import math
import datetime
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
# from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from vk_api.utils import get_random_id
import re
import os
import requests
import json
from weather_requests import make_weather_message
from group_schedule_requests import make_group_schedule_message
from teacher_schedule_requests import make_teacher_schedule_message
from find_teacher import find_teacher
from find_group import find_group
from Client import Client


class Bot:
    def __init__(self, vk_session, vk, long_poll):
        self.vk_session = vk_session
        self.vk = vk
        self.long_poll = long_poll

        self.USERS = {}

        self.standard_keys = "keyboard/default.json"
        self.group_schedule_keys = "keyboard/group_schedule_keys.json"
        self.teacher_schedule_keys = "keyboard/teacher_schedule_keys.json"
        self.choose_teacher_keys = "keyboard/choose.json"
        self.weather_keys = "keyboard/weather_keys.json"
        self.cancel_keys = "keyboard/cancel.json"

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        try:
            if attachment and keyboard:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    keyboard=open(keyboard, "r", encoding="UTF-8").read(),
                    message=message,
                    attachment=attachment
                )
            elif keyboard:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    keyboard=open(keyboard, "r", encoding="UTF-8").read(),
                    message=message
                )
            elif attachment:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    message=message,
                    attachment=attachment
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

                if msg_from not in self.USERS:
                    self.USERS[msg_from] = Client()

                if re.search(r"[Нн]ачать", received_msg):
                    message = "Этот бот позволяет узнать расписание любой группы и любого преподавателя. " \
                              "\n\nТакже Вы можете узнать погоду на выбранное время в Москве. " \
                              "\n\nЧтобы вернуться в главное меню напишите в чат \"Домой\""
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                if re.search(r"[Оо]тменить", received_msg):
                    self.USERS[msg_from].mode = 0
                    message = "Вы вернулись в основное меню"
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                good_msg = True

                if self.USERS[msg_from].mode == 1:  # меню с расписанием
                    good_msg = self.group_schedule_handler(received_msg, msg_from)
                elif self.USERS[msg_from].mode == 2:  # меню с погодой
                    good_msg = self.weather_handler(received_msg, msg_from)
                elif self.USERS[msg_from].mode == 3:  # меню с расписанием преподавателя
                    good_msg = self.teacher_schedule_handler(received_msg, msg_from)
                elif self.USERS[msg_from].mode == 4:  # статус ввода группы
                    group = re.search(r"[а-яА-Я]{4}\-\d\d\-\d\d", received_msg)
                    self.send_message(msg_from, "Поиск группы... Ожидайте.")
                    if group and find_group(group.group(0)):
                        self.USERS[msg_from].group = group.group(0).upper()
                        message = "Текущая группа: " + group.group(0).upper() + \
                                  "\nНа какой период показать расписание?"
                        self.USERS[msg_from].mode = 1
                        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
                    else:
                        message = "Такой группы нет(\nПопробуйте еще раз..."
                        self.send_message(msg_from, message, keyboard=self.cancel_keys)
                    continue

                elif self.USERS[msg_from].mode == 5:  # статус ввода преподавателя
                    if received_msg not in self.USERS[msg_from].teachers:
                        self.send_message(msg_from, "Такого варианта нет(\nПопробуйте другой...",
                                          keyboard=self.choose_teacher_keys)
                        continue

                    self.USERS[msg_from].teacher = received_msg
                    message = "Выбранный преподаватель: " + received_msg + \
                              "\nНа какой период показать расписание?"

                    self.send_message(msg_from, message, keyboard=self.teacher_schedule_keys)
                    self.USERS[msg_from].mode = 3
                    continue

                if self.USERS[msg_from].mode == 0 or not good_msg:
                    if re.search(r"[Рр]асписание", received_msg):
                        self.USERS[msg_from].mode = 4
                        self.send_message(msg_from, "Введите название группы",
                                          keyboard=self.cancel_keys)

                    elif re.search(r"[Нн]айти", received_msg):
                        self.USERS[msg_from].mode = 3
                        self.send_message(msg_from, "Поиск преподавателя... Ожидайте.")
                        name = re.sub(r"[Нн]айти\s+", '', received_msg)
                        teachers = find_teacher(name)
                        self.USERS[msg_from].teachers = teachers
                        print(teachers)

                        if not teachers:
                            self.send_message(msg_from, "Такого преподавателя нет(",
                                              keyboard=self.standard_keys)
                        elif 1 < len(teachers) <= 6:
                            self.USERS[msg_from].mode = 5
                            self.make_choose_keys(teachers)
                            self.send_message(msg_from, "Выберите имя преподавателя",
                                              keyboard=self.choose_teacher_keys)
                        elif len(teachers) >= 7:
                            self.send_message(msg_from, "По данному запросу слишком много совпадений("
                                                        "\nПопробуйте уточнить Ваш запрос...",
                                              keyboard=self.standard_keys)
                        else:
                            self.USERS[msg_from].teacher = teachers[0]
                            self.send_message(msg_from, "Открываю меню расписания преподавателя",
                                              keyboard=self.teacher_schedule_keys)

                    elif re.search(r"[Пп]огода", received_msg):
                        self.USERS[msg_from].mode = 2
                        self.send_message(msg_from, "Открываю меню погоды",
                                          keyboard=self.weather_keys)

                    elif re.search(r"[Пп]омощь", received_msg):
                        self.USERS[msg_from].mode = 0
                        message = "Чтобы пользоваться ботом напишите в чат что-нибудь..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

                    else:
                        self.USERS[msg_from].mode = 0
                        message = "Не понял Вас..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

    def group_schedule_handler(self, msg, msg_from):
        open_schedule = False
        message = "Error"
        command = "Error"
        if "сегодня" in msg.lower():
            command = "TOD"
            open_schedule = True
        elif "завтра" in msg.lower():
            command = "TOM"
            open_schedule = True
        elif "на эту неделю" in msg.lower():
            command = "THIS WEEK"
            open_schedule = True
        elif "на следующую неделю" in msg.lower():
            command = "NEXT WEEK"
            open_schedule = True
        elif "какая неделя" in msg.lower():
            current_week = datetime.datetime.now().date() - \
                           datetime.datetime.strptime("07.02.2022", '%d.%m.%Y').date()
            message = f"Идет {math.ceil(current_week.days / 7)} неделя"
        elif "какая группа" in msg.lower():
            message = "Показываю расписание группы " + self.USERS[msg_from].group
        elif "понедельник" in msg.lower():
            command = "ПН"
            open_schedule = True
        elif "вторник" in msg.lower():
            command = "ВТ"
            open_schedule = True
        elif "среда" in msg.lower():
            command = "СР"
            open_schedule = True
        elif "четверг" in msg.lower():
            command = "ЧТ"
            open_schedule = True
        elif "пятница" in msg.lower():
            command = "ПТ"
            open_schedule = True
        elif "суббота" in msg.lower():
            command = "СБ"
            open_schedule = True
        elif "воскресенье" in msg.lower():
            message = "Воскресенье - выходной"
        else:
            self.USERS[msg_from].mode = 0
            return False

        if open_schedule:
            self.send_message(msg_from, "Поиск расписания группы... Ожидайте.")
            self.group_schedule_parser(self.USERS[msg_from].group, command)
            message = f"расписание {self.USERS[msg_from].group} на {command}"
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
            self.USERS[msg_from].mode = 0
            return False

        self.send_message(msg_from, "Поиск расписания преподавателя... Ожидайте.")
        self.teacher_schedule_parser(self.USERS[msg_from].teacher, command)

        self.send_message(msg_from, f"расписание {self.USERS[msg_from].teacher} на {command}",
                          keyboard=self.teacher_schedule_keys)
        return True

    def make_choose_keys(self, teachers):
        teachers.append("Отменить")

        with open(self.choose_teacher_keys, 'w', encoding="utf-8") as file:
            file_data = {"one_time": True, "buttons": []}

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
            self.USERS[msg_from].mode = 0
            return False

        self.send_message(msg_from, "Поиск погоды... Ожидайте.")
        self.weather_parser(msg_from, message)
        return True

    def group_schedule_parser(self, group, command):
        make_group_schedule_message(group, command)

    def teacher_schedule_parser(self, teacher, command):
        make_teacher_schedule_message(teacher, command)

    def weather_parser(self, msg_from, date):
        weather = make_weather_message(date)
        upload = VkUpload(self.vk)

        if date == "WEEK":
            self.send_message(msg_from, "Погода на неделю")
            s = []
            for i in range(1, len(weather['message']), 2):
                s.append(weather['message'][i] + " | " + weather['message'][i - 1])
            print(s)
            for i in range(len(s)):
                photo = upload.photo_messages(f'icons/icon_double{i}.png')[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"

                if i == len(s) - 1:
                    self.send_message(msg_from, s[i], keyboard=self.weather_keys, attachment=attachment)
                else:
                    self.send_message(msg_from, s[i], attachment=attachment)

        elif date == "NOW":
            print(weather['message'])
            response_icon = requests.get(weather['icons'][0], stream=True)
            photo = upload.photo_messages(photos=response_icon.raw)[0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            self.send_message(msg_from, weather['message'][0], attachment=attachment, keyboard=self.weather_keys)

        else:
            if date == "TOD":
                self.send_message(msg_from, "Погода на сегодня")
            if date == "TOM":
                self.send_message(msg_from, "Погода на завтра")

            print(weather['message'])
            for i in range(len(weather['icons'])):
                response_icon = requests.get(weather['icons'][i], stream=True)
                photo = upload.photo_messages(photos=response_icon.raw)[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"

                if i == len(weather['icons']) - 1:
                    self.send_message(msg_from, weather['message'][i], attachment=attachment, keyboard=self.weather_keys)
                else:
                    self.send_message(msg_from, weather['message'][i], attachment=attachment)


def main():
    with open("file.txt", 'r') as f:
        vk_session = vk_api.VkApi(token=f.readline())

    vk = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)

    vkbot = Bot(vk_session, vk, long_poll)
    # vkbot.start()
    # vkbot.weather_parser("WEEK")
    # vkbot.teacher_schedule_parser("Берков")
    # vkbot.make_choose_keys(["иванова ев", "иванова са"])

    make_group_schedule_message("инбо-03-21", "THIS WEEK")
    # make_teacher_schedule_message("егиазарян к.т.", "TOD")
    # find_teacher("хусяин")


if __name__ == "__main__":
    main()
