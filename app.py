from flask import Flask, jsonify, render_template, redirect, url_for, flash, abort
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exc
from functools import wraps
from main import Category, Weight, MenuItem, Menu, User, LoginForm, CreateMenuItemForm, NotFoundError, NotUnique


engine = create_engine("sqlite:///menu.db", connect_args={"check_same_thread": False})
session = sessionmaker(bind=engine)
sess = session()

app = Flask(__name__)
app.config['SECRET_KEY'] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return sess.query(User).get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1 and current_user.id != 2:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


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
    user = "anonymous"
    if current_user.is_authenticated:
        user = current_user.name
    return render_template("index.html", user=user)


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


@app.route("/menu/add", methods=["GET", "POST"])
@admin_only
def add_new_item():
    form = CreateMenuItemForm()
    if form.validate_on_submit():
        title = form.title.data
        category = form.category.data
        weight = form.weight.data
        try:
            sess.add(MenuItem(title=title,
                              anonce=form.anonce.data,
                              photo_small=form.photo_small.data,
                              photo_first=form.photo_first.data,
                              photo_second=form.photo_second.data))

            sess.add(Menu(title_id=sess.query(MenuItem).filter_by(title=title).first().id_item,
                          category_id=sess.query(Category).filter_by(name=category).first().id_category,
                          weight_id=sess.query(Weight).filter_by(weight=weight).first().id_weight,
                          weight_desc=form.weight_desc.data,
                          price=form.price.data,
                          calories=form.calories.data,
                          carbohydrates=form.carbohydrates.data,
                          fats=form.fats.data,
                          proteins=form.proteins.data,
                          user_create=current_user.id))
            sess.commit()
            new_item = sess.query(Menu, MenuItem).filter(MenuItem.title == title).filter(Menu.title_id == MenuItem.id_item)
            return jsonify(menu={"Successfully added the new item in Menu:": get_menu_items(new_item)})
        except exc.IntegrityError:
            raise NotUnique(f"{title} already exits. Title must be unique.")
        except AttributeError as er:
            if "id_category" in er.args[0]:
                raise NameError(f"Invalid name: {category}")
            else:
                raise NameError(f"Invalid name: {weight}")
        finally:
            sess.close()

    return render_template("add.html", form=form)


@app.route("/menu/update/<item_id>", methods=["GET", "POST"])
@admin_only
def update_menu_item(item_id):
    try:
        update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
            MenuItem.id_item == Menu.title_id).one()
        form = CreateMenuItemForm(title=update_item.MenuItem.title,
                                  category=update_item.Menu.category.name,
                                  weight=update_item.Menu.weight.weight,
                                  weight_desc=update_item.Menu.weight_desc,
                                  price=update_item.Menu.price,
                                  anonce=update_item.MenuItem.anonce,
                                  calories=update_item.Menu.calories,
                                  carbohydrates=update_item.Menu.carbohydrates,
                                  fats=update_item.Menu.fats,
                                  proteins=update_item.Menu.proteins,
                                  photo_small=update_item.MenuItem.photo_small,
                                  photo_first=update_item.MenuItem.photo_first,
                                  photo_second=update_item.MenuItem.photo_second)
        if current_user.id == 1 or update_item.Menu.user_create == current_user.id:
            if form.validate_on_submit():
                title = form.title.data
                category = form.category.data
                weight = form.weight.data
                try:
                    update_item.MenuItem.title = title
                    update_item.Menu.category_id = sess.query(Category).filter_by(name=category).first().id_category
                    update_item.Menu.weight_id = sess.query(Weight).filter_by(weight=weight).first().id_weight
                    update_item.Menu.weight_desc = form.weight_desc.data
                    update_item.Menu.price = form.price.data
                    update_item.MenuItem.anonce = form.anonce.data
                    update_item.Menu.calories = form.calories.data
                    update_item.Menu.carbohydrates = form.carbohydrates.data
                    update_item.Menu.fats = form.fats.data
                    update_item.Menu.proteins = form.proteins.data
                    update_item.MenuItem.photo_small = form.photo_small.data
                    update_item.MenuItem.photo_first = form.photo_first.data
                    update_item.MenuItem.photo_second = form.photo_second.data
                    sess.commit()
                    update_item = sess.query(Menu, MenuItem).filter(Menu.id_menu_item == item_id).filter(
                        MenuItem.id_item == Menu.title_id)
                    return jsonify(menu={"Successfully updated the item in Menu:": get_menu_items(update_item)})
                except AttributeError as er:
                    if "id_category" in er.args[0]:
                        raise NameError(f"Invalid name: {category}")
                    else:
                        raise NameError(f"Invalid name: {weight}")
        else:
            return abort(403)
    except exc.NoResultFound:
        raise NotFoundError(f"Unable to find item with id: {item_id}")
    finally:
        sess.close()
    return render_template("add.html", form=form)


@app.route("/menu/delete/<item_id>", methods=["GET", "DELETE"])
@admin_only
def delete_menu_item(item_id):
    try:
        delete_item = sess.query(Menu).filter(Menu.id_menu_item == item_id).first()
        if current_user.id == 1 or delete_item.user_create == current_user.id:
            sess.query(Menu).filter(Menu.id_menu_item == item_id).delete()
            # If it was the only product in the Menu table, it can also be removed from the table MenuItem
            if not sess.query(Menu).filter(Menu.title_id == delete_item.title_id).first():
                sess.query(MenuItem).filter(MenuItem.id_item == delete_item.title_id).delete()
            sess.commit()
            return jsonify(menu={"Successfully delete the item with id:": item_id})
        else:
            return abort(403)
    except (exc.NoResultFound, AttributeError):
        raise NotFoundError(f"Unable to find item with id: {item_id}")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = sess.query(User).filter(User.email == email).first()
        if user and user.check_password(password):
            login_user(user, remember=form.remember.data)
            return redirect(url_for("home"))
        flash("Invalid email or password.", 'error')
        return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
