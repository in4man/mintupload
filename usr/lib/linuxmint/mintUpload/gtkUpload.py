#!/usr/bin/env python

# mintUpload
#	Clement Lefebvre <root@linuxmint.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; Version 2
# of the License.

import sys

try:
	import pygtk
	pygtk.require("2.0")
except:
	pass

try:
	import gtk
	import gtk.glade
	import os
	import gettext
	import commands
	from mintUploadCore import *
except:
	print "You do not have all the dependencies!"
	sys.exit(1)

gtk.gdk.threads_init()

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintUpload/locale")

def gtkCustomError(self, detail):
	global statusbar
	message = "<span color='red'>" + detail + "</span>"
	statusbar.push(context_id, message)
	statusbar.get_children()[0].get_children()[0].set_use_markup(True)
	CustomError.error(self, detail)

CustomError.__init__ = gtkCustomError

class gtkSpaceChecker(mintSpaceChecker):
	'''Checks for available space on the service'''

	def run(self):
		global statusbar
		global context_id
		global wTree

		# Get the file's persistence on the service
		if self.service.has_key('persistence'):
			wTree.get_widget("txt_persistence").set_label(str(self.service['persistence']) + " " + _("days"))
			wTree.get_widget("txt_persistence").show()
			wTree.get_widget("lbl_persistence").show()
		else:
			wTree.get_widget("txt_persistence").set_label(_("N/A"))
			wTree.get_widget("txt_persistence").hide()
			wTree.get_widget("lbl_persistence").hide()

		# Get the maximum allowed filesize on the service
		if self.service.has_key('maxsize'):
			maxsizeStr = sizeStr(self.service['maxsize'])
			wTree.get_widget("txt_maxsize").set_label(maxsizeStr)
			wTree.get_widget("txt_maxsize").show()
			wTree.get_widget("lbl_maxsize").show()
		else:
			wTree.get_widget("txt_maxsize").set_label(_("N/A"))
			wTree.get_widget("txt_maxsize").hide()
			wTree.get_widget("lbl_maxsize").hide()

		needsCheck = True
		if not self.service.has_key('space'):
			wTree.get_widget("txt_space").set_label(_("N/A"))
			wTree.get_widget("txt_space").hide()
			wTree.get_widget("lbl_space").hide()
			if not self.service.has_key('maxsize'):
				needsCheck=False

		if needsCheck:
			wTree.get_widget("main_window").window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			wTree.get_widget("combo").set_sensitive(False)
			wTree.get_widget("upload_button").set_sensitive(False)
			statusbar.push(context_id, _("Checking space on the service..."))

			wTree.get_widget("frame_progress").hide()

			# Check the filesize
			try:
				self.check()

			except ConnectionError:
				statusbar.push(context_id, "<span color='red'>" + _("Could not connect to the service.") + "</span>")

			except FilesizeError:
				statusbar.push(context_id, "<span color='red'>" + _("File too big or not enough space on the service.") + "</span>")

			else:
				# Display the available space left on the service
				if self.service.has_key('space'):
					pctSpace = float(self.available) / float(self.total) * 100
					pctSpaceStr = sizeStr(self.available) + " (" + str(int(pctSpace)) + "%)"
					wTree.get_widget("txt_space").set_label(pctSpaceStr)
					wTree.get_widget("txt_space").show()
					wTree.get_widget("lbl_space").show()

				# Activate upload button
				statusbar.push(context_id, "<span color='green'>" + _("Service ready. Space available.") + "</span>")
				wTree.get_widget("upload_button").set_sensitive(True)

			finally:
				label = statusbar.get_children()[0].get_children()[0]
				label.set_use_markup(True)
				wTree.get_widget("combo").set_sensitive(True)
				wTree.get_widget("main_window").window.set_cursor(None)
				wTree.get_widget("main_window").resize(*wTree.get_widget("main_window").size_request())

