# vim: set fileencoding=utf-8 sts=4 sw=4 :
from itertools import groupby
import gtk
import pango
from sojourner.malvern import (
    MaybeStackableWindow, MaybePannableArea, MagicCheckButton, STAR_ICON, esc
)
from sojourner.eventwindow import EventWindow

class EventList(MaybeStackableWindow):
    COL_MARKUP = 0
    COL_EVENT = 1
    COL_FAVOURITED = 2
    COL_IS_HEADER = 3

    """Shows a list of events; clicking on an event shows details of that
    event."""
    def __init__(self, schedule, title, events):
        MaybeStackableWindow.__init__(self, title)
        self.schedule = schedule
        self.store = gtk.TreeStore(str, object, bool, bool)

        for day_name, event_iter in groupby(events, lambda e: e.day_name()):
            header = '<span size="x-large" foreground="#aaa">%s</span>' % (
                esc(day_name))
            self.store.append(None, (header, None, False, True))

            for event in event_iter:
                self.store.append(None,
                    (event.summary(), event, event in self.schedule.favourites,
                     False))

        treeview = gtk.TreeView(self.store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.event_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        def text_data_func(column, cell, model, i):
            is_header, markup = self.store.get(i,
                EventList.COL_IS_HEADER, EventList.COL_MARKUP)
            xalign = 0.5 if is_header else 0.0
            cell.set_properties(markup=markup, xalign=xalign)

        tvcolumn.set_cell_data_func(cell, text_data_func)

        cell = gtk.CellRendererPixbuf()
        cell.set_property("icon-name", STAR_ICON)
        tvcolumn.pack_start(cell, False)
        tvcolumn.add_attribute(cell, 'visible', EventList.COL_FAVOURITED)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        self.add_with_margins(pannable)

        self.show_all()

    def event_activated(self, treeview, row, column):
        i = self.store.get_iter(row)
        is_header, event = self.store.get(i,
            EventList.COL_IS_HEADER, EventList.COL_EVENT)

        if not is_header:
            EventWindow(self.schedule, event, lambda state:
                self.store.set(i, EventList.COL_FAVOURITED, state))

