import xml.dom.minidom as minidom

import gtk
import gobject
import pango

import os

if os.environ.get('OSSO_PRODUCT_SHORT_NAME') is not None:
    import hildon
    have_hildon = True
else:
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

class Event:
    def __init__(self, node):
        self.title = get_text(node, "title")
        self.person = get_text(node, "person", joiner=', ')
        self.start = get_text(node, "start")
        self.room = get_text(node, "room")
        self.track = get_text(node, "track")
        self.description = get_text(node, "description")

    def summary(self):
        return "<b>%s</b>\n%s <i>(%s, %s, %s track)</i>" \
            % (esc(self.title), esc(self.person), esc(self.start), esc(self.room), esc(self.track))


    def full(self):
        return "<b>%s</b>\n%s <i>(%s, %s, %s track)</i>\n\n%s" \
            % (esc(self.title), esc(self.person), esc(self.start), esc(self.room), esc(self.track), esc(self.description))

class Thing:
    def event_activated(self, treeview, row, column):
        store = treeview.get_property('model')
        event, = store.get(store.get_iter(row), 1)

        window = mk_window(event.title)

        label = gtk.Label()
        label.set_markup(event.full())
        label.set_property("wrap", True)

        sw = mk_sw(label, True)
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

    def room_activated(self, treeview, row, column):
        store = treeview.get_property('model')
        room, = store.get(store.get_iter(row), 0)

        self.event_list(room, self.events_by_room[room])

    def by_room(self):
        window = mk_window("Rooms")
        store = gtk.TreeStore(str)

        for room in sorted(self.events_by_room.keys()):
            store.append(None, [room])

        treeview = gtk.TreeView(store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.room_activated)

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
        else:
            self.by_room()

    def __init__(self):
        doc = minidom.parse("schedule.en.xml")
        self.events = [Event(node) for node in doc.getElementsByTagName("event")]

        self.events_by_room = {}
        for e in self.events:
            blah = self.events_by_room.get(e.room, [])
            blah.append(e)
            self.events_by_room[e.room] = blah

        window = mk_window("FOSDEM 2010")
        window.connect("delete_event", gtk.main_quit, None)

        store = gtk.TreeStore(str)

        for snake in ["All events", "By room"]:
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