class gtkUploader(mintUploader):
	'''Wrapper for the gtk management of mintUploader'''

	def run(self):
		global progressbar
		global statusbar
		global wTree

		wTree.get_widget("upload_button").set_sensitive(False)
		wTree.get_widget("combo").set_sensitive(False)

		statusbar.push(context_id, _("Connecting to the service..."))
		wTree.get_widget("main_window").window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		wTree.get_widget("frame_progress").show()
		progressbar.set_fraction(0)
		progressbar.set_text("0%")

		try:
			self.upload()
		except:
			try:    raise CustomError(_("Upload failed."))
			except: pass

		else:
			# Report success
			progressbar.set_fraction(1)
			progressbar.set_text("100%")
			statusbar.push(context_id, "<span color='green'>" + _("File uploaded successfully.") + "</span>")
			statusbar.get_children()[0].get_children()[0].set_use_markup(True)

			#If service is Mint then show the URL
			if self.service.has_key('url'):
				wTree.get_widget("txt_url").set_text(self.service['url'])
				wTree.get_widget("txt_url").show()
				wTree.get_widget("lbl_url").show()

		finally:
			wTree.get_widget("main_window").window.set_cursor(None)

	def progress(self, message):
		global statusbar
		statusbar.push(context_id, message)
		mintUploader.progress(self, message)

	def asciicallback(self, buffer):
		global progressbar

		self.so_far = self.so_far+len(buffer)-1
		pct = float(self.so_far)/self.filesize
		pctStr = str(int(pct * 100))
		progressbar.set_fraction(pct)
		progressbar.set_text(pctStr + "%")

		# Output cli for debugging, bugfix
		self.so_far = self.so_far-len(buffer)+1
		mintUploader.asciicallback(self, buffer)
		return

