from pathlib import Path
import time
import urllib.parse
from scrapy_playwright.page import PageMethod
import re


import scrapy


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

class PufferSpider(scrapy.Spider):
    name = "html"


    def start_requests(self):
        urls = [
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
                        #PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                        #PageMethod("evaluate", 'function autoScroll(){var o=0,l=setInterval(function(){window.scrollBy(0,100),++o>=40&&clearInterval(l)},100)},autoScroll();'),
                        #PageMethod("evaluate", "eval('function autoScrollUntilVisible(){let t=document.querySelector(\'div[data-testid=\"pagination-wrapper\"]\');if(!t)return;let e=setInterval(()=>{let i=t.getBoundingClientRect();i.top>=0&&i.bottom<=window.innerHeight?clearInterval(e):window.scrollBy(0,100)},100)}autoScrollUntilVisible();')"),
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
                        PageMethod("wait_for_timeout", 10000),
                        #PageMethod("wait_for_selector", '[data-testid="l-card"]'),
                    ],
                )
            )

    async def parse(self, response):
        self.logger.info('started')

        #page = response.meta['playwright_page']
        #await page.wait_for_timeout(1000) # wait for 1000 milliseconds


        #self.logger.info('here')

        #for _ in range(20):
        #    await page.keyboard.press("ArrowDown", delay=100)
        
        #await page.wait_for_timeout(5000) # wait for 1000 milliseconds


        filename = f"new_page.html"
        Path(filename).write_bytes(response.body)

  

###

###
        #filename = f"puffer.html"
        #Path(filename).write_bytes(response.body)
        #self.log(f"Saved file {filename}")
