from pathlib import Path
import urllib.parse
from scrapy_playwright.page import PageMethod
import re
import pytz
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import sessionmaker
from db.database import engine
from db.models import Product  # Ваш клас Product
from sqlalchemy.exc import IntegrityError

import scrapy

def format_date_to_uk(d):
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    local_time = kyiv_tz.localize(d)

    # Виводимо дату у форматі ISO 8601
    iso_format = local_time.isoformat()

    return iso_format

def parse_stringified_date(stringfied_date):
    months = {
        'січня': 1,
        'лютого': 2,
        'березня': 3,
        'квітня': 4,
        'травня': 5,
        'червня': 6,
        'липня': 7,
        'серпня': 8,
        'вересня': 9,
        'жовтня': 10,
        'листопада': 11,
        'грудня': 12
    }


    # Ваш масив
    date_array = stringfied_date.split(' ')

    if date_array[0] == 'Сьогодні':
        return format_date_to_uk(datetime.now())

    # Витягуємо значення з масиву
    day = int(date_array[0])
    month = months[date_array[1]]
    year = int(date_array[2])

    # Створюємо об'єкт datetime
    local_time = datetime(year, month, day)

    return format_date_to_uk(local_time)


def parse_number(text):
    match = re.search(r'\d+', text)

    if match:
        # Перетворюємо знайдену цифру в int
        number = int(match.group())

        return number
    else:
        print("Цифра не знайдена")

def update_page_in_url(url, new_page_number):
    # Розбираємо URL на частини
    parsed_url = urllib.parse.urlparse(url)
    
    # Перетворюємо параметри запиту в словник
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    # Змінюємо параметр page на новий номер
    query_params['page'] = [str(new_page_number)]
    
    # Формуємо новий URL з оновленими параметрами
    updated_query = urllib.parse.urlencode(query_params, doseq=True)
    updated_url = urllib.parse.urlunparse(parsed_url._replace(query=updated_query))
    
    return updated_url

def parse_price(price_str):
    try:
        # Видаляємо 'грн.' і пробіли, залишаємо лише цифри
        clean_price = price_str.replace('грн.', '').replace(' ', '').strip()
        
        # Перетворюємо на число
        return int(clean_price)
    except (ValueError, AttributeError):
        # У разі помилки повертаємо 0
        return 0

Session = sessionmaker(bind=engine)


