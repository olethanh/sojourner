# vim: set fileencoding=utf-8 sts=4 sw=4 :

from itertools import groupby
import gtk
import pango
from sojourner.malvern import MaybeStackableWindow, MaybePannableArea, esc
from sojourner.eventlist import EventList
from sojourner.schedule import get_color
from sojourner.util import add_swatch_cells

def summarize_events(events):
    """Given a list of events, returns a summary of how many there are, plus
    the time ranges on each day."""

    def format_group(day_name, day_event_iter):
        day_events = list(day_event_iter)
        return "%s %s–%s" % (day_name,
            day_events[0].start_str,
            day_events[-1].end_str)

    time_summary = ', '.join(
        format_group(day_name, event_iter)
        for day_name, event_iter in groupby(events, lambda e: e.day_name)
        )

    return "%(n)u events: %(time_summary)s" % {
        'n': len(events),
        'time_summary': time_summary,
    }

class CategoryList(MaybeStackableWindow):
    COL_CATEGORY = 0
    COL_EVENTS = 1
    COL_CATEGORY_SUMMARY = 2
    COL_CATEGORY_COLOUR = 3

    def __init__(self, schedule, title, categories, event_fmt,
                 show_swatches=False):
        MaybeStackableWindow.__init__(self, title)
        self.schedule = schedule
        self.categories = categories
        self.event_fmt = event_fmt
        # This should really be   (str, list) but that doesn't seem to work:
        #   TypeError: could not get typecode from object
        # I guess list is not a subclass of object.
        self.store = gtk.TreeStore(str, object, str, gtk.gdk.Color)

        for category, events in sorted(categories.items()):
            summary = """<b>%(category)s</b>
<small>%(event_summary)s</small>""" % {
                'category': esc(category),
                'event_summary': summarize_events(events),
            }
            colour = get_color(category) if show_swatches else None
            self.store.append(None, (category, events, summary, colour))

        treeview = gtk.TreeView(self.store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.category_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        if show_swatches:
            add_swatch_cells(tvcolumn,
                colour_col=CategoryList.COL_CATEGORY_COLOUR)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        tvcolumn.add_attribute(cell, 'markup',
            CategoryList.COL_CATEGORY_SUMMARY)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        self.add_with_margins(pannable)

        self.show_all()

    def category_activated(self, treeview, row, column):
        i = self.store.get_iter(row)
        category, events = self.store.get(i,
            CategoryList.COL_CATEGORY, CategoryList.COL_EVENTS)

        EventList(self.schedule, category, events, self.event_fmt)
