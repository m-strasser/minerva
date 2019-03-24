import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
import model
import sys
from gi.repository import Gdk, Gtk
from gui.booklist import BookList
from gui.dialogs.add_book import AddBookHandler
from utils import read_config_file


class Minerva(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = read_config_file()
        self.db     = model.get_db(self.config['db_path'])
        self.books  = []
        for book in self.db.query(model.Book).all():
            self.books.append(book)

        builder             = Gtk.Builder()
        builder.add_from_file('./gui/minerva.glade')
        self.window         = builder.get_object('minerva_main')
        self.vbox           = builder.get_object('vbox')
        self.tv_filters     = builder.get_object('tv_filters')
        self.statusbar      = builder.get_object('statusbar')
        self.btn_edit       = builder.get_object('btn_edit')
        self.btn_delete     = builder.get_object('btn_delete')
        self.books          = BookList(parent=self, books=self.books)
        self.filters        = Gtk.ListStore(str)
        self.info_bar       = Gtk.InfoBar(no_show_all=True)
        self.info_msg       = Gtk.Label('')
        self.info_ok_btn    = self.info_bar.add_button('OK', Gtk.ResponseType.OK)
        self.search_entry   = Gtk.SearchEntry()

        content_area        = self.info_bar.get_content_area()
        content_area.add(self.info_msg)
        self.info_bar.connect('response', self.on_info_bar_response)
        self.info_bar.hide()
        self.info_msg.show()

        self._setup_filters(self.filters, self.tv_filters)
        builder.get_object('hpaned').pack2(self.books)
        builder.get_object('hbox').pack_start(self.search_entry, True, True, 0)
        builder.connect_signals(self)

        self.vbox.pack_end(self.info_bar, False, True, 0)
        self.search_entry.connect('search-changed', self.on_search_changed)
        self.window.connect('key-press-event', self.on_key_press_event)

    def _setup_filters(self, store, view):
        store.append(['All'])
        store.append(['Books I own'])
        store.append(['Books I\'ve read'])

        text = Gtk.CellRendererText()
        view.set_model(self.filters)
        view.append_column(Gtk.TreeViewColumn('Filter', text, text=0))

    def _show_message(self, message):
        self.info_msg.set_text(message)
        self.info_bar.show()
        self.info_ok_btn.grab_focus()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        self.window.set_application(self)
        self.window.present()
        self.window.show_all()
        self.search_entry.grab_focus()
        self.window.connect('delete-event', self.on_quit)

    def on_add_book_dialog_close(self, dialog):
        if self.add_book_handler.added_book and not self.add_book_handler.is_new:
            self._show_message('"{}" is already in your library'.format(
                self.add_book_handler.added_book.title))
        elif self.add_book_handler.added_book:
            self.books.append(self.add_book_handler.added_book)
            self.db.add(self.add_book_handler.added_book)
            self.db.commit()

    def on_btn_add_book_clicked(self, button):
        self.add_book_handler = AddBookHandler(self.db, self.window)
        self.add_book_handler.dialog.connect('destroy', self.on_add_book_dialog_close)
        self.add_book_handler.dialog.show_all()

    def on_btn_edit_clicked(self, button):
        pass

    def on_btn_delete_clicked(self, button):
        if self.selected_book:
            dialog = Gtk.MessageDialog(
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.YES_NO,
                message_format="Are you sure you want to delete '{}'?".format(
                    self.selected_book.title
                )
            )
            response = dialog.run()

            if response == Gtk.ResponseType.YES:
                self.db.delete(self.books.selected_book)
                self.db.commit()
                self.books.remove_selected()
            else:
                pass

            dialog.destroy()

    def on_info_bar_response(self, info_bar, response_id):
        info_bar.hide()

    def on_key_press_event(self, widget, event):
        if not self.books.editing:
            search_event = self.search_entry.handle_event(event)
            if search_event != Gdk.EVENT_STOP:
                if event.keyval == Gdk.KEY_Control_L:
                    self.search_entry.grab_focus_without_selecting()
            return search_event

    def on_search_changed(self, search_entry):
        self.books.search(search_entry.get_text().strip())

    def set_active_book(self, book):
        if not book:
            self.selected_book = None
            self.statusbar.push(
                self.statusbar.get_context_id('Selected book'),
                "Error fetching book information from the database!"
            )

            self.btn_edit.hide()
            self.btn_delete.hide()
        else:
            self.selected_book = book
            self.statusbar.push(
                self.statusbar.get_context_id('Selected book'),
                '"{}" by {}'.format(book.title, book.author)
            )

            self.btn_edit.show()
            self.btn_delete.show()


if __name__ == '__main__':
    app = Minerva()
    app.run(sys.argv)
