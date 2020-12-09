from flask import Flask, render_template, request, redirect, url_for, g, session
from db import get_db
from auth import login_required
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import abort
from flask import flash

app = Flask(__name__)
app.secret_key = 'Br1ckoven'


@app.before_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@app.route('/')
def index():
    db = get_db()
    categories = db.execute(
        "SELECT Name FROM Category ORDER BY Name DESC"
    ).fetchall()
    posts = db.execute(
        "SELECT Post.Title, Category.Name, Author.Name FROM Post "
        "JOIN Category ON Category.Id = Post.CategoryId "
        "JOIN Author ON Author.Id = Post.AuthorId"
    )
    return render_template('index.html', categories=categories, posts=posts)


@app.route('/browse')
def browse():
    db = get_db()
    categories = db.execute(
        "SELECT Name FROM Category ORDER BY Name DESC"
    ).fetchall()
    return render_template('browse.html', categories=categories)


@app.route('/category/<name>')
def category(name):
    db = get_db()

    category = db.execute(
        "SELECT Category.Name, Category.Description, Post.Id, Post.Title FROM Category"
        " LEFT JOIN Post ON Post.CategoryId = Category.Id"
        " WHERE Category.Name == ?"
        " ORDER BY Category.Name DESC", (name,)
    ).fetchall()
    return render_template('category.html', category=category, name=name)


@app.route('/posts') # TODO: add handlers to get the category or authors
def posts():
    db = get_db()
    posts = db.execute("SELECT Post.Id, Post.Title FROM Post").fetchall() # TODO: add date to view
    return render_template('list_post.html', posts=posts)


@app.route('/post/<int:id>')
def post(id):
    db = get_db()
    post = db.execute(
        "SELECT Post.Title, Author.Name, Post.Content FROM Post "
        "INNER JOIN Author ON Post.AuthorId = Author.Id WHERE Post.Id == ? ",
        (id,)
    ).fetchone()
    return render_template('post.html', post=post)


@app.route("/admin/<object>")
@login_required
def adminview(object):
    db = get_db()
    execute_string = "SELECT * FROM " + object.title()
    items = db.execute(execute_string).fetchall()

    return render_template('list_object.html', items=items, object=object)



@app.route("/admin/<object>/new", methods=("GET", "POST"))
@login_required
def admincreate(object):
    """Create a new post for the current user."""
    if request.method == "POST":

        db = get_db()
        execute_string = 'INSERT INTO ' + object.title()

        if object == 'post':
            execute_string += '(title, content, authorId, categoryId) VALUES ("' + request.form['title'] + '", "' + request.form["content"] + '", "' + request.form["authorid"] + '", "' + request.form["categoryid"] + '")'
        elif object == 'author':
            execute_string += '(name) VALUES ("' + request.form['name'] + '")'
        elif object == 'category':
            execute_string += '(name, description) VALUES ("' + request.form['name'] + '", "' + request.form["description"] + '")'

        db.execute(execute_string)
        db.commit()
        return redirect(url_for("adminview", object=object))

    return render_template("new.html", object=object, item={})


@app.route("/admin/<object>/<int:id>/edit", methods=("GET", "POST"))
@login_required
def adminedit(object, id):
    """Update a post if the current user is the author."""

    db = get_db()

    if request.method == "POST":
        execute_string = 'UPDATE ' + object.title() + " SET "

        if object == 'post':
            execute_string += 'title = "' + request.form['title'] + '", content = "' + request.form['content'] + '", authorId = ' + request.form["authorid"] + ', categoryId = ' + request.form["categoryid"] + ''
        elif object == 'author':
            execute_string += 'name = "' + request.form['name'] + '"'
        elif object == 'category':
            execute_string += 'name = "' + request.form['name'] + '", description = "' + request.form['description'] + '"'

        execute_string += " WHERE id = " + str(id)
        db.execute(execute_string)
        db.commit()
        return redirect(url_for("adminview", object=object))

    execute_string = "SELECT * FROM " + object.title() + " WHERE id = " + str(id)
    item = db.execute(execute_string).fetchone()

    return render_template("new.html", object=object, item=item)


@app.route("/admin/<object>/<int:id>/delete", methods=("POST", "GET"))
@login_required
def admindelete(object, id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    db = get_db()
    execute_str = 'DELETE FROM ' + object + ' WHERE id = ' + str(id)
    db.execute(execute_str)
    db.commit()
    return redirect(url_for("adminview", object=object))


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))

        return view(**kwargs)

    return wrapped_view


@app.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.
    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif (
            db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone()
            is not None
        ):
            error = "User " + username + " is already registered."

        if error is None:
            # the name is available, store it in the database and go to
            # the login page
            db.execute(
                "INSERT INTO user (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
            return redirect(url_for("login"))

        flash(error)

    return render_template("auth/register.html")


@app.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@app.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))