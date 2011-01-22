# encoding: utf-8

import xml.dom.minidom as minidom
from xml.dom.minidom import Node
from datetime import datetime

from malvern import config_file, esc

_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
         'Saturday', 'Sunday']

def getChildrenByTagName(node, name):
    """Similar to node.getElementsByTagName(name), but only fetches immediate
    children."""
    return [child for child in node.childNodes if child.nodeName == name]

def get_text(node):
    """Concatenates all of node's text children, removing single newlines (but
    preserving paragraphs."""
    text = ''.join([child.data for child in node.childNodes
                               if child.nodeType == Node.TEXT_NODE])
    return '\n\n'.join([p.replace('\n', ' ') for p in text.split('\n\n')])

def get_text_from_children(parent, name, joiner=''):
    """Given a node, returns the text contents of all its children named
    'name', joined by 'joiner'. For example, given a node 'foo' representing
    this stanza:

        <foo>
          <bar>hello</bar>
          <baz>not this one</baz>
          <bar>world</bar>
        <foo>

    then:

        >>> get_text_from_children(foo, 'bar', joiner=' ')
        u'hello world'.
    """

    texts = [get_text(c) for c in getChildrenByTagName(parent, name)]
    return joiner.join(texts)

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

        for day in getChildrenByTagName(doc.documentElement, 'day'):
            date = datetime.strptime(day.getAttribute('date'), '%Y-%m-%d')
            day_name = _DAYS[date.weekday()]

            for room_node in getChildrenByTagName(day, 'room'):
                room = room_node.getAttribute('name')

                for node in getChildrenByTagName(room_node, 'event'):
                    e = Event(node, day_name, room)
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
    def __init__(self, node, date, room):
        self.date = date
        self.id = node.getAttribute('id')
        self.room = room

        children = [ c for c in node.childNodes
                       if c.nodeType == Node.ELEMENT_NODE
                   ]
        for child in children:
            n = child.nodeName
            t = get_text(child)

            if n == 'title':
                self.title = t
            elif n == 'start':
                self.start = t
            elif n == 'duration':
                self.duration = t
            elif n == 'track':
                self.track = t
            elif n == 'description':
                self.description = t
            elif n == 'persons':
                # FIXME: maybe joining the people together should be up to the
                # widgets?
                self.person = get_text_from_children(child, 'person',
                    joiner=', ')
            else:
                pass

        self.end = calculate_end(self.start, self.duration)

    def summary(self):
        return "<b>%s</b>\n<small>%s <i>(%s, %s–%s, %s, %s track)</i></small>" \
            % (esc(self.title),
               esc(self.person),
               esc(self.date), esc(self.start), esc(self.end),
               esc(self.room), esc(self.track))

    def full(self):
        return "%s\n\n%s" \
            % (self.summary(), esc(self.description))
