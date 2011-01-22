import gtk
import pango
from malvern import (
    MaybeStackableWindow, MaybePannableArea, MagicCheckButton,
)

class EventWindow(MaybeStackableWindow):
    def __init__(self, schedule, event, favourite_toggled_cb):
        MaybeStackableWindow.__init__(self, event.title)
        self.schedule = schedule
        self.event = event
        self.favourite_toggled_cb = favourite_toggled_cb

        vbox = gtk.VBox(spacing=12)

        label = gtk.Label()
        label.set_markup(event.full())
        label.set_properties(wrap=True)
        vbox.pack_start(label)

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
