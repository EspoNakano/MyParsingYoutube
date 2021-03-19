# Программа парсит ютуб канал на странице video, забивая в CSV-файл, находящийся в корневой папке скрипта,
# следующие данные: Название, дата публикации, кол-во просмотров, кол-во лайков, кол-во дизлайков,
# продолжительность видео в секундах.

# Иногда в консоли вылетает некритическая ошибка 'Protocol error Target.detachFromTarget: Target closed.'
# Проблема исходит из ошибки в библиотеке websockets.
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from requests_html import HTMLSession
from bs4 import BeautifulSoup as BS
import time
import csv

session = HTMLSession()


def reload_session(get_url):
    global session
    session.close()
    session = HTMLSession()
    response = session.get(get_url)
    response.html.render(sleep=1)
    mash = BS(response.html.html, "html.parser")
    return mash


def get_video_info(get_url):
    mash = reload_session(get_url)
    result = {}
    # Название видео
    if mash.find("h1").text.strip() == '':
        mash = reload_session(get_url)
        result["Название"] = mash.find("h1").text.strip()
    else:
        result["Название"] = mash.find("h1").text.strip()
    # Количество просмотров видео
    if mash.find("span", attrs={"class": "view-count"}) is None:
        mash = reload_session(get_url)
        mash.find("span", attrs={"class": "view-count"})
        result["Просмотров"] = int(''.join([c for c in mash.find("span",
                                                                 attrs={"class": "view-count"}).text if c.isdigit()]))
    else:
        result["Просмотров"] = int(''.join([c for c in mash.find("span",
                                                                 attrs={"class": "view-count"}).text if c.isdigit()]))
    # Дата публикации видео
    result["Дата публикации"] = mash.find("div", {"id": "date"}).text[1:]
    # Длительность видео
    list_dur = []  # Защита от некорректной длительности видео
    for dd in range(3):
        mash = reload_session(get_url)
        list_dur.append(mash.find("span", {"class": "ytp-time-duration"}).text)
    norm_dur = max(list_dur).split(':')  # перевод в секунды
    if len(norm_dur) == 1:
        ans = int(norm_dur[0])
    elif len(norm_dur) == 2:
        ans = int(norm_dur[0]) * 60 + int(norm_dur[1])
    elif len(norm_dur) == 3:
        ans = int(norm_dur[0]) * 60 + int(norm_dur[1]) * 60 + int(norm_dur[2])
    result["Длительность"] = ans
    # Количество лайков и дизлайков
    text_yt_formatted_strings = mash.find_all("yt-formatted-string",
                                              {"id": "text", "class": "ytd-toggle-button-renderer"})
    if text_yt_formatted_strings[0] is None:
        mash = reload_session(get_url)
        text_yt_formatted_strings = mash.find_all("yt-formatted-string",
                                                  {"id": "text", "class": "ytd-toggle-button-renderer"})
        result["Лайков"] = int(
            ''.join([c for c in text_yt_formatted_strings[0].attrs.get("aria-label") if c.isdigit()]))
    elif text_yt_formatted_strings[1] is None:
        mash = reload_session(get_url)
        text_yt_formatted_strings = mash.find_all("yt-formatted-string",
                                                  {"id": "text", "class": "ytd-toggle-button-renderer"})
        result["Дизлайков"] = int(
            ''.join([c for c in text_yt_formatted_strings[0].attrs.get("aria-label") if c.isdigit()]))
    else:
        result["Лайков"] = int(
            ''.join([c for c in text_yt_formatted_strings[0].attrs.get("aria-label") if c.isdigit()]))
        result["Дизлайков"] = int(
            ''.join([c for c in text_yt_formatted_strings[1].attrs.get("aria-label") if c.isdigit()]))

    return result


if __name__ == '__main__':
    print('Количество охваченных видео: 30 * (ваше число + 1)')
    cst_end = input('Введите положительное число или 0: ')
    if not cst_end.isdigit():
        print('Нужно ввести положительное число или 0')
        cst_end = input('Введите положительное число или 0: ')
    site = input('Введите URL или test: ')
    if site == 'test':
        site = "https://www.youtube.com/c/gosha_dudar/videos"

    driver = webdriver.Chrome()
    driver.get(site)
    time.sleep(2)  # если слабый интернет/компьютер, то поставьте 10
    scroll_pause_time = 1  # если слабый интернет/компьютер, то поставьте 3
    cst_end = int(cst_end)

    # Данный цикл не работает на youtube, т.к. там решили выделиться своим личным скроллом, в котором scrollHeight
    # ставится на 0 для текущей позиции скролла по умолчанию.
    # Но цикл работает на zen.yandex (scroll_pause_time ставить на 4) и других сайтах.
    # --------
    # last_height = driver.execute_script("return document.body.scrollHeight")
    # while True:
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(scroll_pause_time)
    #     new_height = driver.execute_script("return document.body.scrollHeight")
    #     if new_height == last_height:
    #         break
    #     last_height = new_height
    # --------

    # замена цикла выше: пролистывание страницы ютуба через имитацию нажатия END на клавиатуре
    # --------
    for i in range(cst_end):  # для охвата 150 видео cst_end = 4
        driver.find_element_by_tag_name('body').send_keys(Keys.END)
        time.sleep(scroll_pause_time)
    # --------

    html = driver.page_source
    soup = BS(html, "html.parser")
    url_list = []  # лист ссылок на видео в выборке
    videos = soup.find_all("ytd-grid-video-renderer", {"class": "style-scope ytd-grid-renderer"})
    for video in videos:
        a = video.find("a", {"id": "video-title"})
        url = "https://www.youtube.com" + a.get("href")
        url_list.append(url)
    driver.close()
    print('Сбор видео завершён. Приступаем к занесению информации о каждом видео в CSV-файл:', end='\n')
    status_bar = [i for i in range(len(url_list))]
    data_list = []
    for i in range(len(url_list)):
        print('Видео ' + str(i + 1) + '/' + str(len(url_list)) + ' | Сбор информации...')
        data = get_video_info(url_list[i])
        data_ready = [data['Название'], data['Просмотров'], data['Дата публикации'], data['Длительность'],
                      data['Лайков'], data['Дизлайков']]
        data_list.append(data_ready)
        with open("data.csv", mode="w", encoding='utf-16') as w_file:
            file_writer = csv.writer(w_file, delimiter=";", lineterminator="\r")
            file_writer.writerow(['Title', 'Views', 'Date Published', 'Duration', 'Like', 'Dislike'])
            for j in range(len(data_list)):
                file_writer.writerow(data_list[j])
        print('Видео ' + str(i + 1) + '/' + str(len(url_list)) + ' | Информация внесена в CSV-файл.')
