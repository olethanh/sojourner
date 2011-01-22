import gtk
import pango
from malvern import MaybeStackableWindow, MaybePannableArea
from sojourner.eventlist import EventList

class CategoryList(MaybeStackableWindow):
    COL_CATEGORY = 0

    def __init__(self, schedule, title, categories):
        MaybeStackableWindow.__init__(self, title)
        self.schedule = schedule
        self.categories = categories
        self.store = gtk.TreeStore(str)

        for room in sorted(categories.keys()):
            self.store.append(None, [room])

        treeview = gtk.TreeView(self.store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.category_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)

        tvcolumn.add_attribute(cell, 'markup', CategoryList.COL_CATEGORY)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        self.add_with_margins(pannable)

        self.show_all()

    def category_activated(self, treeview, row, column):
        i = self.store.get_iter(row)
        category, = self.store.get(i, CategoryList.COL_CATEGORY)

        EventList(self.schedule, category, self.categories[category])
