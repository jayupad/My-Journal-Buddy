import os
import pymysql.cursors
import re
import hashlib
import json

from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from dotenv import load_dotenv

from flask_jwt_extended import create_access_token, jwt_required, JWTManager, current_user

load_dotenv()

app = Flask(__name__)

# MySQL db connection credentials
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]
db_ip = os.environ["DB_IP"]


app.secret_key = "secret_key"

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://{db_user}:{db_password}@{db_ip}/{db_name}".format(
    db_user=db_user, db_password=db_password, db_ip=db_ip, db_name=db_name
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = "secret_key"

jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    entries = db.relationship("Entry")

    def __repr__(self):
        return f"User: {self.username}; ID: {self.id}"


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    favorited = db.Column(db.Boolean, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, default="", nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return (
            f"Entry: {self.title}; OwnerID: {self.owner_id}; Created: {self.datetime}"
        )


@app.route("/")
def index():
    # entry = entry.query.all()
    entries = Entry.query.order_by(Entry.datetime.desc()).all()
    # print(entries)
    return render_template("index.html", entries=entries)


# Template for register (Testing)
@app.route("/register/", methods=("GET", "POST"))
def register():
    msg = ""
    if request.method == "POST":
        if (
            "username" in request.form
            and "password" in request.form
            and "email" in request.form
        ):
            username = request.form["username"]
            password = request.form["password"]
            email = request.form["email"]

            connection = pymysql.connect(
                host=db_ip,
                user=db_user,
                password=db_password,
                db=db_name,
                cursorclass=pymysql.cursors.DictCursor,
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM user WHERE username = %s OR email = %s",
                    (username, email),
                )
                account = cursor.fetchone()

            if account:
                msg = "Account or email already exists!"
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                msg = "Invalid email address!"
            elif not re.match(r"[A-Za-z0-9]+", username):
                msg = "Username must contain only characters and numbers!"
            # elif not username or not password or not email:
            #     msg = 'Please fill out the form!'
            else:
                # Hash the password
                hash = password + app.secret_key
                hash = hashlib.sha1(hash.encode())
                password = hash.hexdigest()

                user = User(username=username, password=password, email=email)
                db.session.add(user)
                db.session.commit()
                msg = "You have successfully registered"
            # return redirect(url_for('login'))
        else:
            msg = "Please fill out the form!"

    return render_template("register.html", msg=msg)


# Template for login (testing)
@app.route("/login/", methods=("GET", "POST"))
def login():
    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        connection = pymysql.connect(
            host=db_ip,
            user=db_user,
            password=db_password,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user WHERE username = %s AND password = %s",
                (
                    username,
                    password,
                ),
            )
            account = cursor.fetchone()

        if account:
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            return redirect(url_for("index"))
        else:
            msg = "Incorrect username/password!"
    return render_template("login.html", msg=msg)


# unused?
@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    return redirect(url_for("login"))


# Template for creating entries (will always have owner id of 1)
@app.route("/create/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        favorite = request.form.get("favorite")

        entry = Entry(
            title=title, body=body, favorited=favorite is not None, owner_id=1
        )
        db.session.add(entry)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("create.html")


#JWT callback functions
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).one_or_none() # JWK created using username

# Api Routes
@app.route("/api/entry/create/", methods=("POST",))
@jwt_required()
def create_entry():
    # print(current_user)

    data = json.loads(request.data)
    title = data["title"]
    body = data["body"]
    favorite = data.get("favorite")
    owner = current_user.id

    entry = Entry(
        title=title, body=body, favorited=favorite is not None, owner_id=owner
    )
    db.session.add(entry)
    db.session.commit()

    return "", 200


@app.route("/api/register/", methods=("POST",))
def register_api():
    data = json.loads(request.data)
    # print(data)
    if "username" in data and "password" in data and "email" in data:
        username = data["username"]
        password = data["password"]
        email = data["email"]

        connection = pymysql.connect(
            host=db_ip,
            user=db_user,
            password=db_password,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user WHERE username = %s OR email = %s",
                (username, email),
            )
            account = cursor.fetchone()

        if account:
            msg = (False, "Account or email already exists!")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = (False, "Invalid email address!")
        elif not re.match(r"[A-Za-z0-9]+", username):
            msg = (False, "Username must contain only characters and numbers!")
        # elif not username or not password or not email:
        #     msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()

            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            msg = (True, "You have successfully registered")
        # return redirect(url_for('login'))
    else:
        msg = (False, "Please fill out the form!")

    return (msg[1], 200) if msg[0] else (msg[1], 400)


@app.route("/api/login/", methods=("POST",))
def login_api():
    data = json.loads(request.data)
    print(data)
    if "username" in data and "password" in data:
        username = data["username"]
        password = data["password"]

        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        connection = pymysql.connect(
            host=db_ip,
            user=db_user,
            password=db_password,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user WHERE username = %s AND password = %s",
                (
                    username,
                    password,
                ),
            )
            account = cursor.fetchone()

        if account:
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            # msg = (True, "Login Success")
            # return redirect(url_for("index"))
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            # msg = (False, "Incorrect username/password!")
            return jsonify({"msg":"Incorrect username/password"}), 401
    
    # return (msg[1], 200) if msg[0] else (msg[1], 401)

# TODO: ummmm, refine how this works + pathing
@app.route("/api/entry/<username>")
@jwt_required()
def get_user_entries(username):
    if username != current_user.username:
        return jsonify({"msg":"Unauthorized access!"}), 401
    entries = Entry.query.filter_by(owner_id=current_user.id).order_by(Entry.datetime.desc()).all()
    print(entries)
    # return json.dumps(entries), 200
    return render_template("index.html", entries=entries)

# Testing Routes
def initDB():
    conn = pymysql.connect(host=db_ip, user=db_user, password=db_password)
    if (input("Drop DB and recreate? Y or [N] : ").upper() == "Y"):
        conn.cursor().execute("DROP DATABASE testing")
        conn.commit()

    conn.cursor().execute("CREATE DATABASE IF NOT EXISTS testing")
    conn.commit()
    conn.cursor().close()
    conn.close()

    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    initDB()
    app.run()
