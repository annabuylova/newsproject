import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import altair as alt
import pydeck as pdk

st.title("Статистика по новостям")
st.markdown(
"""
### Как сильно коррелирует повестка наших новостей с зарубежными интересами? 

Код собирает информацию об актуальных новостей, выбирает ключевые слова и показывает, насколько они популярны среди российских пользователей и иностранных. Также анализируется популярность конкретных тем и то, насколько долго они остаются в пределах основной повестки.
""")

display_code = st.radio("Показывать ли на странице код?", ("Да", "Нет"))

'Для начала соберём текущие новости. Для этого воспользуемся Яндекс.Новостями и BeautifulSoup.'

if display_code == "Да":
    with st.echo():
            r = requests.get('https://yandex.ru/news/')
            if r.ok:
                obj = BeautifulSoup(r.text, features="html")
                news = []
                for heading in obj.findAll("h2", class_="story__title"):
                    news.append(heading.string)
else:
    r = requests.get('https://yandex.ru/news/')
    if r.ok:
        obj = BeautifulSoup(r.text, features="html")
        news = []
        for heading in obj.findAll("h2", class_="story__title"):
            news.append(heading.string)

'Дата-фрейм новостей выглядит приблизительно так:',news[:5]
#### Найдём самую популярную тему.

#%% md
'Начнём с простого: уберем слова без особой смысловой нагрузки (союзы, предлоги). Сперва разберемся с союзами. Заходим на Википедию (https://ru.wikipedia.org/wiki/Союз_(часть_речи)). Список кажется достаточно полным, но на странице есть много информации, которая нам не нужна. Вытащим текст и попытаемся отчистить его.'
if display_code == "Да":
    with st.echo():
        r = requests.get("https://ru.wikipedia.org/wiki/Союз_(часть_речи)")
        if r.ok:
            obj = BeautifulSoup(r.text, features="xml")
            all_text = []
            for heading in obj.findAll("ul"):
                for li in heading.findAll("li"):
                    all_text.append(li.text)
        else:
            print("Проблема с тегами")
else:
    r = requests.get("https://ru.wikipedia.org/wiki/Союз_(часть_речи)")
    if r.ok:
        obj = BeautifulSoup(r.text, features="xml")
        all_text = []
        for heading in obj.findAll("ul"):
            for li in heading.findAll("li"):
                all_text.append(li.text)
    else:
        print("Проблема с тегами")
'Информация из кода страницы вики', all_text[25:30]
'Заметим, что нужные нам союзы записаны в скобках. Воспользуемся регулярными выражениями, чтобы убрать лишнее'
if display_code == "Да":
    with st.echo():
        import re
        text = ''
        for i in all_text:
            text += ' '.join(re.findall('\(.*\)', i))  # содержимое всех скобок объединили в список
        souzy = re.findall('[а-яА-ЯёЁ]+', text)
        souzy = souzy[:-6]  # чистим случайно попавшие значения (видимо, они тоже были в скобках)
        souzy = list(set(souzy))  # избавляемся от повторений
else:
    import re

    text = ''
    for i in all_text:
        text += ' '.join(re.findall('\(.*\)', i))  # содержимое всех скобок объединили в список
    souzy = re.findall('[а-яА-ЯёЁ]+', text)
    souzy = souzy[:-6]  # чистим случайно попавшие значения (видимо, они тоже были в скобках)
    souzy = list(set(souzy))  # избавляемся от повторений

'Получили спискок союзов (приведём здесь часть)', souzy[:5]

'Некоторые сложные союзы ("как будто", "несмотря на") распались, но это не важно: части союзов сами по себе всё так же не несут смысловой нагрузки и их надо удалить.'
'Теперь рассмотрим предлоги. Возьмём их из вики (https://ru.wikipedia.org/wiki/Предлог). Нам повезло, здесь их можно удобно скопировать.'
predlogi = "в, без, до, из, к, на, по, о, от, перед, при, через, с, у, за, над, об, под, про, для, из-за".split(', ')
'Предлоги (также приведём здесь часть)', predlogi[:5]
'Объединим предлоги и союзы в список. Переведём список новостей в строку и отчистим её от служебных частей речи.'
'Если тексты в примере не изменились, стоит изменить диапазоны: возможно, просто в день проверки заголовки первых новостей вышли без служебных частей речи.'
if display_code == "Да":
    with st.echo():
        sluj_words = list(set(souzy + predlogi))

        news_str = ' '.join(news)
        news_nosluj = ' '.join(list(filter(lambda x: x.lower() not in sluj_words, news_str.split())))
else:
    sluj_words = list(set(souzy + predlogi))
    news_str = ' '.join(news)
    news_nosluj = ' '.join(list(filter(lambda x: x.lower() not in sluj_words, news_str.split())))

'### До чистки:'
news_str[:300]
'### После чистки: '
news_nosluj[:300]

