from flask import Flask, request, jsonify, render_template, make_response
from main import Category, Weight, MenuItem, Menu, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exc
from functools import wraps
import datetime
import jwt


engine = create_engine("sqlite:///menu.db")
session = sessionmaker(bind=engine)
sess = session()

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            curr_user = sess.query(User).filter(User.email == data["email"]).first()
        except:
            return jsonify({"message": "Token is invalid!"}), 401

        return f(curr_user, *args, **kwargs)

    return decorated


def get_menu_items(menu_items):
    """Returns the list of items in the menu.
        It takes table elements as a parameter."""
    menu = []
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


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"message": "Resource Not Found."}), 404
    # return render_template("404.html"), 404


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/menu")
def get_all_menu():
    menu_items = sess.query(Menu, MenuItem).filter(Menu.title_id == MenuItem.id_item)
    return jsonify(menu=sorted(get_menu_items(menu_items), key=lambda i: i["category"]))


@app.route("/menu/<category>", methods=["GET"])
def get_items_category(category):
    try:
        category_id = sess.query(Category).filter(Category.name == category).first().id_category
    except AttributeError:
        return jsonify({"message": f"Invalid category name: {category}."}), 400
    menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == category_id).filter(
        Menu.title_id == MenuItem.id_item)
    return jsonify(menu=get_menu_items(menu_items))


@app.route("/menu/pizza/expensive")
def get_expensive_pizza():
    price = sess.query(Menu.price).filter(Menu.category_id == 1).all()
    menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == 1).filter(
        Menu.title_id == MenuItem.id_item).filter(Menu.price == max(price)[0])
    return jsonify(menu=get_menu_items(menu_items))


@app.route("/menu/pizza/cheap")
def get_cheap_pizza():
    price = sess.query(Menu.price).filter(Menu.category_id == 1).all()
    menu_items = sess.query(Menu, MenuItem).filter(Menu.category_id == 1).filter(
        Menu.title_id == MenuItem.id_item).filter(Menu.price == min(price)[0])
    return jsonify(menu=get_menu_items(menu_items))


@app.route("/menu", methods=["POST"])
@token_required
def add_new_item(curr_user):
    if curr_user.name != "super" and curr_user.name != "admin":
        return jsonify({"message": "No access to this function."}), 403

    title = MenuItem.validate_title(request.form.get("title"))
    category = Category.validate_category(request.form.get("category"))
    weight = Weight.validate_weight(request.form.get("weight"))
    price = Menu.validate_price(request.form.get("price"))
    for item in (title, category, weight, price):
        if isinstance(item, dict):
            return jsonify(item), 400
    try:
        sess.add(MenuItem(title=title,
                          anonce=request.form.get("anonce"),
                          photo_small=request.form.get("photo_small"),
                          photo_first=request.form.get("photo_first"),
                          photo_second=request.form.get("photo_second")))

        sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=title).first().id_item,
                      category_id=sess.query(Category).filter_by(name=category).first().id_category,
                      weight_id=sess.query(Weight).filter_by(weight=weight).first().id_weight,
                      weight_desc=request.form.get("weight_desc"),
                      price=price,
                      calories=request.form.get("calories"),
                      carbohydrates=request.form.get("carbohydrates"),
                      fats=request.form.get("fats"),
                      proteins=request.form.get("proteins"),
                      user_create=curr_user.id))
        sess.commit()
        new_item = sess.query(Menu, MenuItem).filter(MenuItem.title == title).filter(Menu.title_id == MenuItem.id_item)
        return jsonify(menu={"Successfully added the new item in Menu:": get_menu_items(new_item)}), 201
    finally:
        sess.close()


