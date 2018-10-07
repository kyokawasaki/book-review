import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.DictReader(f)
    for book in reader:
        author_id = db.execute("SELECT id FROM authors WHERE name = :author",  {"author": book["author"]}).fetchone()
        print (author_id)
        if author_id == None:
            author_id = db.execute("INSERT INTO authors (name) VALUES (:author) RETURNING id", {"author": book["author"]}).fetchone()
            print(author_id["id"])

        db.execute("INSERT INTO books (isbn, title, year, author_id) VALUES (:isbn, :title, :year, :author_id)",
            {"isbn": book["isbn"], "title": book["title"], "year": book["year"], "author_id": author_id["id"]})

    db.commit()

if __name__ == "__main__":
    main()