'Знаки тоже не несут смысловой нагрузки. Убирем и их. Для этого скачиванием библиотеку string. Аналогично прошлому пункту, если тексты в примере не изменились, стоит изменить диапазоны.'
if display_code == "Да":
    with st.echo():
        import string

        punctuation = dict((ord(char), None) for char in string.punctuation)
        punctuation[ord("«")]=""
        punctuation[ord("»")]=""

        news_clear = news_nosluj.translate(punctuation) # убираем знаки пунктуации
else:
    import string
    punctuation = dict((ord(char), None) for char in string.punctuation)
    punctuation[ord("«")] = ""
    punctuation[ord("»")] = ""
    news_clear = news_nosluj.translate(punctuation)  # убираем знаки пунктуации

'### До чистки:'
news_nosluj[:300]
'### После чистки:'
news_clear[:300]

'Мы ищем не просто самые популярные слова, но самые популярные темы. Они могут быть выражены разными фразами, но ключевые слова с большой вероятностью будут одинаковыми. Чтобы не упустить какие-то упоминания из-за разных форм, приведём все слова к начальной форме. Сделаем это с помощью pymorphy. Скачаем библиотеки.'
if display_code == "Да":
    with st.echo():
        import pymorphy2
        morph = pymorphy2.MorphAnalyzer()
        news_words = []
        for word in news_clear.split():
            news_words.append(morph.parse(word)[0].normal_form)
        for word in news_words:
            p = morph.parse(word)[0]
            if p.tag.POS == "VERB" or p.tag.POS == "INFN":
                news_words.remove(word)
else:
    import pymorphy2

    morph = pymorphy2.MorphAnalyzer()
    news_words = []
    for word in news_clear.split():
        news_words.append(morph.parse(word)[0].normal_form)
    for word in news_words:
        p = morph.parse(word)[0]
        if p.tag.POS == "VERB" or p.tag.POS == "INFN":
            news_words.remove(word)

