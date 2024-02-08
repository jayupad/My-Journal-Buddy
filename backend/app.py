import os
import pymysql.cursors
import re
import hashlib

from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MySQL db connection credentials
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]
db_ip = os.environ["DB_IP"]

app.secret_key = "secret_key"

# app.config[
#     "SQLALCHEMY_DATABASE_URI"
# ] = "mysql+pymysql://{db_user}:{db_password}@{db_ip}/".format(
#     db_user=db_user, db_password=db_password, db_ip=db_ip
# )
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://{db_user}:{db_password}@{db_ip}/{db_name}".format(
    db_user=db_user, db_password=db_password, db_ip=db_ip, db_name=db_name
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# with app.app_context():
#     db.create_all()


class JournalEntry(db.Model):
    _tablename_ = "journal_entries"
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    favorited = db.Column(db.Boolean, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, default="", nullable=False)
    # owner = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Entry Name('{self.title}')"


class AccountEntry(db.Model):
    _tablename_ = "accounts"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return f"Entry Username('{self.username}')"


# Get
@app.route("/")
def index():
    # journal_entries = JournalEntry.query.all()
    journal_entries = JournalEntry.query.order_by(JournalEntry.datetime.desc()).all()
    return render_template("index.html", journal_entries=journal_entries)


@app.route("/favorites/")
def favorites():
    return


# Create Entry
@app.route("/create/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        favorite = request.form.get("favorite")

        journal_entry = JournalEntry(
            title=title, body=body, favorited=favorite is not None
        )
        db.session.add(journal_entry)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("create.html")


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
                    "SELECT * FROM account_entry WHERE username = %s", (username,)
                )
                account = cursor.fetchone()

            if account:
                msg = "Account already exists!"
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

                account_entry = AccountEntry(
                    username=username, password=password, email=email
                )
                db.session.add(account_entry)
                db.session.commit()
                msg = "You have successfully registered"
            # return redirect(url_for('login'))
        else:
            msg = "Please fill out the form!"

    return render_template("register.html", msg=msg)


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
                "SELECT * FROM account_entry WHERE username = %s AND password = %s",
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


@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    return redirect(url_for("login"))


if __name__ == "__main__":
    conn = pymysql.connect(host=db_ip, user=db_user, password=db_password)

    conn.cursor().execute("CREATE DATABASE IF NOT EXISTS testing")
    conn.commit()
    conn.cursor().close()
    conn.close()

    with app.app_context():
        db.create_all()

    app.run()