class PufferSpider(scrapy.Spider):
    name = "puffer"

    def __init__(self):
        self.db = Session()
        self.found_existing_count = 0  # Лічильник існуючих продуктів

    def start_requests(self):
        urls = [
            #"https://www.olx.ua/uk/moda-i-stil/muzhskaya-odezhda/q-вінтажна-футболка-arsenal/?currency=UAH",
            #"https://www.olx.ua/uk/moda-i-stil/muzhskaya-odezhda/q-fjallraven-jacket/?currency=UAH",
            "https://www.olx.ua/uk/moda-i-stil/muzhskaya-odezhda/verhnyaya-odezhda/q-stussy/?currency=UAH&search[filter_enum_size][0]=l&search[filter_enum_size][1]=xl&search[filter_enum_state][0]=used&search[order]=created_at%3Adesc",
            "https://www.olx.ua/uk/moda-i-stil/muzhskaya-odezhda/q-винтажная-куртка/?currency=UAH&search[filter_enum_size][0]=l&search[filter_enum_size][1]=xl&search[filter_enum_state][0]=used&search[order]=created_at%3Adesc",
        ]
        for url in urls:
            yield scrapy.Request(
                url=urllib.parse.quote(url, safe=':/?&=%'),
                callback=self.parse,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_load_state", "load"),
                        PageMethod(
                            "evaluate", 
                            """
                            (function autoScrollUntilVisible() {
                                let target = document.querySelector('div[data-testid="pagination-wrapper"]');
                                if (!target) return;
                                let intervalId = setInterval(() => {
                                    let rect = target.getBoundingClientRect();
                                    if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
                                        clearInterval(intervalId); // Зупиняємо скролінг
                                    } else {
                                        window.scrollBy(0, 100); // Скролимо вниз
                                    }
                                }, 100);
                            })();
                            """
                        ),
                        PageMethod("wait_for_timeout", 15000),
                    ],
                )
            )

    async def parse(self, response):
        # Скидаємо лічильник знайдених продуктів для кожного нового запиту
        self.found_existing_count = 0

        single_page_elem = response.xpath('//p[text()="Ми знайшли результати для схожих запитів:"]').get()
        many_pages = single_page_elem is None

        countString = response.xpath('//span[@data-testid="total-count"]/text()').get()
        count = parse_number(countString)

        container = response.xpath('//div[@data-testid="listing-grid"]')
        cards = container.xpath('.//div[@data-testid="l-card"]') if many_pages else container.xpath('.//div[@data-testid="l-card"]')[:count]
        self.logger.info(count)


        for cardItem in cards:
            item_name = cardItem.xpath('.//div[@data-cy="ad-card-title"]/a/h6/text()').get()
            item_uri =  response.urljoin(cardItem.xpath('.//div[@data-cy="ad-card-title"]/a/@href').get())

            existing_product = self.db.query(Product).filter(
                Product.uri == item_uri,
                Product.name == item_name
            ).first()

            if existing_product:
                self.found_existing_count += 1

            yield {
                "name": item_name,
                "uri": response.urljoin(cardItem.xpath('.//div[@data-cy="ad-card-title"]/a/@href').get()),
                "price": parse_price(cardItem.xpath('.//p[@data-testid="ad-price"]/text()').get()),
                "img_uri": cardItem.xpath('.//a/div/div/img/@src').get(),
                "size": cardItem.xpath('.//span[@data-testid="param-value"]/text()').get() or None,
                "posted_date": parse_stringified_date(cardItem.xpath('.//*[@data-testid="location-date"]/text()').getall()[2]),
                "parsed_date": format_date_to_uk(datetime.now()),
                "viewed": False,
            }

        pagination_wrapper = response.xpath('//div[@data-testid="pagination-wrapper"]')

        if self.found_existing_count >= 10:
            self.logger.info('MORE THAN 10 ITEMS ARE ALREADY IN DB')


        if many_pages and pagination_wrapper.get() is not None and self.found_existing_count < 10:
            #last_page_elem = pagination_wrapper.xpath('.//li[contains(@class, "pagination-item")][last()]')
            forward_elem = pagination_wrapper.xpath('.//a[@data-testid="pagination-forward"]')
            
            if forward_elem.get() is not None:
                #next_page_number = parse_number(next_page_elem.xpath('//a/text()').get())
                #last_page_number = last_page_elem.xpath('.//a/text()').get()
                #last_page_number = parse_number(last_page_number)

                next_page_url = forward_elem.xpath('@href').get()
                next_page_url = response.urljoin(next_page_url)
                #page_range = range(2, last_page_number + 1)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_methods=[
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_load_state", "networkidle"),
                            PageMethod("wait_for_load_state", "load"),
                            PageMethod(
                                "evaluate", 
                                """
                                (function autoScrollUntilVisible() {
                                    let target = document.querySelector('div[data-testid="pagination-wrapper"]');
                                    if (!target) return;
                                    let intervalId = setInterval(() => {
                                        let rect = target.getBoundingClientRect();
                                        if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
                                            clearInterval(intervalId); // Зупиняємо скролінг
                                        } else {
                                            window.scrollBy(0, 100); // Скролимо вниз
                                        }
                                    }, 100);
                                })();
                                """
                            ),
                            PageMethod("wait_for_timeout", 15000),
                        ],
                    )
                )
        
        
  

###

###
        #filename = f"puffer.html"
        #Path(filename).write_bytes(response.body)
        #self.log(f"Saved file {filename}")
