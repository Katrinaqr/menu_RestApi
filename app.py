from flask import Flask, jsonify, render_template, request
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exc
from main import Base, Category, Weight, MenuItem, Menu, NotFoundError


engine = create_engine("sqlite:///menu.db", connect_args={"check_same_thread": False})
session = sessionmaker(bind=engine)
sess = session()

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False


def get_menu_items(menu_items=None, category=None):
    """Returns the list of items in the menu.
        It takes table elements as a parameter."""
    menu = []
    if category:
        menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == category).filter(
            Menu.title_id == MenuItem.id_item)
    try:
        for row in menu_items:
            menu_item = {}
            menu_item["title"] = row.MenuItem.title
            menu_item["category"] = sess.query(Category).filter_by(id_category=row.Menu.category_id).first().name
            menu_item["size"] = sess.query(Weight).filter_by(id_weight=row.Menu.weight_id).first().weight
            menu_item["weight"] = row.Menu.weight_desc
            menu_item["price"] = row.Menu.price
            menu_item["anonce"] = row.MenuItem.anonce
            # In the menu of categories drinks and sauces no values (calories, carbs, fats, proteins).
            if row.Menu.category_id != 4 and row.Menu.category_id != 5:
                menu_item["calories"] = row.Menu.calories
                menu_item["carbohydrates"] = row.Menu.carbohydrates
                menu_item["fats"] = row.Menu.fats
                menu_item["proteins"] = row.Menu.proteins
            menu.append(menu_item)
    except:
        menu = []
    return menu


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/menu")
def get_all_menu():
    menu_items = sess.query(Menu, MenuItem).filter(Menu.title_id == MenuItem.id_item)
    return jsonify(menu=sorted(get_menu_items(menu_items), key=lambda i: i["category"]))


@app.route("/menu/pizzas")
def get_all_pizzas():
    return jsonify(menu=get_menu_items(category=1))


@app.route("/menu/snacks")
def get_all_snacks():
    return jsonify(menu=get_menu_items(category=2))


@app.route("/menu/desserts")
def get_all_desserts():
    return jsonify(menu=get_menu_items(category=3))


@app.route("/menu/drinks")
def get_all_drinks():
    return jsonify(menu=get_menu_items(category=4))


@app.route("/menu/sauces")
def get_all_sauces():
    return jsonify(menu=get_menu_items(category=5))


@app.route("/menu/add", methods=["POST"])
def add_new_item():
    title = request.form.get("title")
    category = request.form.get("category")
    weight = request.form.get("size")
    try:
        sess.add(MenuItem(title=title,
                          anonce=request.form.get("anonce"),
                          photo_small=request.form.get("photo_small"),
                          photo_first=request.form.get("photo_first"),
                          photo_second=request.form.get("photo_second")))

        sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=title).first().id_item,
                      category_id=sess.query(Category).filter_by(name=category).first().id_category,
                      weight_id=sess.query(Weight).filter_by(weight=weight).first().id_weight,
                      weight_desc=request.form.get("weight"),
                      price=request.form.get("price"),
                      calories=request.form.get("calories"),
                      carbohydrates=request.form.get("carbohydrates"),
                      fats=request.form.get("fats"),
                      proteins=request.form.get("proteins")))
        sess.commit()
        new_item = sess.query(Menu, MenuItem).filter(MenuItem.title == title).filter(Menu.title_id == MenuItem.id_item)
        return jsonify(menu={"Successfully added the new item in Menu:": get_menu_items(new_item)})
    except AttributeError as er:
        if "id_category" in er.args[0]:
            raise NameError(f"Invalid name: {category}")
        else:
            raise NameError(f"Invalid name: {weight}")
    finally:
        sess.close()


@app.route("/menu/update/<item_id>", methods=["PUT"])
def update_menu_item(item_id):
    try:
        update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
            MenuItem.id_item == Menu.title_id).one()

        if update_item:
            title = request.form.get("title")
            category = request.form.get("category")
            weight = request.form.get("size")
            try:
                update_item.MenuItem.title = title
                update_item.Menu.category_id = sess.query(Category).filter_by(name=category).first().id_category
                update_item.Menu.weight_id = sess.query(Weight).filter_by(weight=weight).first().id_weight
                update_item.Menu.weight_desc = request.form.get("weight")
                update_item.Menu.price = request.form.get("price")
                update_item.MenuItem.anonce = request.form.get("anonce")
                update_item.Menu.calories = request.form.get("calories")
                update_item.Menu.carbohydrates = request.form.get("carbohydrates")
                update_item.Menu.fats = request.form.get("fats")
                update_item.Menu.proteins = request.form.get("proteins")
                sess.commit()
                update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
                    MenuItem.id_item == Menu.title_id)
                return jsonify(menu={"Successfully updated the item in Menu:": get_menu_items(update_item)})
            except AttributeError as er:
                if "id_category" in er.args[0]:
                    raise NameError(f"Invalid name: {category}")
                else:
                    raise NameError(f"Invalid name: {weight}")
    except exc.NoResultFound:
        raise NotFoundError(f"Unable to find item with id: {item_id}")
    finally:
        sess.close()


@app.route("/menu/delete/<item_id>", methods=["DELETE"])
def delete_menu_item(item_id):
    try:
        title_id = sess.query(Menu).filter(Menu.id_menu_item == item_id).first().title_id
        sess.query(Menu).filter(Menu.id_menu_item == item_id).delete()
        # If it was the only product in the Menu table, it can also be removed from the table MenuItem
        if not sess.query(Menu).filter(Menu.title_id == title_id).first():
            sess.query(MenuItem).filter(MenuItem.id_item == title_id).delete()
        sess.commit()
        return jsonify(menu={"Successfully delete the item with id:": item_id})
    except (exc.NoResultFound, AttributeError):
        raise NotFoundError(f"Unable to find item with id: {item_id}")


@app.route("/menu/pizzas/expensive")
def get_expensive_pizza():
    max_price = sorted(get_menu_items(category=1), key=lambda i: i["price"])[-1]["price"]
    menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == 1).filter(
            Menu.title_id == MenuItem.id_item).filter(Menu.price == max_price)
    return jsonify(menu=get_menu_items(menu_items))


@app.route("/menu/pizzas/cheap")
def get_cheap_pizza():
    min_price = sorted(get_menu_items(category=1), key=lambda i: i["price"])[0]["price"]
    menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == 1).filter(
        Menu.title_id == MenuItem.id_item).filter(Menu.price == min_price)
    return jsonify(menu=get_menu_items(menu_items))


if __name__ == "__main__":
    app.run(debug=True)
