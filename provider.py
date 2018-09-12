import isbnlib
import requests

from enum import Enum
from exc import InvalidISBNError, NoResultsError
from model import Book
from urllib.parse import quote_plus


class Identifier(Enum):
    ISBN    = 'isbn'
    TITLE   = 'title'
    AUTHOR  = 'author'


class Entry(object):
    """A single search result."""
    def __init__(self, isbns, title, author, covers=None):
        self.isbns  = isbns
        self.title  = title
        self.author = author
        self.covers = covers

    def __repr__(self):
        return '{} - {}'.format(self.author, self.title)

    def to_book(self, isbn):
        """Convert the entry into a `model.Book`.
        :param str isbn: The ISBN number of the actual book."""
        return Book(isbn=isbn, title=self.title, author=self.author,
                    own=True, want=False, read=False)

    def to_list(self):
        """Convert the entry into a list (for e.g. a Gtk.TreeView)."""
        return [self.isbns[0], self.title, self.author,
                self.own, self.want, self.read]


class Result(object):
    """A generic API result class."""
    def __init__(self, start, num_found, page, results):
        self.start = start
        self.num_found = num_found
        self.page = page
        self.results = results


class OpenLibrary(object):
    """Provides access to the Open Library API."""

    class Entry(Entry):
        """Handles entries from the Open Library API."""
        @classmethod
        def parse(cls, raw):
            if 'author_name' in raw.keys():
                author  = raw['author_name'][0]
            elif 'authors' in raw.keys():
                author  = raw['authors'][0]['name']
            else:
                author  = 'Unknown'
            isbns   = raw['isbn'] if 'isbn' in raw.keys() else None
            covers  = raw['cover'] if 'cover' in raw.keys() else None
            return cls(isbns=isbns, title=raw['title'], author=author, covers=covers)

    class Result(Result):
        """Handles results from the Open Library API."""
        @classmethod
        def parse_json(cls, raw):
            """Parses Open Library JSON responses into a SearchResult.
            :param str raw: The raw JSON data.
            :return: A `SearchResult` containing the parsed data."""
            start = raw['start']
            num_found = raw['num_found']
            page = 0
            results = []

            for r in raw['docs']:
                results.append(OpenLibrary.Entry.parse(r))
            return cls(start=start, num_found=num_found, page=page, results=results)

    def __init__(self, base_url='https://openlibrary.org/'):
        """Initializes the instance.
        :param str base_url: The URL pointing to the Open Library instance
        (expects a trailing slash).
        """
        self.base_url = base_url

    def isbn_search(self, isbn):
        """Search for a book by its ISBN number.
        :param str isbn: The ISBN number of the book.
        :raises minerva.exc.InvalidISBNError: If `isbn` is not convertible to a valid
        ISBN-13 number.
        :raises minerva.exc.NoResultsError: If Open Library does not have an entry with
        ISBN `isbn`.
        :return: A `Book` containing the retrieved data.
        :rtype: OpenLibrary.Entry"""
        isbn13 = isbnlib.to_isbn13(isbn)
        if isbn13 is None: raise InvalidISBNError(isbn + ' is not a valid ISBN number.')
        r = requests.get(
            self.base_url + 'api/books?bibkeys=ISBN:' + isbn13 + '&jscmd=data&format=json'
        )
        if len(r.json()) > 0:
            data        = r.json()['ISBN:{}'.format(isbn13)]
            entry       = OpenLibrary.Entry.parse(data)
            entry.isbns = [isbn13]
            return entry
        else:
            raise NoResultsError('No book was found with the ISBN ' + isbn)

    def query_search(self, query, identifier):
        """Search for books by querying an identifier.
        Queries the Open Library API for the given query. This is equivalent to calling
        '/search.json?identifier=query'.
        :param str query: The query to search for.
        :param model.Identifier identifier: The identifier to query by
        (except Identifier.ISBN).
        :raises minerva.exc.NoResultsError: If the number of returned results is 0.
        :return: The retrieved results.
        :rtype: OpenLibrary.Result
        """
        url = self.base_url + 'search.json?' + identifier.value + '=' + quote_plus(query)
        r = requests.get(url)
        if r.status_code == 200 and len(r.json()) > 0:
            return OpenLibrary.Result.parse_json(r.json())
        else: raise NoResultsError('No book was found with the ' + identifier + query)

    def get_cover(self, entry, size='M'):
        """Retrieve the URL for the cover of the given entry.
        :param provider.Entry entry: The entry that identifies the book.
        :param str size: The size of the cover image ('S', 'M' or 'L').
        :return: The generated URL."""
        # @TODO: Is oclc better than isbn?
        return 'https://covers.openlibrary.org/b/ISBN/{}-{}.jpg'.format(
            entry.isbns[0], size)
