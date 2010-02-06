import xml.dom.minidom as minidom

import gtk
import gobject
import pango

import os

try:
    import hildon
    have_hildon = True
except ImportError:
    have_hildon = False

def get_text(parent, name, joiner=''):
    blah = parent.getElementsByTagName(name)

    things = []
    for n in blah:
        for node in n.childNodes:
            if node.nodeType == node.TEXT_NODE:
                things.append(node.data)
    return joiner.join(things)

def esc(x):
    return gobject.markup_escape_text(x)

def mk_window(title):
    if have_hildon:
        window = hildon.StackableWindow()
    else:
        window = gtk.Window()
        window.set_size_request(400, 240)
    window.set_title(title)
    return window

def mk_sw(child, viewport=False):
    if have_hildon:
        sw = hildon.PannableArea()
    else:
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

    if viewport:
        sw.add_with_viewport(child)
    else:
        sw.add(child)

    return sw

def mk_toggle(title):
    if have_hildon:
        toggle = hildon.CheckButton(gtk.HILDON_SIZE_FINGER_HEIGHT)
        toggle.set_label(title)
    else:
        toggle = gtk.ToggleButton(label=title)

    return toggle

class Event:
    def __init__(self, node, date):
        self.date = date
        self.id = node.getAttribute('id')
        self.title = get_text(node, "title")
        self.person = get_text(node, "person", joiner=', ')
        self.start = get_text(node, "start")
        self.room = get_text(node, "room")
        self.track = get_text(node, "track")
        self.description = get_text(node, "description")

    def summary(self):
        return "<b>%s</b>\n%s <i>(%s, %s, %s, %s track)</i>" \
            % (esc(self.title),
               esc(self.person), esc(self.date), esc(self.start),
               esc(self.room), esc(self.track))

    def full(self):
        return "%s\n\n%s" \
            % (self.summary(), esc(self.description))

class Thing:
    def favourites_file(self):
        try:
            os.mkdir(os.environ['HOME'] + '/.config')
        except OSError:
            pass

        try:
            os.mkdir(os.environ['HOME'] + '/.config/foschart')
        except OSError:
            pass

        return os.environ['HOME'] + "/.config/foschart/favourites"

    def toggle_toggled(self, toggle, event):
        if toggle.get_active():
            self.favourites.append(event)
        else:
            self.favourites.remove(event)

        f = file(self.favourites_file(), 'w')
        for fav in self.favourites:
            f.write("%s\n" % fav.id)
        f.close()

    def event_activated(self, treeview, row, column):
        store = treeview.get_property('model')
        event, = store.get(store.get_iter(row), 1)

        window = mk_window(event.title)

        vbox = gtk.VBox()

        label = gtk.Label()
        label.set_markup(event.full())
        label.set_property("wrap", True)
        vbox.pack_start(label)

        toggle = mk_toggle("Favourite")
        toggle.set_active(event in self.favourites)
        toggle.connect('toggled', self.toggle_toggled, event)
        vbox.pack_start(toggle, False)

        sw = mk_sw(vbox, True)
        window.add(sw)

        window.show_all()

    def event_list(self, title, events=None):
        window = mk_window(title)

        if events is None:
            events = self.events

        store = gtk.TreeStore(str, object)

        for event in events:
            store.append(None, [event.summary(), event])

        treeview = gtk.TreeView(store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.event_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        tvcolumn.add_attribute(cell, 'markup', 0)

        sw = mk_sw(treeview)
        window.add(sw)

        window.show_all()

    def blah_activated(self, treeview, row, column, title, d):
        store = treeview.get_property('model')
        blah, = store.get(store.get_iter(row), 0)

        self.event_list(blah, d[blah])

    def by_blah(self, d, title):
        window = mk_window(title)
        store = gtk.TreeStore(str)

        for room in sorted(d.keys()):
            store.append(None, [room])

        treeview = gtk.TreeView(store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.blah_activated, title, d)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        tvcolumn.add_attribute(cell, 'markup', 0)

        sw = mk_sw(treeview)
        window.add(sw)

        window.show_all()

    def view_activated(self, treeview, row, column):
        if row[0] == 0:
            self.event_list("All events")
        elif row[0] == 1:
            self.by_blah(self.events_by_room, "Rooms")
        elif row[0] == 2:
            self.by_blah(self.events_by_track, "Tracks")
        elif row[0] == 3:
            self.event_list("Favourites", self.favourites)
        else:
            print row

    def __init__(self):
        doc = minidom.parse("schedule.en.xml")

        self.events = []
        self.events_by_id = {}
        self.events_by_room = {}
        self.events_by_track = {}

        zomg = {'2010-02-06': 'Saturday',
                '2010-02-07': 'Sunday',
               }

        for day in doc.getElementsByTagName("day"):
            date = zomg[day.getAttribute('date')]
            for node in day.getElementsByTagName("event"):
                e = Event(node, date)
                self.events.append(e)
                self.events_by_id[e.id] = e

                blah = self.events_by_room.get(e.room, [])
                blah.append(e)
                self.events_by_room[e.room] = blah

                blah = self.events_by_track.get(e.track, [])
                blah.append(e)
                self.events_by_track[e.track] = blah

        self.favourites = []

        try:
            f = file(self.favourites_file(), 'r')
            for id in f.readlines():
                self.favourites.append(self.events_by_id[id.strip()])
            f.close()
        except IOError:
            pass

        window = mk_window("FOSDEM 2010")
        window.connect("delete_event", gtk.main_quit, None)

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

        sw = mk_sw(treeview)
        window.add(sw)

        #program = hildon.Program.get_instance()
        #program.add_window(window)

        window.show_all()
        gtk.main()

if __name__ == "__main__":
    Thing()

# vim: sts=4 sw=4
