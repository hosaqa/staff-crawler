# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


from sqlalchemy.orm import sessionmaker
from db.database import engine
from db.models import Product  # Ваш клас Product
from sqlalchemy.exc import IntegrityError

Session = sessionmaker(bind=engine)


class OlxPipeline:
    def open_spider(self, spider):
        self.session = Session()

    def close_spider(self, spider):
        self.session.commit()
        self.session.close()

    def process_item(self, item, spider):
        # Перевіряємо наявність продукту з однаковим uri та name
        existing_product = self.session.query(Product).filter_by(uri=item['uri'], name=item['name']).first()

        if existing_product:
            # Якщо продукт вже є, не додаємо його
            spider.log(f"Product with uri: {item['uri']} and name: {item['name']} already exists in the database. Skipping...")
            return item

        product = Product(
            name=item.get('name'),
            price=item.get('price'),
            size=item.get('size'),
            uri=item.get('uri'),
            img_uri=item.get('img_uri'),
            posted_date=item.get('posted_date'),
            parsed_date=item.get('parsed_date'),
            viewed=item.get('viewed'),
        )
        try:
            # Додаємо продукт в сесію
            self.session.add(product)
        except IntegrityError:
            self.session.rollback()  # Відкат, якщо продукт вже існує
        return item
