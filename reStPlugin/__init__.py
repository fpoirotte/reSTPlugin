#!/usr/bin/env python
# -*- coding: utf-8 -*-

# restPlugin - HTML preview of reSt formatted text in gedit
#
# Copyright (C) 2007 - Christophe Kibleur
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import gedit
import os
import sys
import gtk
import gtkhtml2
import gnomevfs
import subprocess

from gettext import gettext as _
from makeTable import toRSTtable
## pygments support
import RegisterPygment
## docutils
from docutils.core import publish_parts


## I'm not satisfied with that
restpluginDir = os.path.dirname(os.path.abspath(__file__))
css = os.path.join(restpluginDir,'restmain.css')
styles = open(css,'r')

START_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Language" content="English" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <style type="text/css">
        %s
    </style>
</head>
<body>"""% (styles.read())

styles.close()

END_HTML = """</body>
</html>
"""

# Menu item example, insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <separator/>
      <placeholder name="ToolsOps_6">
        <menuitem name="preview" action="preview"/>
      </placeholder>
      <placeholder name="ToolsOps_6">
        <menuitem name="table" action="table"/>
      </placeholder>
      <placeholder name="ToolsOps_6">
        <menuitem name="sourcecode" action="sourcecode"/>
      </placeholder>
      <placeholder name="ToolsOps_6">
        <menuitem name="--> HTML" action="--> HTML"/>
      </placeholder>
      <placeholder name="ToolsOps_6">
        <menuitem name="--> LaTeX" action="--> LaTeX"/>
      </placeholder>
      <placeholder name="ToolsOps_6">
        <menuitem name="--> OpenOffice" action="--> OpenOffice"/>
      </placeholder>
      <separator/>
    </menu>
  </menubar>
</ui>
"""

ALLOWED_SCHEME = ('http', 'https', 'ftp', 'ftps', 'mailto', 'file')

