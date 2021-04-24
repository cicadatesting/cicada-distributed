CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name varchar(255),
    age INTEGER,
    email varchar(255),
    CONSTRAINT unique_email UNIQUE (email)
)
