import os
import pymysql.cursors
import re
import hashlib
import json

from datetime import timedelta, datetime, timezone
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy import exc
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    JWTManager,
    get_current_user,
    current_user,
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MySQL db connection credentials
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]
db_ip = os.environ["DB_IP"]
secret_key = os.environ["SECRET_KEY"]
jwt_secret_key = os.environ["JWT_SECRET_KEY"]
jwt_access_token_expiry = int(os.environ["JWT_ACCESS_TOKEN_EXPIRY"])
jwt_refresh_token_expiry = int(os.environ["JWT_REFRESH_TOKEN_EXPIRY"])

# Flask Config
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql+pymysql://{db_user}:{db_password}@{db_ip}/{db_name}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secret_key
app.config["JWT_SECRET_KEY"] = jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=jwt_access_token_expiry)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=jwt_refresh_token_expiry)


db = SQLAlchemy(app)
jwt = JWTManager(app)


def hash(password):
    hash = password + app.secret_key
    hash = hashlib.sha1(hash.encode())
    password = hash.hexdigest()
    return password


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    entries = db.relationship("Entry")

    def checkPassword(self, password):
        if self.password == hash(password):
            return True

        return False

    def __repr__(self):
        return f"User: {self.username}; ID: {self.id}"


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    favorited = db.Column(db.Boolean, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, default="", nullable=False)
    datetime = db.Column(db.DateTime(timezone=True), default=datetime.now().date())
    mood = db.Column(db.Integer, nullable=True, default=-1)
    lock = db.Column(db.Boolean, nullable=False, default=False)
    __table_args__ = (
        UniqueConstraint("owner_id", "datetime", name="_owner_datetime_uc"),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return (
            f"Entry: {self.title}; OwnerID: {self.owner_id}; Created: {self.datetime}"
        )


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    type = db.Column(db.String(16), nullable=False)
    user_id = db.Column(
        db.ForeignKey("user.id"), default=lambda: get_current_user().id, nullable=False
    )
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)


@app.route("/")
def index():
    return "🤯"


# JWT callback functions
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    # JWK created using username
    return User.query.filter_by(username=identity).one_or_none()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None


# Auth API
@app.route("/api/auth/register/", methods=["POST"])
def register_api():
    data = json.loads(request.data)
    # print(data)
    if "username" in data and "password" in data and "email" in data:
        username = data["username"]
        password = data["password"]
        email = data["email"]

        new_user = User(username=username, password=hash(password), email=email)

        if (
            User.query.filter_by(username=username).one_or_none()
            or User.query.filter_by(email=email).one_or_none()
        ):
            return jsonify({"msg": "Account or email already exists!"}), 400

        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"msg": "Invalid email address!"}), 400

        elif not re.match(r"[A-Za-z0-9]+", username):
            return jsonify(
                {"msg": "Username must contain only characters and numbers!"}
            ), 400

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"msg": "You have successfully registered"}), 201

    return jsonify({"msg": "Please fill out the form!"}), 400


@app.route("/api/auth/login/", methods=["POST"])
def login_api():
    data = json.loads(request.data)
    # print(data)
    if "username" in data and "password" in data:
        username = data["username"]
        password = data["password"]

        user = User.query.filter_by(username=username).one_or_none()
        # print(user.checkPassword(password))

        if user.checkPassword(password):
            access_token = create_access_token(identity=username, fresh=True)
            refresh_token = create_refresh_token(identity=username)
            return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    return jsonify({"msg": "Incorrect username/password"}), 401


@app.route("/api/auth/logout", methods=["DELETE"])
@jwt_required(verify_type=False)
def modify_token():
    token = get_jwt()
    jti = token["jti"]
    ttype = token["type"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, type=ttype, created_at=now))
    db.session.commit()
    return jsonify(msg=f"{ttype.capitalize()} token successfully revoked"), 204


@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_api():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify(access_token=access_token), 201


# Entries API
@app.route("/api/entries/", methods=["POST"])
@jwt_required(fresh=True)
# We have fresh set to true b/c we want the user to re-auth after first expiry to modify entries
# Other routes that don't have fresh set to true allows refreshed keys b/c they are read only
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

    try:
        db.session.commit()

    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Entry for today already exists"}), 400

    return jsonify({"msg": "Entry creation successful"}), 201


@app.route("/api/entries/<id>", methods=["PUT"])
@jwt_required(fresh=True)
# We have fresh set to true b/c we want the user to re-auth after first expiry to modify entries
# Other routes that don't have fresh set to true allows refreshed keys b/c they are read only
def edit_entry(id):
    entry = Entry.query.filter_by(id=id).one_or_none()
    if entry:
        if entry.owner_id == current_user.id:
            if not entry.lock:
                data = json.loads(request.data)

                title = data["title"]
                body = data["body"]
                favorite = data.get("favorite")
                lock = data.get("lock")

                entry.title = title
                entry.body = body
                entry.favorite = favorite
                entry.lock = lock

                if lock:
                    entry.mood = 8
                    pass #call LLM and update values

                db.session.commit()

                return jsonify({"msg": "Entry successfully edited"}), 200
            return jsonify({"msg" : "You have already locked this entry"}), 403
        return jsonify({"msg": "Unauthorized access!"}), 401
    return jsonify({"msg": "Entry does not exist!"}), 404


@app.route("/api/entries/", methods=["GET"])
@jwt_required()
def get_user_entries():
    entries = (
        Entry.query.filter_by(owner_id=current_user.id)
        .order_by(Entry.datetime.desc())
        .all()
    )
    entry_data = [entry.to_dict() for entry in entries]
    return json.dumps(entry_data, default=str), 200


@app.route("/api/entries/<id>", methods=["DELETE"])
@jwt_required(fresh=True)
def delete_user_entries(id):
    entry = Entry.query.filter_by(id=id).one_or_none()
    if entry:
        # print("Requested ID is " + id)
        # print("Entry ID " + str(entry.owner_id))
        # print("Authenticated user ID " + str(current_user.id))
        if entry.owner_id == current_user.id:
            Entry.query.filter_by(id=id).delete()
            db.session.commit()
            return jsonify({"msg": "Entry successfully deleted"}), 204
        return jsonify({"msg": "Unauthorized access!"}), 401

    return jsonify({"msg": "Entry does not exist!"}), 404


@app.route("/api/entries/<date>", methods=["GET"])
@jwt_required()
def get_user_entries_by_date(date):
    entry = (
        Entry.query.filter_by(owner_id=current_user.id)
        .filter(Entry.datetime == date)
        .one_or_none()
    )
    if entry:
        return json.dumps(entry.to_dict(), default=str), 200
    return json.dumps({"msg": "Entry does not exist"}), 404


# Search API
@app.route("/api/search/", methods=["GET"])
@jwt_required()
# date format should be YYYY-MM-DD
def search_entries():
    data = json.loads(request.data)
    start_date = data["start_date"]
    end_date = data["end_date"]

    entries = (
        Entry.query.filter_by(owner_id=current_user.id)
        .filter(Entry.datetime >= start_date, Entry.datetime < end_date)
        .order_by(Entry.datetime.desc())
    )

    entry_data = [entry.to_dict() for entry in entries]
    return json.dumps(entry_data, default=str), 200


def initDB():
    conn = pymysql.connect(host=db_ip, user=db_user, password=db_password)
    if input("Drop DB and recreate? Y or [N] : ").upper() == "Y":
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
