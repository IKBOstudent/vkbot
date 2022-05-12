import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
# from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton
from vk_api.utils import get_random_id
import re
import requests
from bs4 import BeautifulSoup
import openpyxl
import datetime
import json


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

                if re.search(r"[Нн]ачать", received_msg):
                    message = "Этот бот позволяет узнать расписание любой группы и любого преподавателя. " \
                              "\n\nТакже Вы можете узнать погоду на выбранное время в Москве. " \
                              "\n\nЧтобы вернуться в главное меню напишите в чат \"Домой\""
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                if msg_from not in self.users:
                    self.users[msg_from] = {'mode': 0, 'group': None, 'teacher': None}

                good_msg = True

                if self.users[msg_from]['mode'] == 1:  # меню с расписанием
                    good_msg = self.group_schedule_handler(received_msg, msg_from)
                elif self.users[msg_from]['mode'] == 2:  # меню с погодой
                    good_msg = self.weather_handler(received_msg, msg_from)
                elif self.users[msg_from]['mode'] == 3:  # меню с расписанием преподавателя
                    good_msg = self.teacher_schedule_handler(received_msg, msg_from)
                elif self.users[msg_from]['mode'] == 4:  # статус ввода группы
                    find_group = re.search(r"[а-яА-Я]{4}\-\d\d\-\d\d", received_msg)
                    if find_group:
                        self.users[msg_from]['group'] = find_group.group(0)
                        message = "Текущая группа: " + find_group.group(0)
                        self.users[msg_from]['mode'] = 1
                        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
                    else:
                        message = "Такой группы нет(\nПопробуйте еще раз..."
                        self.send_message(msg_from, message)
                    continue

                elif self.users[msg_from]['mode'] == 5:  # статус ввода преподавателя
                    self.users[msg_from]['teacher'] = received_msg
                    message = "Выбранный преподаватель: " + received_msg

                    self.send_message(msg_from, message, keyboard=self.teacher_schedule_keys)
                    good_msg = self.teacher_schedule_handler(received_msg, msg_from)


                if self.users[msg_from]['mode'] == 0 or not good_msg:
                    if re.search(r"[Дд]омой", received_msg):
                        self.users[msg_from]['mode'] = 0
                        message = "Вы вернулись в основное меню"
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

                    elif re.search(r"расписание", received_msg):
                        self.users[msg_from]['mode'] = 4
                        self.send_message(msg_from, "Введите название группы")

                    elif re.search(r"[Нн]айти", received_msg):
                        name = re.sub(r"[Нн]айти\s+", '', received_msg)
                        print(name)
                        self.teacher_schedule_handler(received_msg, msg_from)

                    elif re.search(r"погода", received_msg):
                        self.users[msg_from]['mode'] = 2
                        self.send_message(msg_from, "Открываю меню погоды", keyboard=self.weather_keys)

                    elif re.search(r"помощь", received_msg):
                        self.users[msg_from]['mode'] = 0
                        message = "Чтобы пользоваться ботом напишите в чат что-нибудь..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

                    else:
                        self.users[msg_from]['mode'] = 0
                        message = "Не понял Вас..."
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

    def group_schedule_handler(self, msg, msg_from):
        if "на сегодня" in msg:
            message = "TOD"
        elif "на завтра" in msg:
            message = "TOM"
        elif "на эту неделю" in msg:
            message = "THIS WEEK"
        elif "на следующую неделю" in msg:
            message = "NEXT WEEK"
        elif "какая неделя" in msg:
            message = "Идет 15 неделя"
        elif "какая группа" in msg:
            message = "Показываю расписание группы " + self.users[msg_from]['group']
        else:
            self.users[msg_from]['mode'] = 0
            return False

        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
        return True

    def teacher_schedule_handler(self, msg, msg_from):
        # self.users[msg_from]['mode'] = 3
        # self.users[msg_from]['mode'] = 5
        if "на сегодня" in msg:
            message = "TOD"
        elif "на завтра" in msg:
            message = "TOM"
        elif "на эту неделю" in msg:
            message = "THIS WEEK"
        elif "на следующую неделю" in msg:
            message = "NEXT WEEK"
        else:
            self.users[msg_from]['mode'] = 0
            return False

        self.send_message(msg_from, message, keyboard=self.teacher_schedule_keys)
        return True

    def weather_handler(self, msg, msg_from):
        if "сейчас" in msg:
            message = "NOW"
        elif "сегодня" in msg:
            message = "TOD"
        elif "завтра" in msg:
            message = "TOM"
        elif "на неделю" in msg:
            message = "WEEK"
        else:
            self.users[msg_from]['mode'] = 0
            return False

        self.send_message(msg_from, message, keyboard=self.weather_keys)
        return True

    def group_schedule_parser(self):
        gggg = "ИКБО-08-21"
        page = requests.get("https://www.mirea.ru/schedule/")
        soup = BeautifulSoup(page.text, "html.parser")

        result = soup.find("div", {"class": "rasspisanie"}).\
            find(string="Институт информационных технологий").\
            find_parent("div").find_parent("div").find_all("a", {"class": "uk-link-toggle"})

        course = datetime.datetime.now().year % 100 - int(gggg[-2:])
        for a_tag in result:
            if re.search(r"ИИТ_" + str(course), a_tag['href']):
                table = requests.get(a_tag['href'])
                print(table)

                with open("table.xlsx", "wb") as f:
                    f.write(table.content)

                book = openpyxl.load_workbook("table.xlsx")
                sheet = book.active
                num_cols = sheet.max_column
                num_rows = sheet.max_row

                find_group_col = 0
                for col in range(1, num_cols):
                    if str(sheet.cell(row=2, column=col).value) == gggg:
                        find_group_col = col
                        break

                for row in range(1, num_rows):
                    if sheet.cell(row=row, column=find_group_col).value:
                        print(sheet.cell(row=row, column=find_group_col).value)

    def teacher_schedule_parser(self):
        tttt = "Берков".lower()

        page = requests.get("https://www.mirea.ru/schedule/")
        soup = BeautifulSoup(page.text, "html.parser")

        result = soup.find("div", {"class": "rasspisanie"}). \
            find(string="Институт информационных технологий"). \
            find_parent("div").find_parent("div").find_all("a", {"class": "uk-link-toggle"})

        for a_tag in result:
            table = requests.get(a_tag['href'])

            with open("table.xlsx", "wb") as f:
                f.write(table.content)

            book = openpyxl.load_workbook("table.xlsx")
            sheet = book.active
            num_cols = sheet.max_column
            num_rows = sheet.max_row

            for col in range(1, num_cols):
                if re.search(r"[а-яА-Я]{4}\-\d\d\-\d\d", str(sheet.cell(row=2, column=col).value)):
                    for row in range(4, num_rows):
                        teacher = sheet.cell(row=row, column=col+2).value
                        if teacher and tttt in str(teacher).lower():
                            print(teacher, sheet.cell(row=2, column=col).value)

    # def weather_parser(self):
        


def main():
    with open("file.txt", 'r') as f:
        vk_session = vk_api.VkApi(token=f.readline())

    vk = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)

    vkbot = Bot(vk, long_poll)
    # vkbot.start()
    vkbot.teacher_schedule_parser()


if __name__ == "__main__":
    main()
