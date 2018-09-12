"""
Contains all database models and associated functions.
"""
from sqlalchemy import Boolean, Column, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class Book(Base):
    __tablename__ = 'book'
    isbn        = Column(String(250), primary_key=True)
    title       = Column(String(250), nullable=False)
    author      = Column(String(250), nullable=False)
    own         = Column(Boolean, default=True)
    want        = Column(Boolean, default=False)
    read        = Column(Boolean, default=False)
    location    = Column(String(250), nullable=True)

    def to_list(self):
        return [self.isbn, self.title, self.author,
                self.own, self.want, self.read,
                self.location]

    @classmethod
    def exists(cls, isbn, db):
        """Checks whether a `Book` with given ISBN exists.
        :param str isbn: The ISBN number of the book, must be a valid ISBN number.
        :param sqlalchemy.orm.session.Session db: An SQLAlchemy session.
        :return: The database entry or `None` if not found."""
        try:
            return db.query(cls).filter(cls.isbn == isbn).one()
        except NoResultFound:
            return None

    @classmethod
    def exists_author_title(cls, author, title, db):
        """Checks whether a `Book` with given author and title exists.
        :param str author: The author of the book.
        :param str title: The title of the book.
        :return: The database entry or `None` if not found."""
        try:
            return db.query(cls).filter(cls.title == title and cls.author == author).one()
        except NoResultFound:
            return None


def get_db(path):
    engine = create_engine('sqlite:///{}'.format(path))
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    db = DBSession()

    return db
