import gtk
import gio
import glib
import os.path as path

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
        gtk.Dialog.__init__(self, title='Updating schedule', parent=parent,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self._progress = gtk.ProgressBar()
        self._progress.set_fraction(0.0)

        self.get_content_area().add(self._progress)

        self.connect('response', Updater._response_cb)

        # Kick off the actual copying
        self._source = gio.File(url)
        self._temp = gio.File('/tmp/' + target.get_basename())
        self._target = target

        # Setting flags=gio.FILE_COPY_OVERWRITE apparently doesn't work on
        # copy_async so we have to do this stupid dance with downloading to
        # /tmp and then overwriting.
        try:
            self._temp.delete()
        except Exception, e:
            pass

        self._cancellable = gio.Cancellable()
        self._source.copy_async(self._temp,
            self._finished_cb, self._progress_cb,
            cancellable=self._cancellable)
        # Throb for a while until the file is actively being downloaded.
        self._pulse_timeout = glib.timeout_add(100, self._pulse_cb)

        self._finished_cb = finished_cb

    def _pulse_cb(self):
        self._progress.pulse()
        return True

    def _progress_cb(self, current_bytes, total_bytes):
        self._stop_pulsing()

        if total_bytes == 0:
            # This is relatively hypothetical
            self._progress.pulse()
        else:
            fraction = float(current_bytes) / total_bytes
            self._progress.set_fraction(fraction)

    def _finished_cb(self, source, result):
        self._stop_pulsing()

        try:
            source.copy_finish(result)
            # flags= seems to work here...
            self._temp.move(self._target, flags=gio.FILE_COPY_OVERWRITE)
            self._progress.set_fraction(1.0)
            self._finished_cb(self, None)
        except gio.Error, e:
            self._finished_cb(self, e)

    def _stop_pulsing(self):
        if self._pulse_timeout != 0:
            glib.source_remove(self._pulse_timeout)
            self._pulse_timeout = 0

    def _response_cb(self, response_id):
        self._cancellable.cancel()
