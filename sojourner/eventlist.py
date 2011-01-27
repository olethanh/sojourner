# vim: set fileencoding=utf-8 sts=4 sw=4 :
from itertools import groupby
import gtk
import pango
from sojourner.malvern import (
    MaybeStackableWindow, MaybePannableArea, MagicCheckButton, STAR_ICON, esc
)
from sojourner.eventwindow import EventWindow
from sojourner.schedule import Event, get_color
from sojourner.util import add_swatch_cells

class EventList(MaybeStackableWindow):
    COL_MARKUP = 0
    COL_EVENT = 1
    COL_FAVOURITED = 2
    COL_IS_EVENT = 3
    COL_SWATCH_COLOUR = 4

    """Shows a list of events; clicking on an event shows details of that
    event."""
    def __init__(self, schedule, title, events, event_omit=Event.OMIT_DAY):
        MaybeStackableWindow.__init__(self, title)
        self.schedule = schedule
        self.store = gtk.TreeStore(str, object, bool, bool, gtk.gdk.Color)
        self.events = events

        self.__populate_store(event_omit)
        self.__create_treeview()

    def __populate_store(self, event_omit):
        for day_name, event_iter in groupby(self.events, lambda e: e.day_name):
            header = '<span size="x-large" foreground="#aaa">%s</span>' % (
                esc(day_name))
            self.store.append(None, (header, None, False, False, None))

            for event in event_iter:
                self.store.append(None,
                    (event.summary(omit=event_omit), event,
                     event in self.schedule.favourites, True,
                     get_color(event.track)))

    def __create_treeview(self):
        treeview = gtk.TreeView(self.store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.event_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        add_swatch_cells(tvcolumn, colour_col=EventList.COL_SWATCH_COLOUR,
            visible_col=EventList.COL_IS_EVENT)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        def text_data_func(column, cell, model, i):
            is_event, markup = self.store.get(i,
                EventList.COL_IS_EVENT, EventList.COL_MARKUP)
            xalign = 0.0 if is_event else 0.5
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
        is_event, event = self.store.get(i,
            EventList.COL_IS_EVENT, EventList.COL_EVENT)

        if is_event:
            EventWindow(self.schedule, event, lambda state:
                self.store.set(i, EventList.COL_FAVOURITED, state))