class restPlugin(gedit.Plugin):

    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        ## TODO : Maybe have to check the filetype ?

        self._window = window

        # Store data in the window object
        windowdata = dict()
        window.set_data("reStPreviewData", windowdata)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
        scrolled_window.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
        scrolled_window.set_property("shadow-type",gtk.SHADOW_IN)

        html_view = gtkhtml2.View()
        html_doc = gtkhtml2.Document()
        html_doc.connect('request-url', self.request_url)
        html_doc.connect('link-clicked', self.link_clicked)
        html_view.set_document(html_doc)

        html_doc.clear()
        html_doc.open_stream("text/html")
        html_doc.write_stream(START_HTML)
        html_doc.write_stream("<p>reStructuredText viewer</p>")
        html_doc.write_stream(END_HTML)
        html_doc.close_stream()

        scrolled_window.set_hadjustment(html_view.get_hadjustment())
        scrolled_window.set_vadjustment(html_view.get_vadjustment())
        scrolled_window.add(html_view)
        scrolled_window.show_all()

        bottom = window.get_bottom_panel()
        image = gtk.Image()
        image.set_from_icon_name("gnome-mime-text-html", gtk.ICON_SIZE_MENU)
        bottom.add_item(scrolled_window, "reSt Preview", image)
        windowdata["bottom_panel"] = scrolled_window
        windowdata["html_doc"] = html_doc
        windowdata["html_view"] = html_view

        manager = window.get_ui_manager()

        ## Added later
        separator = gtk.SeparatorMenuItem()
        self._action_group = gtk.ActionGroup("reStPluginActions")
        self._action_group.add_actions([("preview", None, _("reSt preview"),
                                         "<Control><Shift>R", _("reSt preview"),
                                         self.on_update_preview),
                                        ("table", None, _("Create Table"),
                                         None, _("Create a reSt table"),
                                         self.on_create_table),
                                        ("sourcecode", None, _("Paste Code"),
                                         None, _("Paste sourcecode"),
                                         self.on_paste_code),
                                        ("--> HTML", None, _("--> HTML"),
                                         None, _("transform to HTML"),
                                         self.on_html),
                                        ("--> LaTeX", None, _("--> LaTeX"),
                                         None, _("transform to LaTeX"),
                                         self.on_latex),
                                        ("--> OpenOffice", None, _("--> OpenOffice"),
                                         None, _("transform to OpenOffice"),
                                         self.on_openoffice),
                                       ])

        # Insert the action group
        manager.insert_action_group(self._action_group, -1)

        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ui_str)

    def deactivate(self, window):
        # Retreive the data of the window object
        windowdata = window.get_data("reStPreviewData")

        # Remove the menu action
        manager = window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

        # Remove the bottom panel
        bottom = window.get_bottom_panel()
        bottom.remove_item(windowdata["bottom_panel"])

    def request_url(self, doc, url, stream):
        gdoc = self._window.get_active_document()
        if not gdoc:
            source_path = None
        else:
            source_path = gdoc.get_location()
            if source_path:
                source_path = gnomevfs.URI(source_path.get_uri())

        if source_path:
            url = source_path.resolve_relative(url)

        try:
            f = gnomevfs.open(url, gnomevfs.OPEN_READ)
        except:
            print "Error opening url", url
            stream.close()
            return

        while True:
            try:
                stream.write(f.read (1024))
            except gnomevfs.EOFError:
                break
        f.close()
        stream.close()

    def link_clicked(self, object, link):
        # Retreive the data of the window object
        windowdata = self._window.get_data("reStPreviewData")

        if link.startswith('#'):
            windowdata['html_view'].jump_to_anchor(link)
            return

        gdoc = self._window.get_active_document()
        if not gdoc:
            source_path = None
        else:
            source_path = gdoc.get_location()
            if source_path:
                source_path = gnomevfs.URI(source_path.get_uri())

        if source_path:
            url = source_path.resolve_relative(link)
        else:
            url = gnomevfs.URI(link)

        command = ['gnome-open', str(url)]

        # Avoid to run the browser as user root
        if os.getuid() == 0 and os.environ.has_key('SUDO_USER'):
            command = ['sudo', '-u', os.environ['SUDO_USER']] + command

        if url.scheme in ALLOWED_SCHEME:
            subprocess.Popen(command)
            return

        print "clicked = %r" % link

    def getSelection(self, window):
        windowdata = window.get_data("reStPreviewData")

        view = window.get_active_view()
        if not view:
            return

        doc = view.get_buffer()

        start = doc.get_start_iter()
        end = doc.get_end_iter()

        if doc.get_selection_bounds():
            start = doc.get_iter_at_mark(doc.get_insert())
            end = doc.get_iter_at_mark(doc.get_selection_bound())

        text = doc.get_text(start, end)

    # Menu activate handlers
    def on_update_preview(self, window):
        # Retreive the data of the window object
        windowdata = self._window.get_data("reStPreviewData")

        view = self._window.get_active_view()
        if not view:
             return

        gdoc = self._window.get_active_document()
        if not gdoc:
            source_path = None
        else:
            source_path = gdoc.get_location()
            if source_path:
                source_path = source_path.get_path()

        doc = view.get_buffer()

        start = doc.get_start_iter()
        end = doc.get_end_iter()

        if doc.get_selection_bounds():
            start = doc.get_iter_at_mark(doc.get_insert())
            end = doc.get_iter_at_mark(doc.get_selection_bound())

        text = doc.get_text(start, end)
        html = publish_parts(text, source_path=source_path, writer_name="html")["html_body"]

        ## Sortie
        sortie = '\n'.join([START_HTML,html,END_HTML])
        fs = open('sortie.html','w')
        fs.write(sortie)
        fs.close()

        p = windowdata["bottom_panel"].get_placement()

        html_doc = windowdata["html_doc"]
        html_doc.clear()
        html_doc.open_stream("text/html")
        html_doc.write_stream(START_HTML)
        html_doc.write_stream(html)
        html_doc.write_stream(END_HTML)
        html_doc.close_stream()

        windowdata["bottom_panel"].set_placement(p)

    def on_latex(self,action):
        doc = self._window.get_active_document()
        filename = doc.get_uri_for_display()[:-4]
        pd = restpluginDir
        os.popen2('python %s/to_tex.py "%s.rst" "%s.tex"'%(pd,filename,filename))

    def on_html(self,action):
        doc = self._window.get_active_document()
        filename = doc.get_uri_for_display()[:-4]
        pd = restpluginDir
        os.popen2('python %s/to_html.py --stylesheet=%s/restmain.css --language=fr "%s.rst" "%s.html"'%(pd,pd,filename,filename))

    def on_openoffice(self,action):
        doc = self._window.get_active_document()
        filename = doc.get_uri_for_display()[:-4]
        pd = restpluginDir
        os.popen2('python %s/to_odt.py --add-syntax-highlighting --stylesheet=%s/default.odt "%s.rst" "%s.odt"'%(pd,pd,filename,filename))

    def on_paste_code(self, action):
        doc = self._window.get_active_document()

        if not doc:
            return

        lines = gtk.clipboard_get().wait_for_text().split('\n')
        to_copy = "\n".join([line for line in lines[1:]])
        doc.insert_at_cursor('..sourcecode:: ChoosenLanguage\n\n    %s\n'%lines[0])
        doc.insert_at_cursor(to_copy + '\n\n')

    def on_create_table(self,action):
        view = self._window.get_active_view()

        if not view:
            return

        indent = view.get_indent()

        doc = view.get_buffer()
        #print 'language=',doc.get_language()

        start = doc.get_start_iter()
        end = doc.get_end_iter()

        if doc.get_selection_bounds():
            start = doc.get_iter_at_mark(doc.get_insert())
            end = doc.get_iter_at_mark(doc.get_selection_bound())

        text = doc.get_text(start, end)
        doc.delete(start,end)

        lines = text.split("\n")
        labels = lines[0].split(',')
        rows = [row.strip().split(',')  for row in lines[1:]]

        doc.insert_at_cursor(toRSTtable([labels]+rows))
