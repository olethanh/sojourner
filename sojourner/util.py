# vim: set fileencoding=utf-8 sts=4 sw=4 :
import gtk

def add_swatch_cells(column, colour_col, visible_col=None):
    # Here's a hack to show a chunk of colour at the left-hand side of
    # events to indicate their track. We have a text renderer containing,
    # erm, nothing, whose background colour we set. Then we have another
    # one with a single space to add a consistent gap between the blob of
    # colour and the event summary. This is easier than writing a custom
    # cell renderer, or using CellRendererPixbuf.
    swatch_cell = gtk.CellRendererText()
    swatch_cell.set_property('text', '   ')
    column.pack_start(swatch_cell, False)

    column.add_attribute(swatch_cell, 'background-gdk', colour_col)

    blank_cell = gtk.CellRendererText()
    blank_cell.set_property('text', ' ')
    column.pack_start(blank_cell, False)

    if visible_col is not None:
        column.add_attribute(swatch_cell, 'visible', visible_col)
        column.add_attribute(blank_cell, 'visible', visible_col)