@app.route("/menu/<item_id>", methods=["PUT"])
@token_required
def update_menu_item(curr_user, item_id):
    try:
        update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
            MenuItem.id_item == Menu.title_id).one()
        if curr_user.name != "super" and curr_user.name != "admin" or \
                curr_user.name == "admin" and curr_user.id != update_item.Menu.user_create:
            return jsonify({"message": "No access to this function."}), 403

        title = request.form.get("title")
        if not title:
            return jsonify({"message": "Title must be a non-empty."})
        category = Category.validate_category(request.form.get("category"))
        weight = Weight.validate_weight(request.form.get("weight"))
        price = Menu.validate_price(request.form.get("price"))
        for item in (category, weight, price):
            if isinstance(item, dict):
                return jsonify(item), 400
        try:
            update_item.MenuItem.title = title
            update_item.Menu.category_id = sess.query(Category).filter_by(name=category).first().id_category
            update_item.Menu.weight_id = sess.query(Weight).filter_by(weight=weight).first().id_weight
            update_item.Menu.weight_desc = request.form.get("weight_desc")
            update_item.Menu.price = price
            update_item.MenuItem.anonce = request.form.get("anonce")
            update_item.Menu.calories = request.form.get("calories")
            update_item.Menu.carbohydrates = request.form.get("carbohydrates")
            update_item.Menu.fats = request.form.get("fats")
            update_item.Menu.proteins = request.form.get("proteins")
            update_item.MenuItem.photo_small = request.form.get("photo_small")
            update_item.MenuItem.photo_first = request.form.get("photo_first")
            update_item.MenuItem.photo_second = request.form.get("photo_second")
            sess.commit()
            update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
                            MenuItem.id_item == Menu.title_id)
            return jsonify(menu={"Successfully updated the item in Menu:": get_menu_items(update_item)}), 201
        except exc.IntegrityError:
            return jsonify({"message": f"{title} already exists in the menu. Title must be unique."}), 400
        finally:
            sess.close()
    except exc.NoResultFound:
        return jsonify({"message": f"Unable to find item with id: {item_id}."}), 404


@app.route("/menu/<item_id>", methods=["DELETE"])
@token_required
def delete_menu_item(curr_user, item_id):
    try:
        delete_item = sess.query(Menu).filter(Menu.id_menu_item == item_id)
        title_id = delete_item.first().title_id
        if curr_user.name != "super" and curr_user.name != "admin" or \
                curr_user.name == "admin" and curr_user.id != delete_item.first().user_create:
            return jsonify({"message": "No access to this function."}), 403
        delete_item.delete()
        # If it was the only product in the Menu table, it can also be removed from the table MenuItem
        if not sess.query(Menu).filter(Menu.title_id == title_id).first():
            sess.query(MenuItem).filter(MenuItem.id_item == title_id).delete()
        sess.commit()
        return jsonify(menu={"Successfully delete the item with id:": item_id}), 200
    except (exc.NoResultFound, AttributeError):
        return jsonify({"message": f"Unable to find item with id: {item_id}."}), 404


@app.route("/user", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        new_user = User(name=data["name"], email=data["email"])
        name_check = new_user.validate_name(data["name"])
        email_check = new_user.validate_email(data["email"])
        password_check = new_user.validate_password(data["password"])
        for item in (name_check, email_check, password_check):
            if isinstance(item, dict):
                return jsonify(item), 400
        new_user.set_password(data["password"])
        sess.add(new_user)
        sess.commit()
        return jsonify({"message": "New user created!"}), 201
    finally:
        sess.close()


@app.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response("Could not verify: user not found.", 401, {"WWW-Authenticate": "Basic realm='Login required!'"})
    user = sess.query(User).filter(User.name == auth.username).first()

    if not user:
        return make_response("Could not verify: invalid name.", 401, {"WWW-Authenticate": "Basic realm='Login required!'"})

    if user.check_password(auth.password):
        token = jwt.encode({"email": user.email, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                           app.config['SECRET_KEY'])
        return jsonify({"token": token})

    return make_response("Could not verify: invalid password.", 401, {"WWW-Authenticate": "Basic realm='Login required!'"})


if __name__ == "__main__":
    app.run(debug=True)
