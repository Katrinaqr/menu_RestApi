from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, validates
from sqlalchemy import create_engine
import requests

CATEGORIES_MENU = ["pizza", "snack", "dessert", "drink", "sauce"]
WEIGHT_ITEMS = ["big", "medium", "thin", "standard"]
# HEADERS is used in the response of the function (parse_csr), each will have its own.
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/98.0.4758.102 Safari/537.36"}
PIZZAS_URL = "https://pzz.by/api/v1/pizzas?load=ingredients,filters&filter=meal_only:0&order=position:asc"
SNACKS_URL = "https://pzz.by/api/v1/snacks?filter=meal_only:0&order=position:asc"
DESSERTS_URL = "https://pzz.by/api/v1/desserts?filter=pizzeria_type:pizzeria&order=position:asc"
DRINKS_URL = "https://pzz.by/api/v1/drinks?filter=pizzeria_type:pizzeria&order=position:asc"
SAUCES_URL = "https://pzz.by/api/v1/sauces"
MENU_URLS = [PIZZAS_URL, SNACKS_URL, DESSERTS_URL, DRINKS_URL, SAUCES_URL]
OTHER_MENU = [{"url": DESSERTS_URL, "category": "dessert"},
              {"url": DRINKS_URL, "category": "drink"},
              {"url": SAUCES_URL, "category": "sauce"}]

Base = declarative_base()
engine = create_engine("sqlite:///menu.db", connect_args={"check_same_thread": False})
session = sessionmaker(bind=engine)
sess = session()


class NotUnique(Exception):
    pass


class NotFoundError(Exception):
    pass


class Category(Base):
    __tablename__ = "categories"
    id_category = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)
    menu_item = relationship("Menu", back_populates="category")

    @validates("name")
    def validate_category(self, key, name):
        if not name:
            raise ValueError("Category must be a non-empty string.")
        return name


class Weight(Base):
    __tablename__ = "weight_items"
    id_weight = Column(Integer, primary_key=True)
    weight = Column(String(250), unique=True, nullable=False)
    menu_item = relationship("Menu", back_populates="weight")

    @validates("weight")
    def validate_category(self, key, weight):
        if not weight:
            raise ValueError("Weight must be a non-empty string.")
        return weight


class MenuItem(Base):
    __tablename__ = "menu_items"
    id_item = Column(Integer, primary_key=True)
    title = Column(String(250), unique=True, nullable=False)
    menu_item = relationship("Menu", back_populates="title")
    anonce = Column(String(250))
    photo_small = Column(String(250))
    photo_first = Column(String(250))
    photo_second = Column(String(250))

    @validates("title")
    def validate_title(self, key, title):
        if not title:
            raise ValueError("Title must be a non-empty string.")
        if sess.query(MenuItem).filter(MenuItem.title == title).first():
            raise NotUnique(f"{title} already exits. Title must be unique.")
        return title


class Menu(Base):
    __tablename__ = "menu"
    id_menu_item = Column(Integer, primary_key=True)
    title_id = Column(Integer, ForeignKey("menu_items.id_item"))
    title = relationship("MenuItem", back_populates="menu_item")
    category_id = Column(Integer, ForeignKey("categories.id_category"))
    category = relationship("Category", back_populates="menu_item")
    weight_id = Column(Integer, ForeignKey("weight_items.id_weight"))
    weight = relationship("Weight", back_populates="menu_item")
    weight_desc = Column(String(250))
    price = Column(Integer, nullable=False)
    calories = Column(Integer)
    carbohydrates = Column(Integer)
    fats = Column(Integer)
    proteins = Column(Integer)

    @validates("price")
    def validate_price(self, key, price):
        if not price:
            raise ValueError("Price must be a non-empty string.")
        try:
            float(price)
        except ValueError:
            raise ValueError("Price must be integer.")
        return price


Base.metadata.create_all(engine)


def parse_csr(url):
    """Returns the collected data from the site.
    It is required to replace headers with your own or remove the parameter."""
    response = requests.get(url=url, headers=HEADERS)
    data = response.json()["response"]["data"]
    return data


if not sess.query(Category).first():
    for item in CATEGORIES_MENU:
        sess.add(Category(name=item))
        sess.commit()

if not sess.query(Weight).first():
    for item in WEIGHT_ITEMS:
        sess.add(Weight(weight=item))
        sess.commit()

