import sqlite3
import requests
from bs4 import*

import os
if os.path.isfile('bdprogect.db'):
    os.remove('bdprogect.db')
    print("success")
else: print("File doesn't exists!")


LINK = {'mila': 'https://mila.by/catalog/dlya-detey-i-mam/podguzniki-i-pelenki/podguzniki-trusiki/?page=1&SECTION_CODE=podguzniki-trusiki&SECTION_PATH=dlya-detey-i-mam%7Cpodguzniki-i-pelenki%7Cpodguzniki-trusiki&set_filter=y&arrFilter_7629_2320655185=Y&arrFilter_7629_3414976804=Y&arrFilter_7658_3548588996=Y&arrFilter_7658_709751707=Y',
        'ostov': 'https://ostrov-shop.by/catalog/tovary-dlya-detey/gigiena-i-ukhod-za-detmi/podguzniki-trusiki/filter/prop_2033-is-подгузники-трусики-or-подгузники-трусики%20ночные/trademark-is-huggies-or-pampers/size_diapers-is-4-or-5/apply/',
        '21vek': 'https://www.21vek.by/diapers/?filter%5Bgood_status%5D%5B%5D=in&filter%5Bproducer%5D%5B%5D=huggies&filter%5Bproducer%5D%5B%5D=pampers&filter%5B4924%5D%5B%5D=15920&filter%5B74603%5D%5B%5D=540433&filter%5B74603%5D%5B%5D=540443&filter%5B74603%5D%5B%5D=540453&filter%5Bsa%5D='
}

def get_html(link):
    response = requests.get(link)
    return response.text


def info(elem1, elem2, elem3):
    count = weigth = size = label = ''

    dict_size = {'4': 'Maxi', '5': 'Junior'}
    elem1 = elem1.replace(',', ' ').replace(' до ', '-').split()

    for i in range(len(elem1)):
        if elem1[i] == 'шт.' or elem1[i] == 'шт':
            count = int(elem1[i - 1])
        if elem1[i] == 'кг' or elem1[i] == 'кг)':
            weigth = elem1[i - 1].replace('(', '')
        if elem1[i].title() == 'Huggies' or elem1[i].title() == 'Pampers':
            label = elem1[i].title()
    for key, value in dict_size.items():
        if key in elem1 or value in elem1:
            size = key + ' ' + value

    price = float(elem2.replace(',', '.').split()[0])
    shop = elem3

    return shop, label, size, weigth, count, price, round(price / count, 2)


def get_data_mila(html):
    shop = 'mila'
    soup = BeautifulSoup(html, 'lxml')
    elems = soup.find('div', class_='catalog-list').find_all('a')
    for elem in elems:
        name = elem.find('span', class_='label offer-name')
        if name is None:
            name = "No type"
        else:
            name = elem.find('span', class_='label offer-name').text

        price = elem.find('div', class_="price-line-listing").find('p', class_="price")
        if price is None:
            price = elem.find('div', class_="price-line-listing").find('p', class_="price new")
            if price is None:
                price = "No price"
            else:
                price = elem.find('div', class_="price-line-listing").find('p', class_="price new").text
        else:
            price = elem.find('div', class_="price-line-listing").find('p', class_="price").text

        add_date_bd(info(name, price, shop))


def get_data_ostrov(html):
    shop = 'ostrov'
    soup = BeautifulSoup(html, 'lxml')
    elems = soup.find_all('div',
                          class_='col-lg-3 col-md-4 col-sm-6 col-xs-6 col-xxs-12 item item-parent item_block js-ga-product-card')

    for elem in elems:
        name = elem.find('div', class_='item_info').find('a').text

        price = elem.find('div', class_="item_info").find('span')
        if price is None:
            price = "No price"
        else:
            price = elem.find('div', class_="item_info").find('span').text

        add_date_bd(info(name, price, shop))


def get_data_21vek(html):
    shop = '21vek'
    soup = BeautifulSoup(html, 'lxml')
    elems = soup.find_all('li', class_='result__item cr-result__full g-box_lseparator g-box_lseparator_catalog')
    for elem in elems:
        trs = elem.find('table').find_all('tr')

        name = []
        for tr in trs:
            info_td = tr.find_all('td', class_='result__attr_val')
            for i in info_td:
                name.append(i.text)

        name = ' '.join(name)
        name1 = elem.find('dl').find('div', class_="catalog-result__item_data").find('dt', class_="result__root").find(
            'a').find('span', class_="result__name").text
        price = elem.find('dl').find('div', class_="catalog-result__item_tools result__tools").find('span',
                                                                                                    class_="g-price result__price cr-price__in").find(
            'span', attrs={'data-category_id': '403'}).text
        name += name1
        add_date_bd(info(name, price, shop))


conn = sqlite3.connect("bdprogect.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS tabl(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    магазин TEXT,
    марка TEXT,
    размер TEXT,
    вес TEXT,
    количество INTEGER,
    [цена за упаковку] REAL,
    [цена за единицу] REAL)
""")
conn.commit()

# cursor.execute('DELETE FROM tabl')
# conn.commit()


def add_date_bd(info):
    cursor.execute("""INSERT INTO
                tabl(магазин, марка, размер, вес, количество, [цена за упаковку], [цена за единицу])
                VALUES(?, ?, ?, ?, ?, ?, ?)""",
                   info)
    conn.commit()


get_data_mila(get_html(LINK['mila']))
get_data_ostrov(get_html(LINK['ostov']))
get_data_21vek(get_html(LINK['21vek']))


cursor.execute("""SELECT *FROM tabl WHERE [цена за упаковку] = (SELECT MIN([цена за упаковку]) FROM tabl)""")
x = cursor.fetchall()
print('Самое выгодное предложение за упаковку:')
for elem in x:
    print(*elem[1:])

print("------")

cursor.execute("""SELECT *FROM tabl WHERE [цена за единицу] = (SELECT MIN([цена за единицу]) FROM tabl)""")
y = cursor.fetchall()
print('Самые выгодное предложение:')
for elem in y:
    print(*elem[1:])



