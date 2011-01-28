# vim: set fileencoding=utf-8 sts=4 sw=4 :
import gtk
import pango
import sojourner.eventlist
from sojourner.malvern import (
    MaybeStackableWindow, MaybePannableArea, MagicCheckButton,
    MagicButton, LANDSCAPE_LABEL_WIDTH, PORTRAIT_LABEL_WIDTH,
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
        vbox.pack_start(self.label, expand=False)

        toggle = MagicCheckButton("Favourite")
        toggle.set_active(event in self.schedule.favourites)
        toggle.connect('toggled', self.toggle_toggled)
        vbox.pack_end(toggle, expand=False)

        self._update_conflicted_events()
        conflicts_button = MagicButton('Overlapped events')
        conflicts_button.connect('clicked', self._conflicts_button_clicked_cb)
        vbox.pack_end(conflicts_button, expand=False)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        self.add_with_margins(pannable)
        self.show_all()

        if not self.conflict_events:
            conflicts_button.hide()

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

    def _update_conflicted_events(self):
        self.conflict_events = [event for event in self.schedule.favourites \
                                if event.conflicts(self.event)]

    def _conflicts_button_clicked_cb(self, button):
        event_list = sojourner.eventlist.EventList(self.schedule,
                                                   "Favourites",
                                                   self.conflict_events)
        event_list.connect('destroy', self._event_list_destroyed_cd, button)

    def _event_list_destroyed_cd(self, window, button):
        self._update_conflicted_events()
        if not self.conflict_events:
            button.hide()
