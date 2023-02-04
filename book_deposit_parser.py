import csv
import logging
import os
import re
import json
import random
from time import sleep

from fake_useragent import UserAgent
import requests

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def make_dir(dir_name: str) -> str:
    """
    Create dir with given name in . Return str with dir path
    """
    try:
        os.mkdir(f"{dir_name}")
    except FileExistsError:
        pass
    return f'{dir_name}/'


def url_to_soup(url_address: str) -> object:
    """
    Create a BeautifulSoup object with attributes (response.text, 'html.parser)'
    :param url_address: url address of website
    :return: BeautifulSoup object
    """
    headers = {
        "Accept": '*/*',
        "User-Agent": UserAgent().random
    }
    resp = requests.get(url_address, headers=headers)

    return BeautifulSoup(resp.text, 'html.parser')


dir_result_path = make_dir("Results")

# Get www.bookdepository.com
soup = url_to_soup('https://www.bookdepository.com/')

while True:
    # Print all available book categories in console
    categories_dic = {}
    categories_dic_counter = 1
    categories = soup.find('div', class_='secondary-header').find_all('a')

    for category in categories:
        if 'href' in category.attrs and category['href'].startswith("/category"):
            categories_dic[categories_dic_counter] = [category.text.strip(), category['href']]
            categories_dic_counter += 1

    for category_num, category_title in categories_dic.items():
        print(f'{category_num:>4} | {category_title[0]}')
    print(f"{'-' * 30}")

    # Ask for input category num
    one_page_pattern = re.compile(r'\d+')
    while True:
        chosen_category = input(f"> Choose category id: ")
        if re.fullmatch(one_page_pattern, chosen_category):
            chosen_category = int(chosen_category)
            break
        continue

    logging.info(categories_dic)
    logging.info(chosen_category)
    logging.info(categories_dic[chosen_category][1])

    # Get category page (like https://www.bookdepository.com/category/2/Art-Photography)
    soup = url_to_soup(f'https://www.bookdepository.com/{categories_dic[chosen_category][1]}')

    # Loop through each book in category
    books = soup.find_all('div', class_='book-item')
    amount_of_books_in_category = len(books)
    amount_of_books_needed = input(f"Found {amount_of_books_in_category} books in {categories_dic[chosen_category][0]}"
                                   f" category.\n> How many should scrap? (Enter the exact amount): ")

    if amount_of_books_needed.lower() == 'all':
        amount_of_books_needed = amount_of_books_in_category
    elif not amount_of_books_needed or not amount_of_books_needed.isdigit():
        amount_of_books_needed = 10

    print(f"{'-' * 30}")
    current_book = 0
    for book in books[:int(amount_of_books_needed)]:
        current_book += 1
        print(f"Progress: {current_book:>3}/{amount_of_books_needed:<3}")
        relative_book_link = book.find('a')['href']
        full_book_link = f"https://www.bookdepository.com{relative_book_link}"
        soup = url_to_soup(full_book_link)

        # Scrap associated categories
        data_categories = ", ".join([item.text.strip() for item in soup.find('ol', class_='breadcrumb').find_all("a")])
        logging.info(f"categories: {data_categories}")

        # Scrap Title
        data_titles = ', '.join([item.text.strip() for item in soup.find_all('h1', itemprop='name')])
        logging.info(f"title: {data_titles}")

        # Scrap rating
        try:
            data_rating = soup.find('span', itemprop="ratingValue").text.strip()
        except AttributeError:
            data_rating = ""
        logging.info(f"rating: {data_rating}")

        # Scrap rating by google
        try:
            data_rating_by_google = soup.find('span', class_="rating-count").text.strip()
        except AttributeError:
            data_rating_by_google = ""
        logging.info(f"rating_by_google: {data_rating_by_google}")

        # Scrap Meta data
        meta_data_li = [item for item in soup.find('ul', class_="meta-info hidden-md").find_all('li')]
        data_meta = ", ".join([li.text for li in meta_data_li if not li.find("span", itemprop="inLanguage")])
        logging.info(f"meta: {data_meta}")

        # Scrap languages
        data_languages = ", ".join([item.text.strip() for item in soup.find_all('span', itemprop="inLanguage")])
        logging.info(f"Languages: {data_languages}")

        # Scarp Author
        data_authors = ", ".join([item.text.strip() for item in soup.find('div', class_='author-info hidden-md')
                                 .find_all("span", itemprop="name")])
        logging.info(f"authors: {data_authors}")

        # Export to .csv and .json files
        data_to_csv_export = [data_titles, data_authors, data_categories, data_languages, data_rating,
                              data_rating_by_google, data_meta]

        csv_to_export = f'{dir_result_path}{categories_dic[chosen_category][0]}.csv'

        if current_book == 1:
            with open(csv_to_export, mode='w') as file:
                writer = csv.writer(file)
                writer.writerow(data_to_csv_export)

        else:
            with open(csv_to_export, mode='a', newline="") as file:
                writer = csv.writer(file)
                writer.writerow(data_to_csv_export)
        sleep(random.randrange(2, 4))

    print(f"{'-' * 30}")
    print(f'Done! Results saved in {csv_to_export}')

    # .csv to .json export
    print('Converting .csv in .json ...')
    json_to_export = f'{dir_result_path}{categories_dic[chosen_category][0]}.json'
    with open(csv_to_export, mode='r') as file:
        reader = csv.reader(file)
        data_to_json_export = []
        for row in reader:
            data_to_json_export.append({
                "Title": row[0],
                "Author": row[1],
                "Category": row[2],
                "Languages": row[3],
                "Rating": row[4],
                "Rating stats by Google": row[5],
                "Meta data:": row[6]
            })

    with open(json_to_export, mode='a', encoding='utf-8') as file:
        json.dump(data_to_json_export, file, indent=4, ensure_ascii=False)

    print(f'Done! Results saved in {json_to_export}')
    print(f"{'-' * 30}")

    while True:
        what_is_next = input("Want to parse another category? [y/n]: ").lower()
        if what_is_next == "n":
            exit()
        if what_is_next == 'y':
            break
