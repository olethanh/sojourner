#!/usr/bin/env python
# encoding: utf-8
#
# Conference schedule application for the Nokia N900.
# Copyright © 2010, Will Thompson <will@willthompson.co.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gtk
import gobject
import gio
import pango
from pynotify import Notification

from malvern import *
from sojourner.updater import Updater
from sojourner.schedule import Schedule

class Thing:
    def toggle_toggled(self, toggle, event, update_star):
        if toggle.get_active():
            self.schedule.add_favourite(event)
            update_star(True)
        else:
            self.schedule.remove_favourite(event)
            update_star(False)

    def event_activated(self, treeview, row, column):
        store = treeview.get_property('model')
        iter = store.get_iter(row)
        event, = store.get(iter, 1)

        window = MaybeStackableWindow(event.title)

        vbox = gtk.VBox(spacing=12)

        label = gtk.Label()
        label.set_markup(event.full())
        label.set_properties(wrap=True, justify=gtk.JUSTIFY_FILL)
        vbox.pack_start(label)

        def update_star(state):
            store.set(iter, 2, state)

        toggle = MagicCheckButton("Favourite")
        toggle.set_active(event in self.schedule.favourites)
        toggle.connect('toggled', self.toggle_toggled, event, update_star)
        vbox.pack_start(toggle, False)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        window.add(pannable)

        window.show_all()

    def event_list(self, title, events):
        window = MaybeStackableWindow(title)
        store = gtk.TreeStore(str, object, bool)

        for event in events:
            store.append(None, [event.summary(), event,
                                event in self.schedule.favourites])

        treeview = gtk.TreeView(store)
        treeview.set_headers_visible(False)
        treeview.connect("row-activated", self.event_activated)

        tvcolumn = gtk.TreeViewColumn('Stuff')
        treeview.append_column(tvcolumn)

        cell = gtk.CellRendererText()
        cell.set_property("ellipsize", pango.ELLIPSIZE_END)
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'markup', 0)

        cell = gtk.CellRendererPixbuf()
        # ou! \o/
        cell.set_property("icon-name",
            "imageviewer_favourite" if have_hildon else "emblem-special")
        tvcolumn.pack_start(cell, False)
        tvcolumn.add_attribute(cell, 'visible', 2)

        pannable = MaybePannableArea()
        pannable.add(treeview)
        window.add(pannable)

        window.show_all()

    def blah_activated(self, treeview, row, column, title, d):
        store = treeview.get_property('model')
        blah, = store.get(store.get_iter(row), 0)

        self.event_list(blah, d[blah])

    def by_blah(self, d, title):
        window = MaybeStackableWindow(title)
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

        pannable = MaybePannableArea()
        pannable.add(treeview)
        window.add(pannable)

        window.show_all()

    def view_activated(self, treeview, row, column):
        if row[0] == 0:
            self.event_list("All events", self.schedule.events)
        elif row[0] == 1:
            self.by_blah(self.schedule.events_by_room, "Rooms")
        elif row[0] == 2:
            self.by_blah(self.schedule.events_by_track, "Tracks")
        elif row[0] == 3:
            self.event_list("Favourites", self.schedule.favourites)
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
        window = MaybeStackableWindow("FOSDEM 2010")
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

        pannable = MaybePannableArea()
        pannable.add(treeview)
        window.add(pannable)

        #program = hildon.Program.get_instance()
        #program.add_window(window)

        window.show_all()

        self.schedule_file = data_file('fosdem.xml')

        if self.schedule_file.query_exists():
            self.schedule = Schedule(self.schedule_file.get_path())
        else:
            updater = Updater(window, 'http://fosdem.org/2011/schedule/xml',
                self.schedule_file, self.fetched_schedule_cb)
            updater.show_all()

        if have_hildon:
            portrait.FremantleRotation("sojourner", window, version='0.1')

        gtk.main()

if __name__ == "__main__":
    gobject.threads_init()
    Thing()

# vim: sts=4 sw=4
