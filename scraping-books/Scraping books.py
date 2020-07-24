#!/usr/bin/env python
# coding: utf-8

# # Scrape books.toscrape.com
# 
# - List of books
# - Pictures
# - Price
# - Rating
# - UPC
# - In Stock
# - \# in stock

# In[1]:


from bs4 import BeautifulSoup
import requests
import csv


# In[2]:


CSV_CATALOG = 'books_catalogue.csv'
CSV_RESULT = 'books_catalog_complete.csv'


# In[3]:


def get_articles(soup):
    products = soup.find_all('article', class_='product_pod')
    rating_numbers = {'One':1, 'Two':2, 'Three':3, 'Four':4, 'Five':5}
    result = []
    for product in products:
        stars = rating_numbers[product.p['class'][1]]
        book_link = product.h3.a['href']
        book_title = product.h3.a['title']
        book_price1 = product.find(class_='price_color').text
        book_in_stock = product.find(class_='availability').i['class'] == ['icon-ok']
        book_in_stock = int(book_in_stock)
        book = {'stars': stars, 
                'link': book_link, 
                'title': book_title, 
                'price': book_price1, 
                'in_stock': book_in_stock,
               }
        result.append(book)
    return result

def reach_and_save_catalog():
    # Pagination
    articles = []
    print('Downloading pages...', end=" ")
    for i in range(1,51):
        url = f'http://books.toscrape.com/catalogue/page-{i}.html'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        articles += get_articles(soup)
        print(i, end=", ")

    # Save CSV
    fields = ['stars', 'link', 'title', 'price', 'in_stock']
    with open(CSV_CATALOG, 'w+') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(articles)
    
    return articles

def get_book_data(url = None):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    tds = soup.table.find_all('td')
    upc = tds[0].text
    available =  tds[-2].text
    try:
        n_stock = available.split('(')[1][:-1].split()[0]
        n_stock = int(n_stock)
    except:
        n_stock = 0
    pic = 'http://books.toscrape.com/' + soup.select('#product_gallery img')[0]['src'].strip(r'./')
    return {'upc': upc, 'stock': n_stock, 'picture': pic}

def reach_and_save_books(articles = None):
    if not articles:
        print(f'Please, read the {CSV_CATALOG} and feed me with a dictReader')
        return
    
    if type(articles) != list or type(articles[0]) != dict:
        print('UNKNOWN ERROR')
        return
        
    fields = ['upc', 'title', 'price', 'in_stock', 'stock', 'stars', 'link', 'picture']
    with open(CSV_RESULT, 'a+') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        
        books_data = []
        for book in articles:
            url = 'http://books.toscrape.com/catalogue/' + book['link']
            print(book['title'], url)
            extra = get_book_data(url)
            data = {**book, **extra}
            books_data.append(data)
            writer.writerow(data)
            print(f"Just saved {data['title']}")
    return books_data


# In[4]:


articles = reach_and_save_catalog()

books_data = reach_and_save_books(articles)


# ### Improvements (TO-DO)
# 
# * Convert GBP into Euro
#   * https://exchangeratesapi.io/
# * Upload pictures to Amazon Bucket
# * Make the code asynchronous

# In[ ]:




