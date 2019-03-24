import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from model import Book


class BookList(Gtk.ScrolledWindow):
    ISBN = 0
    TITLE = 1
    AUTHOR = 2

    def __init__(self, parent, books):
        super(BookList, self).__init__()
        self.parent = parent
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.add(self._setup_view(books))
        select = self.tree_view.get_selection()
        select.connect('changed', self.on_selection_changed)

    def _setup_view(self, books):
        """Populate ListStore and add a filter."""
        self.data = Gtk.ListStore(str, str, str, bool, bool, bool, str)

        for b in books:
            self.data.append(b.to_list())

        self.filter_by = None
        self.filter = self.data.filter_new()
        self.filter.set_visible_func(self._filter_data_func)
        self.tree_view = Gtk.TreeView.new_with_model(self.filter)

        self.isbn_renderer      = Gtk.CellRendererText(editable=True)
        self.title_renderer     = Gtk.CellRendererText(editable=True)
        self.author_renderer    = Gtk.CellRendererText(editable=True)

        self.tree_view.append_column(
            Gtk.TreeViewColumn('ISBN', self.isbn_renderer, text=self.ISBN))
        self.tree_view.append_column(
            Gtk.TreeViewColumn('Title', self.title_renderer, text=self.TITLE))
        self.tree_view.append_column(
            Gtk.TreeViewColumn('Author', self.author_renderer, text=self.AUTHOR))

        self.own_renderer = Gtk.CellRendererToggle()
        self.own_renderer.connect('toggled', self.on_own_toggled)
        own_column = Gtk.TreeViewColumn('Own', self.own_renderer, active=3)
        self.tree_view.append_column(own_column)

        self.want_renderer = Gtk.CellRendererToggle()
        self.want_renderer.connect('toggled', self.on_want_toggled)
        want_column = Gtk.TreeViewColumn('Want', self.want_renderer, active=4)
        self.tree_view.append_column(want_column)

        self.read_renderer = Gtk.CellRendererToggle()
        self.read_renderer.connect('toggled', self.on_read_toggled)
        read_column = Gtk.TreeViewColumn('Read', self.read_renderer, active=5)
        self.tree_view.append_column(read_column)

        self.location_renderer = Gtk.CellRendererText(editable=True)
        self.location_renderer.set_property('editable', True)
        self.location_renderer.connect('edited', self.on_location_edited)
        self.tree_view.append_column(
            Gtk.TreeViewColumn('Location', self.location_renderer, text=6))

        return self.tree_view

    @property
    def editing(self):
        return (self.isbn_renderer.get_property('editing') or
                self.title_renderer.get_property('editing') or
                self.author_renderer.get_property('editing') or
                self.location_renderer.get_property('editing'))

    def on_location_edited(self, cell, path, new_text):
        abs_path = self._convert_filtered_path_to_path(path)
        self.data[abs_path][6] = new_text

    def on_own_toggled(self, cellrenderer_toggle, path):
        abs_path = self._convert_filtered_path_to_path(path)
        self.data[abs_path][3] = not self.data[abs_path][3]

    def on_want_toggled(self, cellrenderer_toggle, path):
        abs_path = self._convert_filtered_path_to_path(path)
        self.data[abs_path][4] = not self.data[abs_path][4]

    def on_read_toggled(self, cellrenderer_toggle, path):
        abs_path = self._convert_filtered_path_to_path(path)
        self.data[abs_path][5] = not self.data[abs_path][5]

    def _convert_filtered_path_to_path(self, child_path):
        """Converts a filtered path to an absolute path.
        Once the TreeView gets filtered, the reported indices no longer
        correspond to the original model, therefore they need to be
        recalculated.
        :param child_path: The path in the filtered TreeView.
        :returns int: The index of the child path.
        """
        path = Gtk.TreePath(child_path)
        model = self.tree_view.get_model()
        abs_path = model.convert_path_to_child_path(path)
        return abs_path.get_indices()[0]

    def _filter_data_func(self, model, iter, data):
        """Filter columns ISBN, Title, Author by query."""
        if self.filter_by is None or self.filter_by == '':
            return True

        location = model[iter][6].lower() if model[iter][6] else ''

        return (self.filter_by in model[iter][self.ISBN].lower() or
                self.filter_by in model[iter][self.TITLE].lower() or
                self.filter_by in model[iter][self.AUTHOR].lower() or
                self.filter_by in location)

    def on_selection_changed(self, selection):
        model, iter = selection.get_selected()
        if iter is not None:
            self.selected_path = model.get_path(iter)
            self.selected_book = Book.fetch(
                model[iter][self.ISBN],
                model[iter][self.TITLE],
                model[iter][self.AUTHOR],
                self.parent.db
            )
            self.parent.set_active_book(self.selected_book)
        else:
            self.selection = None
            self.selected_book = None

    def append(self, entry):
        """Append an entry to the list."""
        self.data.append(entry.to_list())

    def remove_selected(self):
        """Remove the currently selected entry from the list."""
        self.data.remove(self.data.get_iter(self.selected_path))

    def search(self, query):
        """Filter the list by the given term."""
        self.filter_by = query.lower()
        self.filter.refilter()
