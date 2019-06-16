import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from types import MethodType


def setup_info_bar(window):
    """Create a Gtk.InfoBar on the bottom with an info label."""
    window.info_bar = Gtk.InfoBar(no_show_all=True)
    window.info_msg = Gtk.Label("")
    window.info_ok_btn = window.info_bar.add_button("OK", Gtk.ResponseType.OK)
    window.show_message = MethodType(show_message, window)

    content_area = window.info_bar.get_content_area()
    content_area.add(window.info_msg)

    window.info_bar.connect('response', MethodType(on_info_bar_response, window))
    window.info_bar.hide()
    window.info_msg.show()

def on_info_bar_response(self, info_bar, response_id):
    info_bar.hide()

def show_message(self, message):
    self.info_msg.set_text(message)
    self.info_bar.show()
    self.info_ok_btn.grab_focus()