'Теперь имеем список ключевых слов в новостях', news_words[:5]
'Найдём самые популярные слова с помощью счётчика.'
if display_code == "Да":
    with st.echo():
        from datetime import datetime
        from collections import Counter
        c = Counter(news_words)
        commons = c.most_common()
        df = pd.DataFrame(commons, columns=['word', 'score'])
        df['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
else:
    from datetime import datetime
    from collections import Counter
    c = Counter(news_words)
    commons = c.most_common()
    df = pd.DataFrame(commons, columns=['word', 'score'])
    df['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
df[:5]

'Запишем полученную информацию в отдельный файл.'
if display_code == "Да":
    with st.echo():
        with open('C:/NewsProject/data/News_data','a',encoding='utf-8') as f:
           df.to_csv(f, header=False)
else:
    with open('C:/Users/асер/Documents/News_data', 'a', encoding='utf-8') as f:
        df.to_csv(f, header=False)
'За время работы над проектом мне удалось собрать базу за несколько дней. '
#%%
if display_code == "Да":
    with st.echo():
        df = pd.read_csv('C:/Users/асер/Documents/News_data',encoding="cp1251", sep=',')
        df = df[['word','score']]
else:
    df = pd.read_csv('C:/Users/асер/News_data', encoding="utf-8", sep=',')
    df = df[['word', 'score']]
df

'Некоторые слова повторялись изо дня в день в разных новостях ("коронавирус", "ефремов"), поэтому, чтобы оценить их популярность за рассматриваемый период нужно объединить значения по запросу в разные дни в одно. Для этого применим groupby по словам и соберём список из кортежей вида (слово, суммарное число показов за рассматриваемый период).'
'Часть слов встречалась очень часто, но привязки к конкретной новости не имела ("Россия", "США", "объявить", "рассказать"). Исключим их. Также, учитывая большой объём данных, оставим среди "популярных" тем те, которые упоминались больше 10 раз. Сохраним всё на будущее в отдельный файл.'
if display_code == "Да":
    with st.echo():
        pairs = []
        for group in df.groupby('word'):
            pairs.append((group[0], group[1].loc[df['word'] == group[0],'score'].sum()))
        pairs = sorted(pairs,key=lambda x: x[1], reverse=True)
        for pair in pairs:
            p = morph.parse(pair[0])[0]
            if p.tag.POS == "VERB" or p.tag.POS == "INFN":
                pairs.remove(pair)
        clean_pairs = [x for x in pairs if x[0] not in ['россия','российский','сша','москва',
                                                        'один','два','три','год']]
        clean_pairs = [x for x in clean_pairs if x[1] > 10]
        word_clean = []
        score_clean = []
        for x,y in clean_pairs:
            word_clean.append(x)
            score_clean.append(y)
        clean_pairs_df= pd.DataFrame([word_clean,score_clean]).T
        clean_pairs_df.columns = ['word','score']
        clean_pairs_df.to_csv("Clean_pairs")
else:
    pairs = []
    for group in df.groupby('word'):
        pairs.append((group[0], group[1].loc[df['word'] == group[0], 'score'].sum()))
    pairs = sorted(pairs, key=lambda x: x[1], reverse=True)
    for pair in pairs:
        p = morph.parse(pair[0])[0]
        if p.tag.POS == "VERB" or p.tag.POS == "INFN":
            pairs.remove(pair)
    clean_pairs = [x for x in pairs if x[0] not in ['россия', 'российский', 'сша', 'москва',
                                                    'один', 'два', 'три', 'год']]
    clean_pairs = [x for x in clean_pairs if x[1] > 10]
    word_clean = []
    score_clean = []
    for x, y in clean_pairs:
        word_clean.append(x)
        score_clean.append(y)
    clean_pairs_df = pd.DataFrame([word_clean, score_clean]).T
    clean_pairs_df.columns = ['word', 'score']
    clean_pairs_df.to_csv("Clean_pairs")
clean_pairs_df

'Отправим запрос в WordStat от Яндекса с помощью Selenium. Убедитесь, что у вас скачан FireFox и вы вышли из своего аккаунта в Яндекс в том же браузере.'
if display_code == "Да":
    with st.echo():
        from selenium import webdriver
        from selenium.webdriver import ActionChains
        import time

        top_res = clean_pairs[0][0]

        # открыли сайт
        driver = webdriver.Firefox(executable_path='C:\geckodriver.exe')
        driver.implicitly_wait(10)
        driver.get('https://wordstat.yandex.ru/')

        time.sleep(3)

        button = driver.find_element_by_xpath('//li[2]/label/input')
        ActionChains(driver).move_to_element(button).click().perform()

        time.sleep(3)

        # залогинились
        username = driver.find_element_by_id("b-domik_popup-username")
        username.clear()
        username.send_keys('nice.stiven')
        password = driver.find_element_by_id("b-domik_popup-password")
        password.clear()
        password.send_keys('stiven')
        button = driver.find_element_by_xpath('//div[5]/span[1]/span')
        ActionChains(driver).move_to_element(button).click().perform()

        def ask_wordstat(query):
            time.sleep(3)

            # заполнили форму
            content = driver.find_element_by_css_selector('.b-form-input__input')
            content.clear()
            content.send_keys(query)

            # отправили форму
            button = driver.find_element_by_css_selector('.b-search__button')
            ActionChains(driver).move_to_element(button).click().perform()

            time.sleep(5)

            # перешли на вкладку регионов
            button = driver.find_element_by_css_selector('.b-form-radio__button_type_regions')
            ActionChains(driver).move_to_element(button).click().perform()

        ask_wordstat(top_res)
else:
    from selenium import webdriver
    from selenium.webdriver import ActionChains
    import time
    top_res = clean_pairs[0][0]
    # открыли сайт
    driver = webdriver.Firefox(executable_path='C:\geckodriver.exe')
    driver.implicitly_wait(10)
    driver.get('https://wordstat.yandex.ru/')
    time.sleep(3)
    button = driver.find_element_by_xpath('//li[2]/label/input')
    ActionChains(driver).move_to_element(button).click().perform()
    time.sleep(3)
    # залогинились
    username = driver.find_element_by_id("b-domik_popup-username")
    username.clear()
    username.send_keys('nice.stiven')
    password = driver.find_element_by_id("b-domik_popup-password")
    password.clear()
    password.send_keys('stiven')
    button = driver.find_element_by_xpath('//div[5]/span[1]/span')
    ActionChains(driver).move_to_element(button).click().perform()

    def ask_wordstat(query):
        time.sleep(3)
        # заполнили форму
        content = driver.find_element_by_css_selector('.b-form-input__input')
        content.clear()
        content.send_keys(query)
        # отправили форму
        button = driver.find_element_by_css_selector('.b-search__button')
        ActionChains(driver).move_to_element(button).click().perform()
        time.sleep(5)
        # перешли на вкладку регионов
        button = driver.find_element_by_css_selector('.b-form-radio__button_type_regions')
        ActionChains(driver).move_to_element(button).click().perform()
    ask_wordstat(top_res)

'На данный момент у нас должна быть открыта страница с данными от Яндекс. Если это не так, проверьте условия из прошлого комментария. Повторите код ещё раз. Если данные всё ещё не появились, попробуйте изменить аргумент в time.sleep(x) на больший - это даст странице больше времени на прогрузку.'
'Соберем информацию из таблицы. Каждая строка таблицы задается тегом "tr", начиная с 15 и заканчивая тегом с текстом "Ваш товар ищут? Дайте контекстное объявление!...". каждый столбец внутри строки - тегом "td" с 0 по 2.'
if display_code == "Да":
    with st.echo():
        time.sleep(3)
        table = driver.find_elements_by_tag_name('tr')
        print (table[15].find_elements_by_tag_name('td')[0].text, ' ', table[15].find_elements_by_tag_name('td')[1].text, ' ', table[15].find_elements_by_tag_name('td')[1].text)
else:
    time.sleep(3)
    table = driver.find_elements_by_tag_name('tr')
'Получаем информацию: Регион - ', table[15].find_elements_by_tag_name('td')[0].text, ', Показов в месяц - ', table[15].find_elements_by_tag_name('td')[1].text, ', Региональная популярность - ', table[15].find_elements_by_tag_name('td')[1].text


'Таким образом, нам нужен цикл, который будет считывать теги для каждой строки (региона) вплоть до строки с "вашим товаром". Для визуализации возьмём 100 регионов с наивысшими показателями по региональной популярности. Сортировка именно по этому показателю нивелирует различия в популярности Яндекса в разных регионах и отражает популярность запроса в конкретном регионе относительно среднего числа запросов в том же регионе.'
if display_code == "Да":
    with st.echo():
        def get_info_table():
            table = driver.find_elements_by_tag_name('tr')
            word = []
            regions = []
            queries = []
            reg_pop = []
            for tr in table[15:]:
                if tr.text == 'Ваш товар ищут? Дайте контекстное объявление!\nЕсли товары и услуги ищут, значит, на них есть спрос. Пользуйтесь этим. Разместите объявление в Яндекс.Директе, а мы покажем его людям, которые ищут то, что вы продаёте.\nПодробнее о Яндекс.Директе\nМинимальный заказ - всего 1000 рублей':
                    break
                td = tr.find_elements_by_tag_name('td')
                regions.append(td[0].text)
                queries.append(td[1].text)
                reg_pop.append(td[2].text)
                word.append(top_res)
            wordstat = pd.DataFrame([regions,
                                     queries,
                                     reg_pop,
                                     word]).T
            return wordstat

        wordstat = get_info_table()
        wordstat[1] = wordstat[1].replace(' ', '')
        wordstat[2] = wordstat[2].replace(' ', '')
        wordstat[2] = wordstat[2].str[:-1]
        wordstat[2] = wordstat[2].astype(float)
        wordstat = wordstat.sort_values(2, ascending=False).reset_index()  # сортируем по показателю региональной популярности
        del wordstat['index']
        wordstat = wordstat[:100]
        wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
else:
    def get_info_table():
        table = driver.find_elements_by_tag_name('tr')
        word = []
        regions = []
        queries = []
        reg_pop = []
        for tr in table[15:]:
            if tr.text == 'Ваш товар ищут? Дайте контекстное объявление!\nЕсли товары и услуги ищут, значит, на них есть спрос. Пользуйтесь этим. Разместите объявление в Яндекс.Директе, а мы покажем его людям, которые ищут то, что вы продаёте.\nПодробнее о Яндекс.Директе\nМинимальный заказ - всего 1000 рублей':
                break
            td = tr.find_elements_by_tag_name('td')
            regions.append(td[0].text)
            queries.append(td[1].text)
            reg_pop.append(td[2].text)
            word.append(top_res)
        wordstat = pd.DataFrame([regions,
                                 queries,
                                 reg_pop,
                                 word]).T
        return wordstat


    wordstat = get_info_table()
    wordstat[1] = wordstat[1].replace(' ', '')
    wordstat[2] = wordstat[2].replace(' ', '')
    wordstat[2] = wordstat[2].str[:-1]
    wordstat[2] = wordstat[2].astype(float)
    wordstat = wordstat.sort_values(2,
                                    ascending=False).reset_index()  # сортируем по показателю региональной популярности
    del wordstat['index']
    wordstat = wordstat[:100]
    wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
wordstat
'Изобразим полученную информацию на карте. Для этого найдём координаты регионов. '
'В отдельной вкладке должна открыться графика. Если этого не произошло, проверьте установленные пакеты.'
if display_code == "Да":
    with st.echo():
        from geopy.geocoders import Nominatim
        import plotly
        import plotly.graph_objs as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        import numpy as np

        wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
        geolocator = Nominatim(user_agent="Stiven")

        def get_coords(address, geolocator=geolocator):
            if geolocator is None:
                geolocator = Nominatim(user_agent="Stiven")
            ret = geolocator.geocode(address,
                                     timeout=60
                                     )
            if ret is None:
                return None
            return ret.latitude, ret.longitude

        wordstat['Coordinates'] = wordstat['Region'].map(get_coords)
        wordstat = wordstat.dropna(subset=['Coordinates'])
        wordstat[["Latitude", "Longitude"]] = pd.DataFrame(wordstat['Coordinates'].tolist(),
                                                           columns=["lat", "long"],
                                                           index=wordstat.index)
        wordstat = wordstat.dropna()
        wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word', 'Coordinates', 'Latitude', 'Longitude']

        wordstat['Regional pop.'] = wordstat['Regional pop.'].replace(r'\s+', '', regex=True).astype(int)

        wordstat['Displays'] = wordstat['Displays'].replace(r'\s+', '', regex=True).astype(int)
        min_val_size = wordstat['Displays'].min()

        def to_int_size(value):
            try:
                return np.log10(int(value) - min_val_size + 10)
            except:
                return np.log10(int(value.split('[')[0]))

        min_val_col = wordstat['Regional pop.'].min()
        def to_int_color(value):
            try:
                return np.log10(int(value) - min_val_col + 10)
            except:
                return np.log10(int(value.split('[')[0]))

        fig = go.Figure(go.Scattermapbox(lat=wordstat['Latitude'],
                                         lon=wordstat['Longitude'],
                                         text=wordstat['Region'],
                                         marker=dict(
                                             color=10*wordstat['Regional pop.'].map(to_int_color),
                                             size=wordstat['Displays'].map(to_int_size),
                                             sizeref=0.5,
                                             showscale=True
                                         ),
                                         ))
        map_center = go.layout.mapbox.Center(lat=53,
                                             lon=70)
        fig.update_layout(mapbox_style="open-street-map",
                          mapbox=dict(center=map_center, zoom=1.5))
        fig.show()
else:
    from geopy.geocoders import Nominatim
    import plotly
    import plotly.graph_objs as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import numpy as np

    wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
    geolocator = Nominatim(user_agent="Stiven")
    def get_coords(address, geolocator=geolocator):
        if geolocator is None:
            geolocator = Nominatim(user_agent="Stiven")
        ret = geolocator.geocode(address,
                                 timeout=60
                                 )
        if ret is None:
            return None
        return ret.latitude, ret.longitude


    wordstat['Coordinates'] = wordstat['Region'].map(get_coords)
    wordstat = wordstat.dropna(subset=['Coordinates'])
    wordstat[["Latitude", "Longitude"]] = pd.DataFrame(wordstat['Coordinates'].tolist(),
                                                       columns=["lat", "long"],
                                                       index=wordstat.index)
    wordstat = wordstat.dropna()
    wordstat.columns = ['Region', 'Displays', 'Regional pop.', 'Word', 'Coordinates', 'Latitude', 'Longitude']
    wordstat['Regional pop.'] = wordstat['Regional pop.'].replace(r'\s+', '', regex=True).astype(int)
    wordstat['Displays'] = wordstat['Displays'].replace(r'\s+', '', regex=True).astype(int)
    min_val_size = wordstat['Displays'].min()
    def to_int_size(value):
        try:
            return np.log10(int(value) - min_val_size + 10)
        except:
            return np.log10(int(value.split('[')[0]))


    min_val_col = wordstat['Regional pop.'].min()
    def to_int_color(value):
        try:
            return np.log10(int(value) - min_val_col + 10)
        except:
            return np.log10(int(value.split('[')[0]))
    fig = go.Figure(go.Scattermapbox(lat=wordstat['Latitude'],
                                     lon=wordstat['Longitude'],
                                     text=wordstat['Region'],
                                     marker=dict(
                                         color=10*wordstat['Regional pop.'].map(to_int_color),
                                         size=wordstat['Displays'].map(to_int_size),
                                         sizeref=0.5,
                                         showscale=True
                                     ),
                                     ))
    map_center = go.layout.mapbox.Center(lat=53,
                                         lon=70)
    fig.update_layout(mapbox_style="open-street-map",
                      mapbox=dict(center=map_center, zoom=1.5))
    fig.show()
display_code_image = st.radio("В отдельном окне появилась графика?", ("Да", "Нет"))
if display_code_image == "Нет":
    st.write('С помощью кода строится интерактивная карта. В приложении скрин графики для запроса "коронавирус на 16.06.')
    if display_code == "Да":
        with st.echo():
            from PIL import Image, ImageDraw
            image = Image.open('C:/Users/асер/Desktop/Map.jpg') #Открываем изображение.
            st.image(image)
    else:
        from PIL import Image, ImageDraw
        image = Image.open('C:/Users/асер/Desktop/Map.jpg') #Открываем изображение.
        st.image(image)
st.markdown(
"""
#### Насколько популярна эта тема за рубежом? 
""")
'Проверим это, переводя запрос на английский и затем работая по тому же алгоритму. Для перевода воспользумся API Яндекс.Перводчика '
'API взят отсюда (https://www.cyberforum.ru/python-beginners/thread2410879.html).'
if display_code == "Да":
    with st.echo():
        import json
        def translate_query(query):
            url = 'https://translate.yandex.net/api/v1.5/tr.json/translate?'
            key = 'trnsl.1.1.20190227T075339Z.1b02a9ab6d4a47cc.f37d50831b51374ee600fd6aa0259419fd7ecd97'
            r = requests.post(url, data={'key': key, 'text': query, 'lang': 'ru-en'})
            return json.loads(r.text)['text'][0]
        translated_query = translate_query(top_res)
        st.write('Слово \"', top_res, '\" на английском - \"' + translated_query + '\".')
else:
    import json
    def translate_query(query):
        url = 'https://translate.yandex.net/api/v1.5/tr.json/translate?'
        key = 'trnsl.1.1.20190227T075339Z.1b02a9ab6d4a47cc.f37d50831b51374ee600fd6aa0259419fd7ecd97'
        r = requests.post(url, data={'key': key, 'text': query, 'lang': 'ru-en'})
        return json.loads(r.text)['text'][0]
    translated_query = translate_query(top_res)
    st.write('Слово \"', top_res, '\" на английском - \"' + translated_query + '\".')

display_code_tr = st.radio("Перевод появился?", ("Да", "Нет"))
if display_code_tr == "Нет":
    st.wrire('Так как перевод осуществляется через API с общим доступом, то в конкретный день может возникнуть проблема превышения лимита запросов. Если в день проверки произошло именно это, можно воспользоваться следующим кодом (а по возможности перенести проверку на следующий день')
    if display_code == "Да":
        with st.echo():
            driver.get('https://translate.yandex.ru/')
            time.sleep(2)
            inn = driver.find_element_by_xpath('//*[@id="textarea"]')
            inn.clear()
            inn.send_keys(top_res)
            translation = driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div[2]/div/pre/span/span').text
            driver.get('https://wordstat.yandex.ru/')
            time.sleep(2)
            button = driver.find_element_by_xpath('//li[2]/label/input')
            ActionChains(driver).move_to_element(button).click().perform()
            time.sleep(2)
    else:
        driver.get('https://translate.yandex.ru/')
        time.sleep(2)
        inn = driver.find_element_by_xpath('//*[@id="textarea"]')
        inn.clear()
        inn.send_keys(top_res)
        translated_query = driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[2]/div[2]/div/pre/span/span').text
        driver.get('https://wordstat.yandex.ru/')
        time.sleep(2)
        button = driver.find_element_by_xpath('//li[2]/label/input')
        ActionChains(driver).move_to_element(button).click().perform()
        time.sleep(2)
    st.write('Слово \"', top_res, '\" на английском - \"' + translated_query + '\".')
'Здесь мы тоже используем статистику Яндекса. Чтобы нивелировать различия в популярности Яндекса  в разных странах также стоит рассматривать не число запросов (диаметр точек), а их региональную популярность (цвет). Это относительный показатель, отражающий, насколько тема интересна в конкретный момент в конкретном регионе относительно средней частоты этого запроса.'

if display_code == "Да":
    with st.echo():
        ask_wordstat(translated_query)
        time.sleep(5)

        wordstat_eng = get_info_table()
        wordstat_eng['Translated'] = [translated_query] * len(wordstat_eng[0])
        wordstat_eng['Word'] = [top_res] * len(wordstat_eng[0])

        wordstat_eng[1] = wordstat_eng[1].str.replace(' ', '')
        wordstat_eng[1] = wordstat_eng[1].astype(float)
        wordstat_eng[2] = wordstat_eng[2].str[:-1]
        wordstat_eng[2] = wordstat_eng[2].str.replace(' ', '')
        wordstat_eng[2] = wordstat_eng[2].astype(float)
        wordstat_eng = wordstat_eng.sort_values(2, ascending=False).reset_index()
        del wordstat_eng['index']
        wordstat_eng = wordstat_eng[:100]

        wordstat_eng['Coordinates'] = wordstat_eng[0].map(get_coords)
        wordstat_eng = wordstat_eng.dropna()
        wordstat_eng[["Latitude", "Longitude"]] = pd.DataFrame(wordstat_eng['Coordinates'].tolist(),
                                                               columns=["lat", "long"],
                                                               index=wordstat_eng.index)
        wordstat_eng = wordstat_eng.dropna()

        min_val_col = wordstat_eng[2].min()
        min_val_size = wordstat_eng[1].min()

        fig = go.Figure(go.Scattermapbox(lat=wordstat_eng['Latitude'],
                                         lon=wordstat_eng['Longitude'],
                                         text=wordstat_eng[0],
                                         marker=dict(color=10 * wordstat_eng[2].map(to_int_color),
                                                     size=wordstat_eng[1].map(to_int_size),
                                                     sizeref=0.5,
                                                     showscale=True
                                                     ),
                                         ))
        map_center = go.layout.mapbox.Center(lat=53,
                                             lon=70)
        fig.update_layout(mapbox_style="open-street-map",
                          mapbox=dict(center=map_center, zoom=1.5))
        fig.show()
else:
    ask_wordstat(translated_query)

    time.sleep(5)

    wordstat_eng = get_info_table()
    wordstat_eng['Translated'] = [translated_query] * len(wordstat_eng[0])
    wordstat_eng['Word'] = [top_res] * len(wordstat_eng[0])

    wordstat_eng[1] = wordstat_eng[1].str.replace(' ', '')
    wordstat_eng[1] = wordstat_eng[1].astype(float)
    wordstat_eng[2] = wordstat_eng[2].str[:-1]
    wordstat_eng[2] = wordstat_eng[2].str.replace(' ', '')
    wordstat_eng[2] = wordstat_eng[2].astype(float)
    wordstat_eng = wordstat_eng.sort_values(2, ascending=False).reset_index()
    del wordstat_eng['index']
    wordstat_eng = wordstat_eng[:100]

    wordstat_eng['Coordinates'] = wordstat_eng[0].map(get_coords)
    wordstat_eng = wordstat_eng.dropna()
    wordstat_eng[["Latitude", "Longitude"]] = pd.DataFrame(wordstat_eng['Coordinates'].tolist(),
                                                           columns=["lat", "long"],
                                                           index=wordstat_eng.index)
    wordstat_eng = wordstat_eng.dropna()

    min_val_col = wordstat_eng[2].min()
    min_val_size = wordstat_eng[1].min()

    fig = go.Figure(go.Scattermapbox(lat=wordstat_eng['Latitude'],
                                     lon=wordstat_eng['Longitude'],
                                     text=wordstat_eng[0],
                                     marker=dict(color=10 * wordstat_eng[2].map(to_int_color),
                                                 size=wordstat_eng[1].map(to_int_size),
                                                 sizeref=0.5,
                                                 showscale=True
                                                 ),
                                     ))
    map_center = go.layout.mapbox.Center(lat=53,
                                         lon=70)
    fig.update_layout(mapbox_style="open-street-map",
                      mapbox=dict(center=map_center, zoom=1.5))
    fig.show()

'Сейчас мы рассмотрели популярность 1 топ-запроса. Соберём информацию по всем запросам из топ ключевых слов и объединим их в датафрейм'
'Парсинг может заняться несколько часов, поэтому в приложениях можно найти искомый датафрейм с информацией на 16 июня (при желании получить более актуальный можно использовать код).'
display_code_3 = st.radio("Обратиться к уже готовому датафрейму?", ("Да, меня устраивает df из приложения", "Нет, хочу проверить работу кода и получить df, актуальный на день проверки"))
if display_code_3 == "Да, хочу проверить работу кода и получить df, актуальный на день проверки":
    if display_code == "Нет, хочу проверить работу кода и получить df, актуальный на день проверки":
        st.write('Напоминаю, что сбор данных может занять несколько часов. Код здесь тот же, что и в работе с одним запросом, но повторенный для всего списка clean_pairs')
        with st.echo():
            wordstat_full = wordstat[['Region', 'Displays', 'Regional pop.', 'Word']]
            for pair in clean_pairs[1:]:
                ask_wordstat(pair[0])
                new = get_info_table()
                new.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
                wordstat_full = pd.concat([wordstat_full, new])

            wordstat_full[1] = wordstat_full[1].str.replace(' ', '')
            wordstat_full[1] = wordstat_full[1].astype(float)
            wordstat_full[2] = wordstat_full[2].str[:-1]
            wordstat_full[2] = wordstat_full[2].str.replace(' ', '')
            wordstat_full[2] = wordstat_full[2].astype(float)
            wordstat_full.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
            wordstat_full.to_csv("Wordstat_full")
    else:
        st.write('Напоминаю, что сбор данных может занять несколько часов. Код здесь тот же, что и в работе с одним запросом, но повторенный для всего списка clean_pairs')
        wordstat_full = wordstat[['Region', 'Displays', 'Regional pop.', 'Word']]
        for pair in clean_pairs[1:]:
            ask_wordstat(pair[0])
            new = get_info_table()
            new.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
            wordstat_full = pd.concat([wordstat_full, new])

        wordstat_full[1] = wordstat_full[1].str.replace(' ', '')
        wordstat_full[1] = wordstat_full[1].astype(float)
        wordstat_full[2] = wordstat_full[2].str[:-1]
        wordstat_full[2] = wordstat_full[2].str.replace(' ', '')
        wordstat_full[2] = wordstat_full[2].astype(float)
        wordstat_full.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
        wordstat_full.to_csv("Wordstat_full")
else:
    if display_code == "Да":
        with st.echo():
            wordstat_full = pd.read_csv('C:/Users/асер/Wordstat_full',encoding='utf-8')
    else:
        wordstat_full = pd.read_csv('C:/Users/асер/Wordstat_full', encoding='utf-8')
wordstat_full
'Аналогично для английского датафрейма.'
if display_code_3 == "Нет, хочу проверить работу кода и получить df, актуальный на день проверки":
    display_code_eng_3 = st.radio("Обратиться к уже готовому английскому датафрейму?", ("Да, меня устраивает df из приложения","Нет, хочу проверить работу кода и получить df, актуальный на день проверки"))
    if display_code_eng_3 == "Нет, хочу проверить работу кода и получить df, актуальный на день проверки":
        if display_code == "Да":
                with st.echo():
                    import json
                    wordstat_eng_full = wordstat_eng[['Region', 'Displays', 'Regional pop.', 'Word']]
                    for pair in clean_pairs:
                        translated_query = translate_query(pair[0])
                        ask_wordstat(translated_query)
                        new = get_info_table()
                        new.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
                        new['Translated'] = [translated_query] * len(new['Region'])
                        new['Word'] = [pair[0]] * len(new['Region'])
                        wordstat_eng_full = pd.concat([wordstat_eng_full, new])

                    wordstat_eng_full[1] = wordstat_eng_full[1].str.replace(' ', '')
                    wordstat_eng_full[1] = wordstat_eng_full[1].astype(float)
                    wordstat_eng_full[2] = wordstat_eng_full[2].str[:-1]
                    wordstat_eng_full[2] = wordstat_eng_full[2].str.replace(' ', '')
                    wordstat_eng_full[2] = wordstat_eng_full[2].astype(float)
                    wordstat_eng_full.columns = ['Region', 'Displays', 'Regional pop.', 'Translated', 'Word']
                    wordstat_eng_full.to_csv("Wordstat_eng_full")
        else:
            import json
            wordstat_eng_full = wordstat_eng[['Region', 'Displays', 'Regional pop.', 'Word']]
            for pair in clean_pairs:
                translated_query = translate_query(pair[0])
                ask_wordstat(translated_query)
                new = get_info_table()
                new.columns = ['Region', 'Displays', 'Regional pop.', 'Word']
                new['Translated'] = [translated_query] * len(new['Region'])
                new['Word'] = [pair[0]] * len(new['Region'])
                wordstat_eng_full = pd.concat([wordstat_eng_full, new])

            wordstat_eng_full[1] = wordstat_eng_full[1].str.replace(' ', '')
            wordstat_eng_full[1] = wordstat_eng_full[1].astype(float)
            wordstat_eng_full[2] = wordstat_eng_full[2].str[:-1]
            wordstat_eng_full[2] = wordstat_eng_full[2].str.replace(' ', '')
            wordstat_eng_full[2] = wordstat_eng_full[2].astype(float)
            wordstat_eng_full.columns = ['Region', 'Displays', 'Regional pop.', 'Translated', 'Word']
            wordstat_eng_full.to_csv("Wordstat_eng_full")
    else:
        if display_code == "Да":
            with st.echo():
                wordstat_eng_full = pd.read_csv('C:/Users/асер/Wordstat_eng_full', encoding='utf-8')
        else:
            wordstat_eng_full = pd.read_csv('C:/Users/асер/Wordstat_eng_full', encoding='utf-8')
else:
    if display_code == "Да":
        with st.echo():
            wordstat_eng_full = pd.read_csv('C:/Users/асер/Wordstat_eng_full', encoding='utf-8')
    else:
        wordstat_eng_full = pd.read_csv('C:/Users/асер/Wordstat_eng_full', encoding='utf-8')
wordstat_eng_full

'Мы получили 2 датафрейма со статистикой запросов на 2 языках. Хотя запросы на английском языке могут ' \
'делать и российские граждане, будем предполагать, что большая часть запросов на английском языке сделана иностранцами.' \
'Проверим, есть ли взаимосвязь между популярностью запросов среди русскоговорящих пользователей Яндекса и носителей ' \
'других языков. Для этого воспользуемся R и его математическими функциями.'
'Для данных из папки корреляция равнялась 0.0346...'
if display_code == "Да":
        'library (tidyverse)'
        'wordstat_eng_full<- read.csv("C:/Users/асер/Documents/data for project/Wordstat_eng_full", encoding = "UTF-8")'
        'wordstat_full<- read.csv("C:/Users/асер/Documents/data for project/Wordstat_full", encoding = "UTF-8")'
        'names(wordstat_eng_full) <- cbind("index_eng","region","regpop_eng","query_eng","word")'
        'names(wordstat_full) <- cbind("index","index2","region","query","regpop","word")'
        'top_wordstat < - wordstat_full % > % group_by(Word) % > % summarise(mean.reg_pop = mean(Regional.pop.)) % > % arrange(desc(mean.reg_pop))'
        'top_wordstat_eng < - wordstat_eng_full % > % group_by(Word) % > % summarise(mean.reg_pop_eng = mean(Regional.pop.)) % > % arrange(desc(mean.reg_pop_eng))'
        'two_langs < - merge(top_wordstat, top_wordstat_eng, on="word")'
        'cor(as.numeric(two_langs$mean.reg_pop_eng), as.numeric(two_langs$mean.reg_pop_eng))'

