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

import xml.dom.minidom as minidom

import gtk
import gobject
import gio
import pango
from pynotify import Notification

from malvern import *
from sojourner.updater import Updater

def get_text(parent, name, joiner=''):
    blah = parent.getElementsByTagName(name)

    things = []
    for n in blah:
        for node in n.childNodes:
            if node.nodeType == node.TEXT_NODE:
                things.append(node.data)
    return joiner.join(things)

def calculate_end(start, duration):
    h1, m1 = start.split(':')
    h2, m2 = duration.split(':')

    h3 = int(h1) + int(h2)
    m3 = int(m1) + int(m2)

    h4 = h3 + (m3 / 60)
    m4 = m3 % 60

    return "%02d:%02d" % (h4, m4)

class Event:
    def __init__(self, node, date):
        self.date = date
        self.id = node.getAttribute('id')
        self.title = get_text(node, "title")
        self.person = get_text(node, "person", joiner=', ')
        self.start = get_text(node, "start")
        self.duration = get_text(node, "duration")
        self.end = calculate_end(self.start, self.duration)
        self.room = get_text(node, "room")
        self.track = get_text(node, "track")
        self.description = get_text(node, "description")

    def summary(self):
        return "<b>%s</b>\n<small>%s <i>(%s, %s–%s, %s, %s track)</i></small>" \
            % (esc(self.title),
               esc(self.person),
               esc(self.date), esc(self.start), esc(self.end),
               esc(self.room), esc(self.track))

    def full(self):
        return "%s\n\n%s" \
            % (self.summary(), esc(self.description))

def by_date_time(x, y):
    a = cmp(x.date, y.date)
    if a != 0:
        return a
    else:
        return cmp(x.start, y.start)

class Thing:
    def favourites_file(self):
        return config_file('favourites').get_path()

    def toggle_toggled(self, toggle, event, update_star):
        if toggle.get_active():
            self.favourites.append(event)
            self.favourites.sort(cmp=by_date_time)
            update_star(True)
        else:
            self.favourites.remove(event)
            update_star(False)

        f = file(self.favourites_file(), 'w')
        for fav in self.favourites:
            f.write("%s\n" % fav.id)
        f.close()

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
        toggle.set_active(event in self.favourites)
        toggle.connect('toggled', self.toggle_toggled, event, update_star)
        vbox.pack_start(toggle, False)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        window.add(pannable)

        window.show_all()

    def event_list(self, title, events=None):
        window = MaybeStackableWindow(title)

        if events is None:
            events = self.events

        store = gtk.TreeStore(str, object, bool)

        for event in events:
            store.append(None, [event.summary(), event,
                                event in self.favourites])

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
            self.event_list("All events")
        elif row[0] == 1:
            self.by_blah(self.events_by_room, "Rooms")
        elif row[0] == 2:
            self.by_blah(self.events_by_track, "Tracks")
        elif row[0] == 3:
            self.event_list("Favourites", self.favourites)
        else:
            print row

    def parse(self, schedule_path):
        doc = minidom.parse(schedule_path)

        self.events = []
        self.events_by_id = {}
        self.events_by_room = {}
        self.events_by_track = {}
        self.favourites = []

        # XXX this isn't gonna fly
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

        self.events.sort(cmp=by_date_time)

        try:
            f = file(self.favourites_file(), 'r')
            for id in f.readlines():
                self.favourites.append(self.events_by_id[id.strip()])
            f.close()
        except IOError:
            # I guess they don't have any favourites
            pass

    def fetched_schedule_cb(self, updater, error):
        updater.destroy()

        if error is None:
            self.parse(self.schedule_file.get_path())
        else:
            print error
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
            self.parse(self.schedule_file.get_path())
        else:
            updater = Updater(window, 'http://fosdem.org/2011/schedule/xml',
                self.schedule_file, self.fetched_schedule_cb)
            updater.show_all()

        gtk.main()

if __name__ == "__main__":
    Thing()

# vim: sts=4 sw=4
