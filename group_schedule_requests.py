import re
import requests
from bs4 import BeautifulSoup
import openpyxl
import datetime


def make_group_schedule_message(group, command):
    group = group.upper()
    print("find", command)

    page = requests.get("https://www.mirea.ru/schedule/")
    soup = BeautifulSoup(page.text, "html.parser")

    result = soup.find("div", {"class": "rasspisanie"}). \
        find(string="Институт информационных технологий"). \
        find_parent("div").find_parent("div").find_all("a", {"class": "uk-link-toggle"})

    course = datetime.datetime.now().year % 100 - int(group[-2:])
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
                if str(sheet.cell(row=2, column=col).value) == group:
                    find_group_col = col
                    break

            for row in range(1, num_rows):
                if sheet.cell(row=row, column=find_group_col).value:
                    print(sheet.cell(row=row, column=find_group_col).value)