# Check if there are records in the database, if not, we insert the data that was collected from the site.
if not sess.query(MenuItem).first():
    for url in MENU_URLS:
        for item in parse_csr(url):
            anonce = ""
            photo_first = ""
            photo_second = ""
            if "pizzas" in url or "snacks" in url:
                anonce = item["anonce"]
                photo_first = item["photo1"]
                photo_second = item["photo2"]
            if not sess.query(MenuItem).filter_by(title=item["title"]).first():
                sess.add(MenuItem(title=item["title"],
                                  anonce=f"{anonce}",
                                  photo_small=item["photo_small"],
                                  photo_first=f"{photo_first}",
                                  photo_second=f"{photo_second}"))
                sess.commit()

if not sess.query(Menu).first():
    for item in parse_csr(PIZZAS_URL):
        # Checking in the requested data the presence of thin-crust pizzas
        if item["is_thin"] == 0:
            weight_items = ["big_weight", "medium_weight"]
        else:
            weight_items = ["big_weight", "medium_weight", "thin_weight"]
        for weight in weight_items:
            if weight == "big_weight":
                weight_item = "big"
                price = item["big_price"]
                calories = item["big_thin_calories"]
                carbohydrates = item["big_thin_carbohydrates"]
                fats = item["big_thin_fats"]
                proteins = item["big_thin_proteins"]
            elif weight == "medium_weight":
                weight_item = "medium"
                price = item["medium_price"]
                calories = item["medium_thin_calories"]
                carbohydrates = item["medium_thin_carbohydrates"]
                fats = item["medium_thin_fats"]
                proteins = item["medium_thin_proteins"]
            else:
                weight_item = "thin"
                price = item["thin_price"]
                calories = item["thin_thin_calories"]
                carbohydrates = item["thin_thin_carbohydrates"]
                fats = item["thin_thin_fats"]
                proteins = item["thin_thin_proteins"]
            sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=item["title"]).first().id_item,
                          category_id=sess.query(Category).filter_by(name="pizza").first().id_category,
                          weight_id=sess.query(Weight).filter_by(weight=weight_item).first().id_weight,
                          weight_desc=item[f"{weight}"],
                          price=price / 10000,
                          calories=calories,
                          carbohydrates=carbohydrates,
                          fats=fats,
                          proteins=proteins))
            sess.commit()

    for item in parse_csr(SNACKS_URL):
        # Checking the requested data for medium snacks
        if item["has_medium"] == 0:
            weight_items = ["big_amount"]
        else:
            weight_items = ["big_amount", "medium_amount"]
        for weight in weight_items:
            if weight == "big_amount":
                weight_item = "big"
                price = item["big_price"]
                calories = item["big_calories"]
                carbohydrates = item["big_carbohydrates"]
                fats = item["big_fats"]
                proteins = item["big_proteins"]
            else:
                weight_item = "medium"
                price = item["medium_price"]
                calories = item["medium_calories"]
                carbohydrates = item["medium_carbohydrates"]
                fats = item["medium_fats"]
                proteins = item["medium_proteins"]
            sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=item["title"]).first().id_item,
                          category_id=sess.query(Category).filter_by(name="snack").first().id_category,
                          weight_id=sess.query(Weight).filter_by(weight=weight_item).first().id_weight,
                          weight_desc=item[f"{weight}"],
                          price=price / 10000,
                          calories=calories,
                          carbohydrates=carbohydrates,
                          fats=fats,
                          proteins=proteins))
            sess.commit()

    for url in OTHER_MENU:
        # Keywords in the categories: (dessert, drinks, sauces) are similar, you can combine them into one group.
        for item in parse_csr(url["url"]):
            temp = "anonce"
            if url["category"] == "sauce":
                temp = "description"
            if url["category"] == "sauce" or url["category"] == "drink":
                calories, carbohydrates, fats, proteins = "", "", "", ""
            else:
                calories = item["calories"]
                carbohydrates = item["carbohydrates"]
                fats = item["fats"]
                proteins = item["proteins"]
            sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=item["title"]).first().id_item,
                          category_id=sess.query(Category).filter_by(name=url["category"]).first().id_category,
                          weight_id=sess.query(Weight).filter_by(weight="standard").first().id_weight,
                          weight_desc=item[f"{temp}"],
                          price=item["price"] / 10000,
                          calories=calories,
                          carbohydrates=carbohydrates,
                          fats=fats,
                          proteins=proteins))
            sess.commit()
