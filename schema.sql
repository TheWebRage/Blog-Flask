DROP TABLE IF EXISTS Author;
DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS Category;


CREATE TABLE Author (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL
);

CREATE TABLE Post (
    Id integer primary key AUTOINCREMENT,
    Content varchar(600) NOT NULL,
    Title text NOT NULL,
    AuthorId integer NOT NULL,
    CategoryId integer NOT NULL,
    Foreign Key(AuthorId) References Author(Id),
    Foreign Key(CategoryId) REFERENCES Category(Id)
);

CREATE TABLE Category (
    Id integer primary key AUTOINCREMENT,
    Name text NOT NULL,
    Description text NOT NULL
);

CREATE TABLE user (
    id integer primary key AUTOINCREMENT,
    username text not null,
    password text not null
);