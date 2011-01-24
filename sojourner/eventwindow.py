# vim: set fileencoding=utf-8 sts=4 sw=4 :
import gtk
import pango
from sojourner.malvern import (
    MaybeStackableWindow, MaybePannableArea, MagicCheckButton,
    LANDSCAPE_LABEL_WIDTH, PORTRAIT_LABEL_WIDTH,
)

class EventWindow(MaybeStackableWindow):
    def __init__(self, schedule, event, favourite_toggled_cb):
        MaybeStackableWindow.__init__(self, event.title,
            self._on_orientation_changed)
        self.schedule = schedule
        self.event = event
        self.favourite_toggled_cb = favourite_toggled_cb

        vbox = gtk.VBox(spacing=12)

        self.label = gtk.Label()
        self.label.set_markup(event.full())
        self.label.set_properties(wrap=True)
        vbox.pack_start(self.label)

        toggle = MagicCheckButton("Favourite")
        toggle.set_active(event in self.schedule.favourites)
        toggle.connect('toggled', self.toggle_toggled)
        vbox.pack_start(toggle, False)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        self.add_with_margins(pannable)
        self.show_all()

    def toggle_toggled(self, toggle):
        if toggle.get_active():
            self.schedule.add_favourite(self.event)
            self.favourite_toggled_cb(True)
        else:
            self.schedule.remove_favourite(self.event)
            self.favourite_toggled_cb(False)

    def _on_orientation_changed(self, is_portrait):
        self.label.set_size_request(
            width=(PORTRAIT_LABEL_WIDTH if is_portrait
                                        else LANDSCAPE_LABEL_WIDTH),
            height=-1)
