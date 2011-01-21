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
    def view_activated(self, treeview, row, column):
        if row[0] == 0:
            EventList(self.schedule, "All events", self.schedule.events)
        elif row[0] == 1:
            CategoryList(self.schedule, "Rooms", self.schedule.events_by_room)
        elif row[0] == 2:
            CategoryList(self.schedule, "Tracks", self.schedule.events_by_track)
        elif row[0] == 3:
            EventList(self.schedule, "Favourites", self.schedule.favourites)
        else:
            print row

    def fetched_schedule_cb(self, updater, error):
        updater.destroy()

        if error is None:
            self.schedule = Schedule(self.schedule_file.get_path())
        else:
            print error
            if error.domain != gio.ERROR or error.code != gio.ERROR_CANCELLED:
                Notification("Couldn't fetch latest FOSDEM schedule").show()

    def __init__(self):
        MaybeStackableWindow.__init__(self, "FOSDEM 2010")
        self.connect("delete_event", gtk.main_quit, None)

        store = gtk.TreeStore(str)

        for snake in ["All events", "By room", "By track", "Favourites"]:
            store.append(None, [snake])

        treeview = gtk.TreeView(store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.view_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        tvcolumn.add_attribute(cell, 'markup', 0)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        self.add(pannable)
        self.show_all()

        self.schedule_file = data_file('fosdem.xml')

        if self.schedule_file.query_exists():
            self.schedule = Schedule(self.schedule_file.get_path())
        else:
            updater = Updater(self, 'http://fosdem.org/2011/schedule/xml',
                self.schedule_file, self.fetched_schedule_cb)
            updater.show_all()

        if have_hildon:
            portrait.FremantleRotation("sojourner", self, version='0.1')
