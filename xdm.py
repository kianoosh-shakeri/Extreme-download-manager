# -*- coding: UTF-8 -*-

import os
import gettext
import glob
import wx
from pySmartDL import SmartDL as downloader
#constants
EXIT_ID=1000
CONNECT_ID=1001
DISCONNECT_ID=1002
REMEMBERME_ID=1003
DOWNLOAD_ID=1004
BACKTODEFAULTPAGE_ID=1005
CHANGELANGUAGE_ID=1006
#initiate translation
langstring=""
try:
	with open("locale/savedlng", "r") as f:
		langstring=f.read()
except Exception as e:
	langstring=""
if langstring != "":
	lang=gettext.translation(langstring, localedir='locale', languages=[langstring])
else:
	lang=gettext.translation("en", localedir='locale', languages=["en"])
lang.install()

class application(wx.Frame):
	def __init__(self, parent, title):
		super(application, self).__init__(parent, title=title, size=(500, 300))
		#constant event bindings
		#this event is raised usually when cancel buttons are pressed
		self.Bind(wx.EVT_BUTTON, self.BackToDefaultPage, id=BACKTODEFAULTPAGE_ID)
		#define what happens when the user exits
		self.Bind(wx.EVT_CLOSE, self.OnQuit)
		#doing this makes me be able to place elements in a panel so they are accessible with TAB
		self.firstpanel=wx.Panel(self)
		#this dictionary contains in-app elements for easier access
		self.elements={}
		self.DefaultPage()
		self.firstpanel.Show()
	
	def CreateDefaultMenuBar(self):
		self.menubar=wx.MenuBar()
		file=wx.Menu()
		file.Append(wx.MenuItem(file, DOWNLOAD_ID, _("add new download")+"\tALT+A"))
		file.Append(wx.MenuItem(file, CHANGELANGUAGE_ID, _("change language")+"\tALT+C"))
		file.Append(wx.MenuItem(file, EXIT_ID, _("exit")+"\tALT+X"))
		self.menubar.Append(file, "&"+_("file"))
		self.SetMenuBar(self.menubar)
		self.Bind(wx.EVT_MENU, self.closeapp, id=EXIT_ID)
		self.Bind(wx.EVT_MENU, self.downloadclicked, id=DOWNLOAD_ID)
		self.Bind(wx.EVT_MENU, self.LanguageSelector, id=CHANGELANGUAGE_ID)
	def ResetElements(self):
		for i in list(self.elements):
			try:
				#stopping stuff before killing them
				#making sure the downloader is resumed before stopping it. It looks like it can't stop downloading when is paused so we quickly unpause the download and stop it
				if i == "downloader":
					print("unpausing download... ")
					if self.elements[i].get_status() == "paused":
						self.elements[i].resume()
				if hasattr(self.elements[i], "stop"):
					self.elements[i].stop()
				if hasattr(self.elements[i], "Stop"):
					self.elements[i].Stop()
				if hasattr(self.elements[i], "Destroy"):
					self.elements[i].Destroy()
				del self.elements[i]
			except Exception as e:
				wx.MessageDialog(self.firstpanel, str(e), _("error")).ShowModal()
				del self.elements[i]
		self.elements={}
	#pages
	def DefaultPage(self):
		self.ResetElements()
		self.CreateDefaultMenuBar()
		self.elements["helplabel"]=wx.StaticText(self.firstpanel, wx.ID_ANY, _("to start a download, select Add New Download from the file menu"))
		self.elements['helplabel'].SetFocus()
	def LanguageSelectorPage(self):
		self.ResetElements()
		#languages elements should always be first_two_letter_starting_of_a_language-actual_language_name
		languages=['en-english', 
		'fa-پارسی', 
		'de-deutsche',
		'es-Spanish', 
		'ge-georgian']
		self.elements['cancelbutton']=wx.Button(self.firstpanel, id=BACKTODEFAULTPAGE_ID, label=_("cancel"))
		self.elements['listlabel']=wx.StaticText(self.firstpanel, wx.ID_ANY, label=_("select a language"))
		self.elements['langlist']=wx.ListCtrl(self.firstpanel)
		for i in range(len(languages)):
			self.elements['langlist'].InsertItem(i, languages[i])
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.SelectLanguage, self.elements['langlist'])
		self.elements['langlist'].SetFocus()
	def NewDownloadPage(self):
		self.ResetElements()
		self.SetMenuBar(None)
		self.elements['addresscaption']=wx.StaticText(self.firstpanel, wx.ID_ANY, label=_("enter download link here"))
		self.elements['address']=wx.TextCtrl(self.firstpanel, value=self.GetClipboard())
		self.elements['pathlabel']=wx.StaticText(self.firstpanel, wx.ID_ANY, label=_("where should this file be saved to? "))
		self.elements['path']=wx.TextCtrl(self.firstpanel, value=os.path.expanduser("~\\downloads"))
		self.elements['startdownloadbutton']=wx.Button(self.firstpanel, wx.ID_ANY, label=_("start download"))
		self.elements['startdownloadbutton'].Bind(wx.EVT_BUTTON, self.BeginDownload)
		self.elements['cancelbutton']=wx.Button(self.firstpanel, BACKTODEFAULTPAGE_ID, label=_("cancel"))
		self.elements['address'].SetFocus()
	def BeginDownload(self, e):
		val=self.elements['address'].GetValue()
		if val != "" and "/" in val and ":" in val and "." in val:
			if val[0:4] == "http" or val[0:3] == "ftp":
				self.InitiateDownload(self.elements['address'].GetValue(), self.elements['path'].GetValue())
			else:
				wx.MessageDialog(self.firstpanel, _("wrong protocol set. Supported protocols are http* and ftp"), _("error")).ShowModal()
		else:
			wx.MessageDialog(self.firstpanel, _("wrong download link set"), _("error")).ShowModal()
	def InitiateDownload(self, address, path):
		self.ResetElements()
		self.elements['statlistlabel']=wx.StaticText(self.firstpanel, id=wx.ID_ANY, label=_("download info"))
		self.elements['statlist']=wx.ListCtrl(self.firstpanel, style=wx.LC_REPORT)
		self.elements['statlist'].InsertColumn(0, _("info"))
		self.elements['statlist'].InsertColumn(1, _("state"))
		self.elements['statlist'].InsertItem(0, _("download progress"))
		self.elements['statlist'].InsertItem(1, _("estimated time remaining"))
		self.elements['statlist'].InsertItem(2, _("transfer rate"))
		self.elements['statlist'].InsertItem(3, _("downloaded size"))
		self.elements['statlist'].InsertItem(4, _("file size"))
		self.elements['statlist'].InsertItem(5, _("status"))
		self.elements['timer']=wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.UpdateDownloadingInfo, self.elements['timer'])
		try:
			self.elements['downloader']=downloader(address, path, threads=3)
			self.elements['downloader'].start(False)
			self.elements['timer'].Start(200)
			self.elements['pausebutton']=wx.Button(self.firstpanel, wx.ID_ANY, label=_("pause"))
			self.elements['pausebutton'].Bind(wx.EVT_BUTTON, self.PauseDownload)
			self.elements['canceldownloadbutton']=wx.Button(self.firstpanel, BACKTODEFAULTPAGE_ID, label=_("cancel"))
			self.elements['pausebutton'].SetFocus()
		except Exception as e:
			wx.MessageDialog(self.firstpanel, str(e), "error").ShowModal()
			self.DefaultPage()
	def UpdateDownloadingInfo(self, e):
		self.elements['statlist'].SetItem(0, 1, str(round(self.elements['downloader'].get_progress()*100, 1))+" %")
		self.elements['statlist'].SetItem(1, 1, self.elements['downloader'].get_eta(True))
		self.elements['statlist'].SetItem(2, 1, self.elements['downloader'].get_speed(True))
		self.elements['statlist'].SetItem(3, 1, self.elements['downloader'].get_dl_size(True))
		self.elements['statlist'].SetItem(4, 1, self.elements['downloader'].get_final_filesize(True))
		self.elements['statlist'].SetItem(5, 1, _(self.elements['downloader'].get_status()))
		if len(self.elements['downloader'].get_errors())>0:
			self.elements['timer'].Stop()
			errors=self.elements['downloader'].get_errors()
			for i in errors:
				wx.MessageDialog(self.firstpanel, str(i), _("error")).ShowModal()
			self.DefaultPage()
		if self.elements['downloader'].isFinished():
			self.elements['timer'].Stop()
			if len(self.elements['downloader'].get_errors()) <= 0 and self.elements['downloader'].isSuccessful():
				wx.MessageDialog(self.firstpanel, _("download completed successfully. The file saved in")+" "+self.elements['downloader'].get_dest(), _("download complete")).ShowModal()
				self.DefaultPage()
			else:
				errors=self.elements['downloader'].get_errors()
				if len(errors) > 0:
					for i in errors:
						wx.MessageDialog(self.firstpanel, str(i), _("error")).ShowModal()
				self.DefaultPage()
	def PauseDownload(self, e):
		self.elements['downloader'].pause()
		self.elements['pausebutton'].SetLabel(_("resume"))
		self.elements['pausebutton'].Bind(wx.EVT_BUTTON, self.ResumeDownload)
		self.elements['timer'].Stop()#updating status. It fails at updating status because the timer is stopped, so we do it manually
		self.elements['statlist'].SetItem(5, 1, _(self.elements['downloader'].get_status()))
	def ResumeDownload(self, e):
		self.elements['downloader'].resume()
		self.elements['pausebutton'].SetLabel(_("pause"))
		self.elements['pausebutton'].Bind(wx.EVT_BUTTON, self.PauseDownload)
		self.elements['timer'].Start(200)
	def BackToDefaultPage(self, e):
		self.DefaultPage()
	def downloadclicked(self, e):
		self.NewDownloadPage()
	def LanguageSelector(self, e):
		self.LanguageSelectorPage()
	def SelectLanguage(self, e):
		try:
			langstr=self.elements['langlist'].GetItemText(self.elements['langlist'].GetFocusedItem())
			if langstr != "":
				langstr=langstr.replace(langstr[langstr.index("-"):], "")
				lng=gettext.translation(langstr, localedir='locale', languages=[langstr])
				lng.install()
				with open("locale/savedlng", "w") as f:
					f.write(langstr)
				self.DefaultPage()
			else:
				self.DefaultPage()
		except Exception as e:
			wx.MessageDialog(self.firstpanel, str(e), _("error")).ShowModal()
			self.ResetElements()
			self.Destroy()
	def closeapp(self, e):
		self.ResetElements()
		self.Destroy()
	def OnQuit(self, e):
		self.ResetElements()
		self.Destroy()
	def GetClipboard(self):
		if wx.TheClipboard.Open():
			data = wx.TextDataObject()
			if wx.TheClipboard.GetData(data):
				t = data.GetText()
		wx.TheClipboard.Close()
		return t



app=wx.App()
gui=application(None, _("extreme download manager"))
gui.Show()
app.MainLoop()