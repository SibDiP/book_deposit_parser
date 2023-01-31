import requests
from bs4 import BeautifulSoup
import csv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# 1 | Get www.bookdepository.com
url = 'https://www.bookdepository.com/'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
while True:
    # 2 | Print all available book categories in console
    categories_dic = {}
    categories_dic_counter = 0
    categories = soup.find('div', class_='secondary-header').find_all('a')

    for category in categories:
        if 'href' in category.attrs and category['href'].startswith("/category"):
            categories_dic[categories_dic_counter] = [category.text.strip(), category['href']]
            categories_dic_counter += 1

    for category_num, data in categories_dic.items():
        print(f'{category_num:>4} | {data[0]}')

    # 3 | Ask for input category num
    while True:
        chosen_category = input("Choose category num: ")
        if not chosen_category:
            continue
        chosen_category = int(chosen_category)
        break

    # 4 | Get category page (like https://www.bookdepository.com/category/2/Art-Photography)
    category_link = f'https://www.bookdepository.com/{categories_dic[chosen_category][1]}'
    response = requests.get(category_link)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 5 | Loop through each book in category
    books = soup.find_all('div', class_='book-item')
    amount_of_books_in_category = len(books)

    amount_of_books_needed = input(f"Found {amount_of_books_in_category} books in category.\n"
                                   f"How many should scrap? (type number for exact amount, or 'All' to scrap all "
                                   f"available books): ")
    if not amount_of_books_needed:
        amount_of_books_needed = 10
    if amount_of_books_needed.lower() == 'all':
        amount_of_books_needed = amount_of_books_in_category

    current_book = 1
    for book in books[:int(amount_of_books_needed)]:
        print(f"Progress: {current_book:>3}/{amount_of_books_needed:<3}")
        current_book += 1
        link = book.find('a')['href']
        book_link = f"https://www.bookdepository.com{link}"
        response = requests.get(book_link)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 6.1 | Scrap associated categories
        data_categories = ", ".join([item.text.strip() for item in soup.find('ol', class_='breadcrumb').find_all("a")])
        logging.info(f"categories: {data_categories}")

        # 6.2 | Scrap Title
        data_titles = ', '.join([item.text.strip() for item in soup.find_all('h1', itemprop='name')])
        logging.info(f"title: {data_titles}")

        # 6.3 | Scrap rating
        try:
            data_rating = soup.find('span', itemprop="ratingValue").text.strip()
        except AttributeError:
            data_rating = ""
        logging.info(f"rating: {data_rating}")

        # 6.4 | Scrap rating by google
        try:
            data_rating_by_google = soup.find('span', class_="rating-count").text.strip()
        except AttributeError:
            data_rating_by_google = ""
        logging.info(f"rating_by_google: {data_rating_by_google}")

        # 6.5 | Scrap Meta data
        meta_data_li = [item for item in soup.find('ul', class_="meta-info hidden-md").find_all('li')]
        data_meta = ", ".join([li.text for li in meta_data_li if not li.find("span", itemprop="inLanguage")])
        logging.info(f"meta: {data_meta}")

        # 6.6 | Scrap languages
        data_languages = ", ".join([item.text.strip() for item in soup.find_all('span', itemprop="inLanguage")])
        logging.info(f"Languages: {data_languages}")

        # 6.7 | Scarp Author
        data_authors = ", ".join([item.text.strip() for item in soup.find('div', class_='author-info hidden-md')
                                 .find_all("span", itemprop="name")])
        logging.info(f"authors: {data_authors}")

        # 7 | Write scraped data to .csv file
        if current_book == 1:
            with open(f'{categories_dic[chosen_category][0]}.csv', mode='w') as file:
                writer = csv.writer(file)
                writer.writerow([data_titles, data_authors, data_categories, data_languages, data_rating,
                                 data_rating_by_google, data_categories, data_meta])

        with open(f'{categories_dic[chosen_category][0]}.csv', mode='a', newline="") as file:
            writer = csv.writer(file)
            writer.writerow([data_titles, data_authors, data_categories, data_languages, data_rating,
                             data_rating_by_google, data_categories, data_meta])

    print(f'Done! Results saved in "{categories_dic[chosen_category][0]}.csv"')

    while True:
        what_is_next = input("Want to parse another category? [y/n]: ").lower()

        if what_is_next == "n":
            exit()
        if what_is_next == 'y':
            break