class mintUploadWindow:
	"""This is the main class for the application"""

	def __init__(self, filename):
		global wTree
		global name
		global statusbar

		self.filename = filename
		name = os.path.basename(filename)
		self.iconfile = "/usr/lib/linuxmint/mintSystem/icon.png"

		# Set the Glade file
		self.gladefile = "/usr/lib/linuxmint/mintUpload/mintUpload.glade"
		wTree = gtk.glade.XML(self.gladefile,"main_window")

		wTree.get_widget("main_window").connect("destroy", gtk.main_quit)
		wTree.get_widget("main_window").set_icon_from_file(self.iconfile)

		# i18n
		wTree.get_widget("label2").set_label("<b>" + _("Upload service") + "</b>")
		wTree.get_widget("label3").set_label("<b>" + _("Local file") + "</b>")
		wTree.get_widget("label4").set_label("<b>" + _("Remote file") + "</b>")
		wTree.get_widget("label187").set_label(_("Name:"))
		wTree.get_widget("lbl_space").set_label(_("Free space:"))
		wTree.get_widget("lbl_maxsize").set_label(_("Max file size:"))
		wTree.get_widget("lbl_persistence").set_label(_("Persistence:"))
		wTree.get_widget("label195").set_label(_("Path:"))
		wTree.get_widget("label193").set_label(_("Size:"))
		wTree.get_widget("label190").set_label(_("Upload progress:"))
		wTree.get_widget("lbl_url").set_label(_("URL:"))

		fileMenu = gtk.MenuItem(_("_File"))
		fileSubmenu = gtk.Menu()
		fileMenu.set_submenu(fileSubmenu)
		closeMenuItem = gtk.ImageMenuItem(gtk.STOCK_CLOSE)
		closeMenuItem.get_child().set_text(_("Close"))
		closeMenuItem.connect("activate", gtk.main_quit)
		fileSubmenu.append(closeMenuItem)

		helpMenu = gtk.MenuItem(_("_Help"))
		helpSubmenu = gtk.Menu()
		helpMenu.set_submenu(helpSubmenu)
		aboutMenuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		aboutMenuItem.get_child().set_text(_("About"))
		aboutMenuItem.connect("activate", self.open_about)
		helpSubmenu.append(aboutMenuItem)

		editMenu = gtk.MenuItem(_("_Edit"))
		editSubmenu = gtk.Menu()
		editMenu.set_submenu(editSubmenu)
		prefsMenuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		prefsMenuItem.get_child().set_text(_("Services"))
		prefsMenuItem.connect("activate", self.open_services, wTree.get_widget("combo"))
		editSubmenu.append(prefsMenuItem)

		wTree.get_widget("menubar1").append(fileMenu)
		wTree.get_widget("menubar1").append(editMenu)
		wTree.get_widget("menubar1").append(helpMenu)
		wTree.get_widget("menubar1").show_all()

		self.reload_services(wTree.get_widget("combo"))

		cell = gtk.CellRendererText()
		wTree.get_widget("combo").pack_start(cell)
		wTree.get_widget("combo").add_attribute(cell,'text',0)

		wTree.get_widget("combo").connect("changed", self.comboChanged)
		wTree.get_widget("upload_button").connect("clicked", self.upload)
		wTree.get_widget("cancel_button").connect("clicked", gtk.main_quit)

		# Print the name of the file in the GUI
		wTree.get_widget("txt_file").set_label(self.filename)

		# Calculate the size of the file
		self.filesize = os.path.getsize(self.filename)
		wTree.get_widget("txt_size").set_label(sizeStr(self.filesize))

		if len(self.services) == 1:
			wTree.get_widget("combo").set_active(0)
			self.comboChanged(None)

		statusbar = wTree.get_widget("statusbar")

	def reload_services(self, combo):
		model = gtk.TreeStore(str)
		combo.set_model(model)
		self.services = read_services()
		for service in self.services:
			iter = model.insert_before(None, None)
			model.set_value(iter, 0, service['name'])
		del model

	def open_about(self, widget):
		dlg = gtk.AboutDialog()
		dlg.set_title(_("About") + " - mintUpload")
		version = commands.getoutput("mint-apt-version mintupload 2> /dev/null")
		dlg.set_version(version)
		dlg.set_program_name("mintUpload")
		dlg.set_comments(_("File uploader for Linux Mint"))
		try:
		    h = open('/usr/lib/linuxmint/mintSystem/GPL.txt','r')
		    s = h.readlines()
		    gpl = ""
		    for line in s:
		    	gpl += line
		    h.close()
		    dlg.set_license(gpl)
		except Exception, detail:
		    print detail

		dlg.set_authors([
			"Clement Lefebvre <root@linuxmint.com>",
			"Philip Morrell <ubuntu.emorrp1@xoxy.net>",
			"Manuel Sandoval <manuel@slashvar.com>",
			"Dennis Schwertel <s@digitalkultur.net>"
		])
		dlg.set_icon_from_file(self.iconfile)
		dlg.set_logo(gtk.gdk.pixbuf_new_from_file(self.iconfile))
		def close(w, res):
		    if res == gtk.RESPONSE_CANCEL:
		        w.hide()
		dlg.connect("response", close)
		dlg.show()

	def open_services(self, widget, combo):
		wTree = gtk.glade.XML(self.gladefile, "services_window")
		treeview_services = wTree.get_widget("treeview_services")
		treeview_services_system = wTree.get_widget("treeview_services_system")

		wTree.get_widget("services_window").set_title(_("Services") + " - mintUpload")
		wTree.get_widget("services_window").set_icon_from_file(self.iconfile)
		wTree.get_widget("services_window").show()

		wTree.get_widget("button_close").connect("clicked", self.close_window, wTree.get_widget("services_window"), combo)
		wTree.get_widget("services_window").connect("destroy", self.close_window, wTree.get_widget("services_window"), combo)
		wTree.get_widget("toolbutton_add").connect("clicked", self.add_service, treeview_services)
		wTree.get_widget("toolbutton_edit").connect("clicked", self.edit_service_toolbutton, treeview_services)
		wTree.get_widget("toolbutton_remove").connect("clicked", self.remove_service, treeview_services)

		column1 = gtk.TreeViewColumn(_("Services"), gtk.CellRendererText(), text=0)
		column1.set_sort_column_id(0)
		column1.set_resizable(True)
		treeview_services.append_column(column1)
		treeview_services.set_headers_clickable(True)
		treeview_services.set_reorderable(False)
		treeview_services.show()
		column1 = gtk.TreeViewColumn(_("System-wide services"), gtk.CellRendererText(), text=0)
		treeview_services_system.append_column(column1)
		treeview_services_system.show()
		self.load_services(treeview_services, treeview_services_system)
		treeview_services.connect("row-activated", self.edit_service);

	def load_services(self, treeview_services, treeview_services_system):
		usermodel = gtk.TreeStore(str)
		usermodel.set_sort_column_id( 0, gtk.SORT_ASCENDING )
		sysmodel = gtk.TreeStore(str)
		sysmodel.set_sort_column_id( 0, gtk.SORT_ASCENDING )
		models = {
			'user':usermodel,
			'system':sysmodel
		}
		treeview_services.set_model(models['user'])
		treeview_services_system.set_model(models['system'])

		self.services = read_services()
		for service in self.services:
			iter = models[service['loc']].insert_before(None, None)
			models[service['loc']].set_value(iter, 0, service['name'])

		del usermodel
		del sysmodel

	def close_window(self, widget, window, combo=None):
		window.hide()
		if (combo != None):
			self.reload_services(combo)

	def add_service(self, widget, treeview_services):
		wTree = gtk.glade.XML(self.gladefile, "dialog_add_service")
		wTree.get_widget("dialog_add_service").set_title(_("New service"))
		wTree.get_widget("dialog_add_service").set_icon_from_file(self.iconfile)
		wTree.get_widget("dialog_add_service").show()
		wTree.get_widget("lbl_name").set_label(_("Name:"))
		wTree.get_widget("button_ok").connect("clicked", self.new_service, wTree.get_widget("dialog_add_service"), wTree.get_widget("txt_name"), treeview_services)
		wTree.get_widget("button_cancel").connect("clicked", self.close_window, wTree.get_widget("dialog_add_service"))

	def new_service(self, widget, window, entry, treeview_services):
		service = Service('/usr/lib/linuxmint/mintUpload/sample.service')
		sname = entry.get_text()
		if sname:
			model = treeview_services.get_model()
			iter = model.insert_before(None, None)
			model.set_value(iter, 0, sname)
			service.filename = config_paths['user'] + sname
			service.write()
		self.close_window(None, window)
		self.edit_service(treeview_services, model.get_path(iter), 0)

	def edit_service_toolbutton(self, widget, treeview_services):
		selection = treeview_services.get_selection()
		(model, iter) = selection.get_selected()
		self.edit_service(treeview_services, model.get_path(iter), 0)

	def edit_service(self,widget, path, column):
		model=widget.get_model()
		iter = model.get_iter(path)
		sname = model.get_value(iter, 0)
		file = config_paths['user'] + sname

		wTree = gtk.glade.XML(self.gladefile, "dialog_edit_service")
		wTree.get_widget("dialog_edit_service").set_title(_("Edit service"))
		wTree.get_widget("dialog_edit_service").set_icon_from_file(self.iconfile)
		wTree.get_widget("dialog_edit_service").show()
		wTree.get_widget("button_ok").connect("clicked", self.modify_service, wTree.get_widget("dialog_edit_service"), wTree, file)
		wTree.get_widget("button_cancel").connect("clicked", self.close_window, wTree.get_widget("dialog_edit_service"))

		#i18n
		wTree.get_widget("lbl_type").set_label(_("Type:"))
		wTree.get_widget("lbl_hostname").set_label(_("Hostname:"))
		wTree.get_widget("lbl_port").set_label(_("Port:"))
		wTree.get_widget("lbl_username").set_label(_("Username:"))
		wTree.get_widget("lbl_password").set_label(_("Password:"))
		wTree.get_widget("lbl_timestamp").set_label(_("Timestamp:"))
		wTree.get_widget("lbl_path").set_label(_("Path:"))

		wTree.get_widget("lbl_hostname").set_tooltip_text(_("Hostname or IP address, default: mint-space.com"))
		wTree.get_widget("txt_hostname").set_tooltip_text(_("Hostname or IP address, default: mint-space.com"))

		wTree.get_widget("lbl_port").set_tooltip_text(_("Remote port, default is 21 for FTP, 22 for SFTP and SCP"))
		wTree.get_widget("txt_port").set_tooltip_text(_("Remote port, default is 21 for FTP, 22 for SFTP and SCP"))

		wTree.get_widget("lbl_username").set_tooltip_text(_("Username, defaults to your local username"))
		wTree.get_widget("txt_username").set_tooltip_text(_("Username, defaults to your local username"))

		wTree.get_widget("lbl_password").set_tooltip_text(_("Password, by default: password-less SCP connection, null-string FTP connection, ~/.ssh keys used for SFTP connections"))
		wTree.get_widget("txt_password").set_tooltip_text(_("Password, by default: password-less SCP connection, null-string FTP connection, ~/.ssh keys used for SFTP connections"))

		wTree.get_widget("lbl_timestamp").set_tooltip_text(_("Timestamp format (strftime). By default:") + defaults['format'])
		wTree.get_widget("txt_timestamp").set_tooltip_text(_("Timestamp format (strftime). By default:") + defaults['format'])

		wTree.get_widget("lbl_path").set_tooltip_text(_("Directory to upload to. <TIMESTAMP> is replaced with the current timestamp, following the timestamp format given. By default: ."))
		wTree.get_widget("txt_path").set_tooltip_text(_("Directory to upload to. <TIMESTAMP> is replaced with the current timestamp, following the timestamp format given. By default: ."))

		try:
			config = Service(file)
			try:
				model = wTree.get_widget("combo_type").get_model()
				iter = model.get_iter_first()
				while (iter != None and model.get_value(iter, 0) != config['type'].lower()):
					iter = model.iter_next(iter)
				wTree.get_widget("combo_type").set_active_iter(iter)
			except:
				pass
			try:
				wTree.get_widget("txt_hostname").set_text(config['host'])
			except:
				wTree.get_widget("txt_hostname").set_text("")
			try:
				wTree.get_widget("txt_port").set_text(config['port'])
			except:
				wTree.get_widget("txt_port").set_text("")
			try:
				wTree.get_widget("txt_username").set_text(config['user'])
			except:
				wTree.get_widget("txt_username").set_text("")
			try:
				wTree.get_widget("txt_password").set_text(config['pass'])
			except:
				wTree.get_widget("txt_password").set_text("")
			try:
				wTree.get_widget("txt_timestamp").set_text(config['format'])
			except:
				wTree.get_widget("txt_timestamp").set_text("")
			try:
				wTree.get_widget("txt_path").set_text(config['path'])
			except:
				wTree.get_widget("txt_path").set_text("")
		except Exception, detail:
			print detail

	def modify_service(self, widget, window, wTree, file):
		try:
			model = wTree.get_widget("combo_type").get_model()
			iter = 	wTree.get_widget("combo_type").get_active_iter()

			# Get configuration
			config = {}
			config['type'] = model.get_value(iter, 0)
			config['host'] = wTree.get_widget("txt_hostname").get_text()
			config['port'] = wTree.get_widget("txt_port").get_text()
			config['user'] = wTree.get_widget("txt_username").get_text()
			config['pass'] = wTree.get_widget("txt_password").get_text()
			config['format'] = wTree.get_widget("txt_timestamp").get_text()
			config['path'] = wTree.get_widget("txt_path").get_text()

			# Write to service's config file
			s = Service(file)
			s.merge(config)
			s.write()
		except Exception, detail:
			print detail
		window.hide()

	def remove_service(self, widget, treeview_services):
		(model, iter) = treeview_services.get_selection().get_selected()
		if (iter != None):
			service = model.get_value(iter, 0)
			for s in self.services:
				if s['name'] == service:
					s.remove()
					self.services.remove(s)
			model.remove(iter)

	def comboChanged(self, widget):
		'''Change the selected service'''

		global progressbar
		global statusbar
		global wTree
		global context_id
		global selected_service

		progressbar = wTree.get_widget("progressbar")
		statusbar = wTree.get_widget("statusbar")
		context_id = statusbar.get_context_id("mintUpload")

		# Get the selected service
		model = wTree.get_widget("combo").get_model()
		active = wTree.get_widget("combo").get_active()
		if active < 0:
			return
		selectedService = model[active][0]

		self.services = read_services()
		for service in self.services:
			if service['name'] == selectedService:
				selected_service = service
				checker = gtkSpaceChecker(selected_service, self.filesize)
				checker.start()
				return True

	def upload(self, widget):
		'''Start the upload process'''

		uploader = gtkUploader(selected_service, self.filename)
		uploader.start()
		return True

if __name__ == "__main__":
	mainwin = mintUploadWindow(sys.argv[1])
	gtk.main()
