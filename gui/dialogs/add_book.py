import gi
import requests
gi.require_version('Gtk', '3.0')
from exc import InvalidISBNError, NoResultsError
from gi.repository import Gdk, Gtk
from gi.repository.GdkPixbuf import Pixbuf
from model import Book
from provider import Identifier, OpenLibrary


class AddBookHandler(object):
    def __init__(self, db, parent):
        self.builder            = Gtk.Builder()
        self.builder.add_from_file('./gui/dialogs/add_book.glade')
        self.dialog             = self.builder.get_object('dialog_add_book')
        self.lbl_message        = self.builder.get_object('lbl_message')
        self.lbl_manual_message = self.builder.get_object('lbl_manual_message')
        self.added_book         = None
        self.identifier         = Identifier.ISBN
        self.is_new             = False
        self.current_entry      = None
        self.current_page       = 'SEARCH'
        self.result             = None
        self.ol                 = OpenLibrary()
        self.db                 = db

        self.dialog.set_transient_for(parent)

        self.tv_results = self.builder.get_object('treeview_results')
        render_text     = Gtk.CellRendererText(width_chars=150, wrap_width=150)
        self.tv_results.append_column(Gtk.TreeViewColumn('Title', render_text,
                                                         text=0))
        self.tv_results.append_column(Gtk.TreeViewColumn('Author', render_text,
                                                         text=1))

        self.lbl_message.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('red'))
        self.lbl_manual_message.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('red'))
        self.builder.connect_signals(self)

    def _add_book(self):
        if self.current_page == 'SEARCH':
            if self.current_entry:
                self.added_book = self.current_entry.to_book(self.current_entry.isbns[0])
                if not Book.exists(self.added_book.isbn, self.db):
                    self.db.add(self.added_book)
                    self.is_new = True
                self.dialog.close()
            else:
                self._show_message(
                    'You need to select a book to add to the library.')
        elif self.current_page == 'MANUAL':
            isbn    = self.builder.get_object('entry_isbn').get_text().strip()
            title   = self.builder.get_object('entry_title').get_text().strip()
            author  = self.builder.get_object('entry_author').get_text().strip()
            own     = self.builder.get_object('chk_own').get_active()
            want    = self.builder.get_object('chk_want').get_active()
            read    = self.builder.get_object('chk_read').get_active()

            if not title:
                self.lbl_manual_message.set_text('Please enter a title.')
                return
            elif not author:
                self.lbl_manual_message.set_text('Please enter an author.')
                return

            self.added_book = Book(isbn=isbn, title=title, author=author,
                                   own=own, want=want, read=read)
            if ((isbn != '' and not Book.exists(isbn, self.db)) or
                    not Book.exists_author_title(author, title, self.db)):
                self.db.add(self.added_book)
                self.is_new = True
            self.dialog.close()

    def _has_query(self, entry):
        if entry.get_text().strip() == '':
            self._show_message('Please enter a search query.')
            return False
        else:
            self.lbl_message.hide()
            return True

    def _show_message(self, msg):
        self.lbl_message.set_text(msg)
        self.lbl_message.show()

    def _search_by_isbn(self, entry):
        isbn = entry.get_text().strip()
        try:
            book                = self.ol.isbn_search(isbn)
            self.current_entry  = book
            store               = self.builder.get_object('resultstore')
            store.clear()
            store.append([book.title, book.author])
            self.tv_results.set_cursor(Gtk.TreePath.new_from_indices([0]))
            self._set_result_entry(book)
            self.lbl_message.hide()
        except InvalidISBNError as e:
            self._show_message(str(e))

    def _search_by_query(self, entry, identifier):
        query = entry.get_text().strip()
        try:
            self.result = self.ol.query_search(query, identifier)
            store       = self.builder.get_object('resultstore')
            store.clear()
            for r in self.result.results:
                store.append([r.title, r.author])
            self.lbl_message.hide()
        except NoResultsError as e:
            self._show_message(str(e))

    def _search(self, entry_search):
        if self._has_query(entry_search):
            if self.identifier == Identifier.ISBN:
                self._search_by_isbn(entry_search)
            else:
                self._search_by_query(entry_search, self.identifier)

    def _set_result_entry(self, entry):
        self._set_result(entry.isbns[0], entry.title, entry.author)

    def _set_result(self, isbn, title, author, cover=None):
        tbl_result  = self.builder.get_object('table_result')
        lbl_details = self.builder.get_object('lbl_book_details')
        img_cover   = self.builder.get_object('img_cover')

        lbl_details.set_text('{}\n{}\n{}'.format(isbn, title, author))
        if cover:
            r       = requests.get(cover, stream=True)    # load cover from web
            with open('cover.jpg', 'wb') as img:
                for chunk in r:
                    img.write(chunk)
            pb      = Pixbuf.new_from_file('cover.jpg')
            img_cover.set_from_pixbuf(pb)
        tbl_result.show()

    def on_notebook_switch_page(self, notebook, page, page_num):
        if page_num == 0:
            self.current_page = 'SEARCH'
        elif page_num == 1:
            self.current_page = 'MANUAL'

    def on_btn_add_clicked(self, btn_add):
        self._add_book()

    def on_btn_cancel_clicked(self, btn_cancel):
        self.dialog.close()

    def on_btn_search_clicked(self, entry_search):
        self._search(entry_search)

    def on_cmbbx_identifier_changed(self, cmbbx_identifier):
        # @TODO: There's a cleaner way than those ifs
        model       = cmbbx_identifier.get_model()
        selected    = model[cmbbx_identifier.get_active_iter()][0]
        if selected == 'ISBN':
            self.identifier = Identifier.ISBN
        elif selected == 'Title':
            self.identifier = Identifier.TITLE
        elif selected == 'Author':
            self.identifier = Identifier.AUTHOR

    def on_entry_search_activate(self, entry_search):
        self._search(entry_search)

    def on_treeview_results_cursor_changed(self, tv):
        if self.result:
            path, col       = tv.get_cursor()
            self.current_entry  = self.result.results[path.get_indices()[0]]
            self._set_result_entry(self.current_entry)

    def on_treeview_results_row_activated(self, tv, path, column):
        self._add_book()
