# vim: set fileencoding=utf-8 sts=4 sw=4 :
import gtk
import gio
import glib
import os.path as path

import threading

class Updater(gtk.Dialog):
    """
    Fetches a fresh copy of the schedule, and shows a progress dialog. We try
    not to stamp on an existing copy in the event of disaster.
    """

    def __init__(self, parent, url, target, finished_cb):
        """
        Arguments:

        parent:       a gtk.Window
        url:          the URL to fetch
        target:       a gio.File object at which to save the URL's contents
        finished_cb:  a function accepting this Updater object and a gio.Error
                      (which is None if we finished successfully)
        """

        # Set up the widget
        gtk.Dialog.__init__(self, title='Downloading the latest schedule…',
            parent=parent, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.__progress = gtk.ProgressBar()
        self.__progress.set_fraction(0.0)
        self.vbox.pack_start(self.__progress)

        self.connect('response', Updater.__response_cb)

        # Stash urls and things
        self.__source = gio.File(url)
        self.__temp = gio.File('/tmp/' + target.get_basename())
        self.__target = target
        self.__finished_cb = finished_cb

        # Throb for a while until the file is actively being downloaded.
        self.__pulse_timeout = 0
        self.__start_pulsing()

        # Kick off the actual copying.  Maemo 5's pygobject doesn't have
        # copy_async, so we use a thread to basically re-implement
        # copy_async...
        self.__cancellable = gio.Cancellable()
        self.__download_thread = threading.Thread(target=self.__download,
            name='Downloader')
        self.__download_thread.daemon = True
        self.__download_thread.start()

    def __download(self):
        """Grabs the latest schedule, if possible."""
        try:
            self.__source.copy(self.__temp,
                # Use an idle to be run in the main thread.
                (lambda c, t: glib.idle_add(self.__progress_cb, c, t)),
                flags=gio.FILE_COPY_OVERWRITE,
                cancellable=self.__cancellable)

            # FIXME: parse the new file to make sure it's actually valid before
            # overwriting any existing file.
            self.__temp.move(self.__target, flags=gio.FILE_COPY_OVERWRITE)

            glib.idle_add(self.__finished_copying, None)
        except Exception, e:
            glib.idle_add(self.__finished_copying, e)

    def __progress_cb(self, current_bytes, total_bytes):
        """Called (in an idle, so in the glib mainloop thread) for each chunk
        of data downloaded."""
        self.__stop_pulsing()

        if total_bytes == 0:
            # The server didn't tell us how big the file is; so the best we
            # can do is pulse for each chunk of data.
            self.__progress.pulse()
        else:
            fraction = float(current_bytes) / total_bytes
            self.__progress.set_fraction(fraction)

    def __finished_copying(self, e):
        self.__stop_pulsing()
        self.__progress.set_fraction(1.0)
        self.__finished_cb(self, e)

    def __start_pulsing(self):
        if self.__pulse_timeout == 0:
            self.__pulse_timeout = glib.timeout_add(100, self.__pulse_cb)

        return False

    def __pulse_cb(self):
        self.__progress.pulse()
        return True

    def __stop_pulsing(self):
        if self.__pulse_timeout != 0:
            glib.source_remove(self.__pulse_timeout)
            self.__pulse_timeout = 0

        return False

    def __response_cb(self, response_id):
        self.__cancellable.cancel()
