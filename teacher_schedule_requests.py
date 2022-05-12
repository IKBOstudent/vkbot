import re
import requests
from bs4 import BeautifulSoup
import openpyxl
import datetime


def make_teacher_schedule_message(teacher, command):
    teacher = teacher.lower()
    print("find", command)

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
                    cell_teacher = sheet.cell(row=row, column=col + 2).value
                    if cell_teacher and teacher in str(cell_teacher).lower():
                        print(cell_teacher, str(sheet.cell(row=2, column=col).value))



