import os
import requests

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/books")
def books():
    books = db.execute("""SELECT books.id, books.isbn, books.title, authors.name FROM books JOIN authors
        ON (books.author_id = authors.id)""").fetchall()
    return render_template("books.html", books=books)

@app.route("/books/<int:book_id>", methods=['GET', 'POST'])
def book(book_id):
    if session.get("user") is None:
        return render_template("error.html", message="Please login to access the books section")

    book = db.execute("""SELECT books.id, books.isbn, books.title, books.year, authors.name FROM books
        JOIN authors ON (books.author_id = authors.id) WHERE books.id = :book_id""",
        {"book_id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="Invalid book id.")

    api = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": "QsukmixisgSsVGiBVGJH3Q",
        "isbns": book[1]})

    reviews = db.execute("""SELECT reviews.score, reviews.comment, users.username FROM reviews JOIN users ON
        (user_id = users.id) WHERE book_id = :book_id""", {"book_id": book_id})
        
    return render_template("book.html", book=book, reviews=reviews, api=api.json())

@app.route("/api/<string:book_isbn>")
def api(book_isbn):
    book = db.execute("""SELECT books.title, books.isbn, books.year, authors.name FROM books
        JOIN authors ON (books.author_id = authors.id) WHERE books.isbn = :book_isbn""",
        {"book_isbn": book_isbn}).fetchone()
    request = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "QsukmixisgSsVGiBVGJH3Q", "isbns": book_isbn})

    api = {
        "title": book[0],
        "isbn": book[1],
        "year": book[2],
        "author": book[3],
        "review_count": request.json()["books"][0]["ratings_count"],
        "average_score": request.json()["books"][0]["average_rating"]
    }

    return jsonify(api)

@app.route("/review", methods=['POST'])
def review():
    score = request.form.get("score")
    comment = request.form.get("comment")
    book_id = request.form.get("book")
    user = session.get("user")

    if user is None:
        return render_template("error.html", message="Please login before submitting a review")

    user_id = db.execute("SELECT id FROM users WHERE username = :username", {"username": user}).fetchone()

    if score is None or comment == "":
        return render_template("error.html", message="Please fill out all the fields before submitting")
    
    try:
        db.execute("""INSERT INTO reviews (score, comment, user_id, book_id)
            VALUES (:score, :comment, :user_id, :book_id)""",
            {"score": score, "comment": comment, "user_id": user_id[0], "book_id": book_id})
        db.commit()
    except:
        return render_template("error.html", message="Something went wrong!")
    
    return redirect("/books/" + book_id)

@app.route("/search")
def search():
    if session.get("user") is None:
        return render_template("error.html", message="Please login to be able to search for books")

    query = request.args.get("search")
    books = []

    if query is not None and query != "":
        books = db.execute("""SELECT books.id, books.isbn, books.title, authors.name 
            FROM books JOIN authors ON (books.author_id = authors.id) WHERE
            LOWER(isbn) LIKE LOWER(:query) OR LOWER(title) LIKE LOWER(:query)
            OR LOWER(authors.name) LIKE LOWER(:query)""",
            {"query": '%' + query + '%'}).fetchall() 

    return render_template("search.html", books=books)

@app.route("/user", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        username_available = db.execute("SELECT * FROM users WHERE username = :username",
            {"username": username}).rowcount == 0
        
        if (username_available):
            db.execute("INSERT INTO users (email, username, password) VALUES (:email, :username, :password)",
                {"email": email, "username": username, "password": password})
            db.commit()
            return render_template("success.html", message="User registered with success!")
        
        return render_template("error.html", message="User already exists.")

    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get("user") is None:
        session["user"] = None

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        db_password = db.execute("SELECT password FROM users WHERE username = :username",
            {"username": username}).fetchone()
        
        if (db_password != None):
            check = check_password_hash(db_password[0], password)
            if (check):
                session["user"] = username
                return render_template("success.html", message="Login realized with success")
        
        return render_template("error.html", message="Username and/or password are incorrect. Please try again.")

    return render_template("login.html", user=session["user"])

@app.route("/logout")
def logout():
    if session.get("user") is None:
        return redirect("/login")
    
    session["user"] = None
    return render_template("success.html", message="Logout realized with success.")