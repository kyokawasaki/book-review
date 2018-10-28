CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    author_id SERIAL NOT NULL REFERENCES authors(id)
);

CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR NOT NULL UNIQUE,
    password VARCHAR NOT NULL
);

CREATE TABLE reviews(
    id SERIAL PRIMARY KEY,
    score FLOAT NOT NULL,
    comment VARCHAR,
    user_id SERIAL NOT NULL REFERENCES users(id),
    book_id SERIAL NOT NULL REFERENCES books(id),
    UNIQUE (user_id, book_id),
    CHECK (score>=1 and score<=5)
);