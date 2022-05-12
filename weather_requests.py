import json
import requests
import os
from PIL.Image import Image
import datetime

my_api = "4f35276e9892e31276c03a9889e7c3a2"
city_id = "524901"  # moscow
# city_id = "2643743"  # london


def wind_direction(degrees):
    if degrees < 22.5:
        return "С"
    if degrees < 45 + 22.5:
        return "СВ"
    if degrees < 90 + 22.5:
        return "В"
    if degrees < 135 + 22.5:
        return "ЮВ"
    if degrees < 180 + 22.5:
        return "Ю"
    if degrees < 225 + 22.5:
        return "ЮЗ"
    if degrees < 270 + 22.5:
        return "З"
    if degrees < 315 + 22.5:
        return "СЗ"
    return "С"


def wind_strength(speed):
    if speed < 0.5:
        return "штиль"
    if speed < 1.5:
        return "тихий"
    if speed < 3:
        return "легкий"
    if speed < 5:
        return "слабый"
    if speed < 8:
        return "умеренный"
    if speed < 10:
        return "свежий"
    if speed < 14:
        return "сильный"
    if speed < 17:
        return "крепкий"
    if speed < 20:
        return "очень крепкий"
    if speed < 25:
        return "шторм"
    if speed < 33:
        return "сильный шторм"
    return "ураган"


def formatted_weather(description,
                      temperature,
                      feels_like,
                      pressure,
                      humidity,
                      visibility,
                      wind_deg,
                      wind_speed):
    return f"{description}, {round(temperature)}°C" \
           f"\n\nощущается как {round(feels_like)}°C" \
           f"\nдавление {round(pressure * 0.750064)} мм рт. ст." \
           f"\nвлажность {humidity}%" \
           f"\nвидимость {visibility // 1000}км" \
           f"\nветер {wind_direction(wind_deg)}, " \
           f"{wind_strength(wind_speed)}, " \
           f"{round(wind_speed)}м/с"


def make_weather_message(date):
    today = f"{datetime.datetime.now():%Y-%m-%d}"
    tomorrow = f"{(datetime.datetime.now() + datetime.timedelta(days=1)):%Y-%m-%d}"
    after_tom = f"{(datetime.datetime.now() + datetime.timedelta(days=2)):%Y-%m-%d}"
    print(today, tomorrow, after_tom)

    if date == "NOW":
        url = f"https://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={my_api}&units=metric&lang=ru"
    else:
        url = f"https://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={my_api}&units=metric&lang=ru"

    print(url)

    response_weather = requests.get(url)
    filepath = os.path.abspath(os.curdir) + "/tables/weather.json"
    with open(filepath, 'w') as f:
        json.dump(response_weather.json(), f)

    with open(filepath, 'r') as f:
        weather = json.load(f)

    if date == "NOW":
        current_weather = weather
        iconcode = current_weather['weather'][0]['icon']
        iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"
        response_icon = requests.get(iconurl)

        iconpath = os.path.abspath(os.curdir) + "/icons/icon_current_weather.png"
        with open(iconpath, 'wb') as f:
            f.write(response_icon.content)

        message = formatted_weather(current_weather['weather'][0]['description'],
                                    current_weather['main']['temp'],
                                    current_weather['main']['feels_like'],
                                    current_weather['main']['pressure'],
                                    current_weather['main']['humidity'],
                                    current_weather['visibility'],
                                    current_weather['wind']['deg'],
                                    current_weather['wind']['speed'])
        print(message)

    elif date == "TOD":
        pass

    elif date == "TOM":
        i = 0

        time_good = [tomorrow + " 06:00:00",
                     tomorrow + " 12:00:00",
                     tomorrow + " 18:00:00",
                     after_tom + " 00:00:00"]

        result = []
        for current_weather in weather['list']:
            if current_weather['dt_txt'] not in time_good:
                continue

            # print(current_weather)
            iconcode = current_weather['weather'][0]['icon']
            iconurl = f"https://openweathermap.org/img/wn/{iconcode}@2x.png"
            response_icon = requests.get(iconurl)

            iconpath = os.path.abspath(os.curdir) + "/icons/icon_current" + str(i) + ".png"
            i += 1
            with open(iconpath, 'wb') as f:
                f.write(response_icon.content)

            if i == 1:
                message = "УТРО\n"
            elif i == 2:
                message = "ДЕНЬ\n"
            elif i == 3:
                message = "ВЕЧЕР\n"
            else:
                message = "НОЧЬ\n"

            message += formatted_weather(current_weather['weather'][0]['description'],
                                         current_weather['main']['temp'],
                                         current_weather['main']['feels_like'],
                                         current_weather['main']['pressure'],
                                         current_weather['main']['humidity'],
                                         current_weather['visibility'],
                                         current_weather['wind']['deg'],
                                         current_weather['wind']['speed'])
            result.append(message)
            if i == 4:
                break
        print(result)

    else:
        time_good = []
        for i in range(1, 6):
            time_good.append(f"{(datetime.datetime.now() + datetime.timedelta(days=i)):%Y-%m-%d} 03:00:00")
            time_good.append(f"{(datetime.datetime.now() + datetime.timedelta(days=i)):%Y-%m-%d} 15:00:00")
        print(time_good)

        result = []
        for current_weather in weather['list']:
            if current_weather['dt_txt'] not in time_good:
                continue

            is_day = current_weather['dt_txt'][11:] == "15:00:00"
            if is_day:
                message = "ДЕНЬ "
            else:
                message = "НОЧЬ "

            message += f"{round(current_weather['main']['temp'])}°C"

            result.append(message)

        for i in range(0, len(result) - 1, 2):
            result[i], result[i+1] = result[i+1], result[i]
        print(result)
