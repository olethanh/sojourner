import gtk
import pango
from malvern import MaybeStackableWindow, MaybePannableArea
from sojourner.eventlist import EventList

class CategoryList(MaybeStackableWindow):
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

        tvcolumn.add_attribute(cell, 'markup', 0)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        self.add(pannable)

        self.show_all()

    def category_activated(self, treeview, row, column):
        category, = self.store.get(self.store.get_iter(row), 0)

        EventList(self.schedule, category, self.categories[category])
