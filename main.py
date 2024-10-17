from fasthtml.common import *
from sqlalchemy.dialects.postgresql import insert

import sys

sys.path.append('./db')

from db.models import Base, Product
from db.database import engine, SessionLocal

Base.metadata.create_all(bind=engine)

# Функція для створення сесії з базою даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функція для завантаження всіх даних з таблиці Product
def get_all_products():
    # Отримуємо сесію
    db = next(get_db())

    # Виконуємо запит для отримання всіх записів з таблиці Product
    products = db.query(Product).order_by(Product.parsed_date.desc()).all()

    return products

app, rt = fast_app(static_path='public')

def render_img(src):
    # The code below is a set of ft components
    return Div(
        Img(src=src, style="display: block; max-width: 320px;"),
    )


def render_item(name, link, img_link, price, size, parsed_datex):
    return Div(
        A(
            render_img(src=img_link),
            href=link,
            style="display: block; max-width: 320px;",
            target="_blank"
        ),
        A(name, href=link, target="_blank"),
        Div(price),
        Div(size),
        Div(parsed_datex),
        cls="col-xs-12 col-sm-8 col-md-6 col-lg-4",
    ),

@rt("/")
def get():
    data = get_all_products()

    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "size": product.size,
            "uri": product.uri,
            "img_uri": product.img_uri,
            "posted_date": product.posted_date.isoformat() if product.posted_date else None,
            "parsed_datex": product.parsed_date.isoformat() if product.parsed_date else None,
            "viewed": product.viewed
        }
        for product in data
    ]

    list = [render_item(
        name=item["name"],
        link=item["uri"],
        img_link=item["img_uri"],
        price=item["price"],
        size=item["size"],
        parsed_datex=item["parsed_datex"],
    ) for item in product_list]


    return Container(
        Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css", type="text/css"),
        Div(len(list)),
        Div(
            *list,
            cls="row"
        ),
    )

serve()