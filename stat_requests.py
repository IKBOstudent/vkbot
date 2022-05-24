import json
import requests
import os
from bs4 import BeautifulSoup
from PIL import Image
import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter




def make_stat(link):
    url = "https://coronavirusstat.ru" + link
    need_dynamics = "russia" in link
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        # print(page)

        result = {}
        stat = soup.find("div", {"class": "row justify-content-md-center"})
        for elem in stat.find_all("div", {"class": "h2"}):
            total = elem.text
            name = elem["title"].split()[-1]
            result.update({name: {"total": "", "today": ""}})
            today = elem.find_parent().find("span", text="(сегодня)").find_parent().find("span").text
            result[name]["total"] = total
            result[name]["today"] = today

        message = f'По состоянию на {stat.find_parent().find("h6").find("strong").text}'
        for i in result.keys():
            message += f'\n{i}: {result[i]["total"]} ({result[i]["today"]} за сегодня)'

        print(message)

        if need_dynamics:
            dates = []
            dynamics = {"active": [],
                        "recovered": [],
                        "deaths": []}
            table = soup.find("table", {"class": "table table-bordered small"}).find("tbody")
            ci = 0
            for i in table.find_all("tr"):
                if ci == 0:
                    ci += 1
                    continue
                if ci == 11:
                    break

                date = i.find("th").text

                cc = 0
                dates.append(date)
                for count in i.find_all("td"):
                    if cc == 0:
                        dynamics["active"].append(int(count.text.split()[0]))
                    elif cc == 1:
                        dynamics["recovered"].append(int(count.text.split()[0]))
                    elif cc == 2:
                        dynamics["deaths"].append(int(count.text.split()[0]))
                    elif cc == 3:
                        break
                    cc += 1

                ci += 1

            print(dynamics)

            x = [datetime.datetime.strptime(i, '%d.%m.%Y').date() for i in dates]

            dataset1 = np.array(dynamics["active"])
            dataset2 = np.array(dynamics["recovered"])
            dataset3 = np.array(dynamics["deaths"])

            plt.bar(x, dataset1, color='tab:blue')
            plt.bar(x, dataset2, bottom=dataset1, color='tab:orange')
            plt.bar(x, dataset3, bottom=dataset1 + dataset2, color='tab:green')
            plt.legend(["Активных", "Вылечено", "Умерло"])
            plt.title("Статистика за последние 10 дней")

            y_formatter = ScalarFormatter(useOffset=False)
            y_formatter.set_scientific(False)
            plt.gca().yaxis.set_major_formatter(y_formatter)
            plt.gcf().autofmt_xdate()

            plt.savefig('stat.png')

        return message
    except Exception:
        print(f"something wrong with {url}")
        return "BAD"









