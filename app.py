from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import string, random

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///url.db"
app.config["SECRET_KEY"] = "aim_club"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(400), nullable=False)
    short_url = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password=password)

        user = User.query.filter_by(username=username).first()

        if not user:
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            session["user"] = new_user.id
            flash("User Registered Successfully", "success")
            return redirect("/")
        else:
            flash("User Already Exists, Try To Log In", "warning")
            return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                session["user"] = user.id
                flash("Logged In", "success")
                return redirect("/")
            else:
                flash("Wrong Password, Try Again", "warning")
                return redirect("/login")
        else:
            flash("User Does Not Exists, Try To Register", "warning")
            return redirect("/register")

    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user")
    flash("Logged Out", "success")
    return redirect("/login")


def generate_short_url(slug):
    chars = string.ascii_letters + string.digits

    if slug:
        return slug

    return "".join(random.choices(chars, k=5))


@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        flash("You Have To Log In To Access This Page", "warning")
        return redirect("/login")
    if request.method == "POST":
        long_url = request.form.get("long_url")
        slug = request.form.get("slug")

        if slug:
            slug_exist = Url.query.filter_by(short_url=slug).first()

            if not slug_exist:
                flash("Custom Url Created", "success")
                short_url = generate_short_url(slug)
            else:
                flash("Slug Already Exist, Random Url Created", "success")
                short_url = generate_short_url("")
        else:
            flash("Random Url Created", "success")
            short_url = generate_short_url("")

        new_url = Url(long_url=long_url, short_url=short_url, user_id=session["user"])

        db.session.add(new_url)
        db.session.commit()
        return redirect("/")

    all_urls = Url.query.filter_by(user_id=session["user"])
    user = User.query.filter_by(id=session["user"]).first()
    return render_template("index.html", all_urls=all_urls, user=user)


@app.route("/<short_url>")
def redirect_url(short_url):
    url = Url.query.filter_by(short_url=short_url).first()

    if url:
        flash("Url Opened In New Tab", "success")
        return redirect(url.long_url)

    flash("URL NOT FOUND", "warning")
    return "URL NOT FOUND", 404


@app.route("/delete/<int:url_id>")
def delete_url(url_id):
    if "user" not in session:
        flash("You Have To Log In To Delete Url", "warning")
        return redirect("/login")

    url = Url.query.filter_by(id=url_id).first()

    if url:
        if url.user_id == session["user"]:
            db.session.delete(url)
            db.session.commit()
            flash("Url Deleted", "success")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
