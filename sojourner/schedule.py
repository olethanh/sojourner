# encoding: utf-8

import xml.dom.minidom as minidom
from datetime import datetime

from malvern import config_file, esc

_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
         'Saturday', 'Sunday']

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

def by_date_time(x, y):
    a = cmp(x.date, y.date)
    if a != 0:
        return a
    else:
        return cmp(x.start, y.start)

class Schedule(object):
    def __init__(self, schedule_path):
        doc = minidom.parse(schedule_path)

        self.events = []
        self.events_by_id = {}
        self.events_by_room = {}
        self.events_by_track = {}
        self.favourites = []

        for day in doc.getElementsByTagName("day"):
            date = datetime.strptime(day.getAttribute('date'), '%Y-%m-%d')
            day_name = _DAYS[date.weekday()]
            for node in day.getElementsByTagName("event"):
                e = Event(node, day_name)
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
            f = file(self._favourites_file(), 'r')
            for id in f.readlines():
                self.favourites.append(self.events_by_id[id.strip()])
            f.close()
        except IOError:
            # I guess they don't have any favourites
            pass

    def _favourites_file(self):
        # FIXME: this would need to be based on the schedule_path if we wanted
        # to support more than one conference.
        return config_file('fosdem/favourites').get_path()

    def _write_favourites(self):
        f = file(self._favourites_file(), 'w')
        for fav in self.favourites:
            f.write("%s\n" % fav.id)
        f.close()

    def add_favourite(self, event):
        self.favourites.append(event)
        self.favourites.sort(cmp=by_date_time)
        self._write_favourites()

    def remove_favourite(self, event):
        self.favourites.remove(event)
        self._write_favourites()

class Event(object):
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
