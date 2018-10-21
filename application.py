import os

from flask import Flask, session, render_template, request, redirect
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

@app.route("/search")
def search():
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