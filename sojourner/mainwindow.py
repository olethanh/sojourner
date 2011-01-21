import gtk
import gio
import pango
from pynotify import Notification
from malvern import *
from sojourner.updater import Updater
from sojourner.schedule import Schedule
from sojourner.eventlist import EventList
from sojourner.categorylist import CategoryList

class MainWindow(MaybeStackableWindow):
    def fetched_schedule_cb(self, updater, error):
        updater.destroy()

        if error is None:
            self.schedule = Schedule(self.schedule_file.get_path())
        else:
            print error
            if error.domain != gio.ERROR or error.code != gio.ERROR_CANCELLED:
                Notification("Couldn't fetch latest FOSDEM schedule").show()

    def _on_configure_event(self, event):
        is_portrait = event.width < event.height

        if self.is_portrait == is_portrait:
            return

        self.is_portrait = is_portrait

        if is_portrait:
            self.views.set_current_page(1)
        else:
            self.views.set_current_page(0)

    def _make_button_grid(self, portrait):
        # Hi. My name's Will, and I'm a functional programming addict.
        def _make_button(label, on_activated, icon=None):
            b = MagicButton(label, icon, thumb_height=True)
            b.connect('clicked', on_activated)
            return b

        buttons = [ _make_button(*x) for x in [
            ("All events", lambda b: EventList(self.schedule, "All events",
                self.schedule.events)),
            ("Events by room", lambda b: CategoryList(self.schedule, "Rooms",
                self.schedule.events_by_room)),
            ("Events by track", lambda b: CategoryList(self.schedule, "Tracks",
                self.schedule.events_by_track)),
            ("Favourites", lambda b: EventList(self.schedule, "Favourites",
                self.schedule.favourites), STAR_ICON),
        ]]

        if portrait:
            rows=4
            columns=1
        else:
            rows=2
            columns=2

        coordinates = [ (x, y) for x in range(0, columns)
                               for y in range(0, rows)
                      ]

        table = gtk.Table(rows=rows, columns=columns, homogeneous=True)
        table.set_row_spacings(6)
        table.set_col_spacings(6)

        for ((x, y), button) in zip(coordinates, buttons):
            table.attach(button, x, x + 1, y, y + 1)

        vbox = gtk.VBox(spacing=12)

        # We should have something nicer here.
        l = gtk.Label()
        l.set_markup("<span size='larger' weight='bold'>FOSDEM 2011</span>")
        vbox.pack_start(l, expand=False)

        vbox.pack_start(table, expand=False)

        return vbox

    def __init__(self):
        MaybeStackableWindow.__init__(self, "FOSDEM 2010")
        self.connect("delete_event", gtk.main_quit, None)

        # We use a notebook with no tabs and two pages to flip between
        # landscape and portrait layouts as necessary.
        self.views = gtk.Notebook()
        self.views.set_show_tabs(False)
        self.views.append_page(self._make_button_grid(portrait=False))
        self.views.append_page(self._make_button_grid(portrait=True))
        self.add(self.views)
        self.show_all()

        # We'll find out shortly which way up we actually are. Launching
        # straight into portrait mode doesn't seem to work anyway, so ... no
        # harm done.
        self.is_portrait = False
        self.connect('configure-event', MainWindow._on_configure_event)

        if have_hildon:
            portrait.FremantleRotation("sojourner", self, version='0.1')

        # FIXME: We should parse in a thread. It takes ages, and makes the app
        # appear to start more slowly...
        self.schedule_file = data_file('fosdem.xml')

        if self.schedule_file.query_exists():
            self.schedule = Schedule(self.schedule_file.get_path())
        else:
            updater = Updater(self, 'http://fosdem.org/2011/schedule/xml',
                self.schedule_file, self.fetched_schedule_cb)
            updater.show_all()
