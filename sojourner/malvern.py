# vim: set fileencoding=utf-8 sts=4 sw=4 :
#
# Malvern:
#   A bunch of sketchily-defined classes to help write applications that can be
#   developed on a Linux desktop using pygtk, but which target the N900 using
#   Hildon.
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

import os
import gtk
import gobject
import gio

# First up, some useful functions which are either not in the version of
# pygobject in Maemo 5, or just really wordy.

def esc(x):
    return gobject.markup_escape_text(x)

def create_parent_directory(path):
    f = gio.File(path)

    # If the version of pygobject in Maemo weren't prehistoric, we could call:
    #   f.get_parent().make_directory_with_parents()
    # Oh well.

    # I couldn't find a combinator for this in functools or itertools. Boo.
    directories = []
    g = f.get_parent()

    while g is not None:
        directories.append(g)
        g = g.get_parent()

    try:
        while directories:
            try:
                d = directories.pop()
                d.make_directory()
            except gio.Error, e:
                if e.code != gio.ERROR_EXISTS:
                    raise
    except gio.Error, e:
        # Oh well. :(
        print e

    return f

def config_file(basename):
    return create_parent_directory(
        "%s/.config/sojourner/%s" % (os.environ['HOME'], basename))

def data_file(basename):
    return create_parent_directory(
        "%s/.local/share/sojourner/%s" % (os.environ['HOME'], basename))

#  _______________________
# ( it's just gtk, right? )
#  -----------------------
#        o   ,__,
#         o  (oo)____
#            (__)    )\
#               ||--|| *
#

try:
    import hildon
    import sojourner.portrait
    have_hildon = True
except ImportError:
    have_hildon = False

# ou! \o/
STAR_ICON = "imageviewer_favourite" if have_hildon else "emblem-special"

# Mmm. It seems—I would love to be corrected on this—that if you want a
# GtkLabel to fill the available width and also word-wrap, you have to forcibly
# set its size request. I *believe* that the height-for-width and natural size
# stuff in really modern Gtk+ fixes this, but that's not available in
# Fremantle.
SIDE_MARGIN = 12

if have_hildon:
    # I measured a screenshot.
    scroll_bar_width = 8

    LANDSCAPE_SCREEN_WIDTH = 800
    PORTRAIT_SCREEN_WIDTH = 480
else:
    # Whatever
    scroll_bar_width = 16

    LANDSCAPE_SCREEN_WIDTH = 400
    PORTRAIT_SCREEN_WIDTH = 240

dead_space = 2 * SIDE_MARGIN + scroll_bar_width
LANDSCAPE_LABEL_WIDTH = LANDSCAPE_SCREEN_WIDTH - dead_space
PORTRAIT_LABEL_WIDTH = PORTRAIT_SCREEN_WIDTH - dead_space

class MaybeStackableWindow(hildon.StackableWindow if have_hildon
                           else gtk.Window):
    def __init__(self, title, orientation_changed_cb=None):
        super(MaybeStackableWindow, self).__init__()
        self.set_title(title)
        self.orientation_discovered = False
        self.is_portrait = False
        self.orientation_changed_cb = orientation_changed_cb

        if orientation_changed_cb is not None or not have_hildon:
            self.connect('configure-event',
                MaybeStackableWindow._on_configure_event)

        if not have_hildon:
            # Fake a N900-esque size. Obviously this doesn't scale down images
            # or whatever but it's a reasonable approximation of the kind of
            # size you can expect.
            self.set_size_request(400, 240)
            self.resize(400, 240)

            # Make mashing 'r' act like rotating the window.
            def kpe(_window, event):
                if event.string == 'r':
                    if self.is_portrait:
                        self.set_size_request(400, 240)
                        self.resize(400, 240)
                    else:
                        self.set_size_request(240, 400)
                        self.resize(240, 400)

                    # We don't update is_portrait; the configure-event callback
                    # will do that for us.
                    return True

                return False

            self.connect('key-press-event', kpe)

            self.vbox = gtk.VBox()
            self.add(self.vbox)
            self.menu_buttons = None

    def add_with_margins(self, child):
        """Adds a single widget to the window, with margins that seem to match
        those used in standard Fremantle applications. (There are supposedly
        constants for the correct values, but I can't find them in the Python
        bindings and I don't have the C headers handy. So these are eyeballed.)

        This makes the app look atrocious on plain Gtk+ but that's okay. It
        means it's easy to see when you've forgotten to use this function!"""
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(6, 0, SIDE_MARGIN, SIDE_MARGIN)
        alignment.add(child)

        if have_hildon:
            self.add(alignment)
        else:
            self.vbox.pack_end(alignment)

    if not have_hildon:
        def set_app_menu(self, menu):
            self.vbox.pack_start(menu, expand=False)

    def _on_configure_event(self, event):
        is_portrait = event.width < event.height

        # Don't notify the application if we've told them once and there's been
        # no change.
        if self.orientation_discovered and self.is_portrait == is_portrait:
            return

        self.orientation_discovered = True
        self.is_portrait = is_portrait

        if self.orientation_changed_cb is not None:
            self.orientation_changed_cb(self.is_portrait)

class AppMenu(hildon.AppMenu if have_hildon else gtk.HButtonBox):
    def __init__(self):
        super(AppMenu, self).__init__()

    # Ick, python lets you do this.
    if not have_hildon:
        def append(self, button):
            self.add(button)

class MaybePannableArea(hildon.PannableArea if have_hildon
                        else gtk.ScrolledWindow):
    def __init__(self):
        super(MaybePannableArea, self).__init__()

        # Hildon doesn't do horizontal scroll bars
        if not have_hildon:
            self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

class MagicButton(hildon.Button if have_hildon else gtk.Button):
    def __init__(self, label, icon_name=None, thumb_height=False):
        if have_hildon:
            if thumb_height:
                height_flag = gtk.HILDON_SIZE_THUMB_HEIGHT
            else:
                height_flag = gtk.HILDON_SIZE_FINGER_HEIGHT

            super(MagicButton, self).__init__(
                gtk.HILDON_SIZE_AUTO_WIDTH | height_flag,
                # XXX o rly
                hildon.BUTTON_ARRANGEMENT_HORIZONTAL,
                title=label,
                value=None)
        else:
            super(MagicButton, self).__init__(label=label)

        if icon_name is not None:
            image = gtk.Image()
            image.set_from_icon_name(icon_name, gtk.ICON_SIZE_BUTTON)
            self.set_image(image)

class MagicEntry(hildon.Entry if have_hildon else gtk.Entry):
    def __init__(self):
        if have_hildon:
            super(MagicEntry, self).__init__(gtk.HILDON_SIZE_AUTO)
        else:
            super(MagicEntry, self).__init__()

class MagicCheckButton(hildon.CheckButton if have_hildon else gtk.CheckButton):
    def __init__(self, label):
        if have_hildon:
            super(MagicCheckButton, self).__init__(
                gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
        else:
            super(MagicCheckButton, self).__init__()

        self.set_label(label)
