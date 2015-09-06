import os,sys,re
import xbmc
import xbmcplugin
import xbmcgui
import urllib
from dudehere.routines import *
from dudehere.routines.vfs import VFSClass
Views = {
		"list": 50,
		"big list": 51,
		"thumbnail": 500,
		"small thumb": 522,
		"fanart": 508,
		"poster wrap": 501,
		"media info": 504,
		"media info 2": 503,
		"media info 3": 515,
		"wide": 505,
		"default folder view": 50,
		"default tv view": 515,
		"default movie view": 551
}	
vfs = VFSClass()
class ContextMenu:
	def __init__(self):
		self.commands = []

	def add(self, text, arguments={}):
		cmd = self._build(arguments)
		self.commands.append((text, cmd, ''))
	
	def _build(self, arguments, plugin=False):
		query = urllib.urlencode(arguments)
		if plugin:
			cmd = 'XBMC.RunPlugin(%s?%s)' % (ADDON_ID, query)
		else:
			cmd = ADDON_ID + '?' + query
		return cmd

	def get(self):
		return self.commands

class Plugin():
	def __init__(self):
		self.args = ADDON.parse_query(sys.argv[2])
		self.dispatcher = {}
		self.kargs = {}
		self.ENABLE_DEFAULT_VIEWS = True
	
	def arg(self, k):
		if k in self.args.keys():
			return self.args[k]
		else:
			return None
		
	def register(self, mode, target, kargs=None):
		if isinstance(mode, list):
			for foo in mode:
				self.dispatcher[foo] = target
				self.kargs[foo] = kargs
		else:
			self.dispatcher[mode] = target
			self.kargs[mode] = kargs
		
	def run(self):
		#ADDON.log(self.args)
		#try:
		if self.kargs[self.args['mode']] is None:
			self.dispatcher[self.args['mode']]()
		else:
			self.mode = self.args['mode']
			self.dispatcher[self.args['mode']](*self.kargs[self.args['mode']])
#		except:
#			ADDON.log('This function is not implemented or internal error.', 1)
		
	def add_menu_item(self, data, info, image=None, fanart='None', menu=None, isPlayable=False, require_auth=False):
		if isPlayable: 
			isFolder = False
		else:
			isFolder = True
		if not menu:
			menu=ContextMenu()	
		ADDON.add_directory(data, info, img=image, fanart=fanart, is_folder=isFolder, contextmenu_items=menu.get())
		
		
	def eod(self, view='default folder view', content=None, viewid=None):
		if view=='custom':
			self.set_view('custom', content=content, viewid=viewid)
		else:
			self.set_view(view,content=content)
		ADDON.end_of_directory()
	
	def set_view(self, view, content=None, viewid=None):
		if self.ENABLE_DEFAULT_VIEWS:
			if content:
				xbmcplugin.setContent(int(sys.argv[1]), content)
			if not viewid:
				viewid = Views[view]
			xbmc.executebuiltin("Container.SetViewMode(%s)" % viewid)
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )	
	
	def dialog_input(self, title):
		kb = xbmc.Keyboard('', title, False)
		kb.doModal()
		if (kb.isConfirmed()):
			text = kb.getText()
			if text != '':
				return text
		return None	
	
	def dialog_ok(self, title="", m1="", m2="", m3=""):
		dialog = xbmcgui.Dialog()
		dialog.ok(title, m1, m2, m3)
	
	def confirm(self, title, m1='', m2=''):
		dialog = xbmcgui.Dialog()
		return dialog.yesno(title, m1, m2)
	
	def notify(self, title, message, timeout=1500):
		cmd = "XBMC.Notification('%s', '%s', %s)" % (title, message, timeout)
		xbmc.executebuiltin(cmd)
		
	def refresh(self):
		xbmc.executebuiltin("Container.Refresh")
	
	def play_stream(self, url, metadata={"cover_url": ""}):
		listitem = xbmcgui.ListItem('video', iconImage=metadata['cover_url'], thumbnailImage=metadata['cover_url'], path=url)
		listitem.setProperty('IsPlayable', 'true')
		listitem.setPath(url)
		listitem.setInfo('video', metadata)
		try:
			xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
		except Exception, e:
			ADDON.log( e )

class ProgressBar(xbmcgui.DialogProgress):
	def __init__(self, *args, **kwargs):
		xbmcgui.DialogProgress.__init__(self, *args, **kwargs)
		self._silent = False
		self._index = 0
		self._total = 0
		self._percent = 0
	def new(self, heading, total):
		if not self._silent:
			self._index = 0
			self._total = total
			self._percent = 0
			self._heading = heading
			self.create(heading)
			self.update(0, heading, '')
	def update_subheading(self, subheading):
		self.update(self._percent, self._heading, subheading)
		
	def next(self, subheading):
		if not self._silent:
			self._index = self._index + 1
			self._percent = self._index * 100 / self._total
			self.update(self._percent, self._heading, subheading)
		
class TextBox:
	# constants
	WINDOW = 10147
	CONTROL_LABEL = 1
	CONTROL_TEXTBOX = 5

	def __init__( self, *args, **kwargs):
		# activate the text viewer window
		xbmc.executebuiltin( "ActivateWindow(%d)" % ( self.WINDOW, ) )
		# get window
		self.window = xbmcgui.Window( self.WINDOW )
		# give window time to initialize
		xbmc.sleep( 500 )


	def setControls( self ):
		#get header, text
		heading, text = self.message
		# set heading
		self.window.getControl( self.CONTROL_LABEL ).setLabel( "%s - %s v%s" % ( heading, ADDON_NAME, VERSION) )
		# set text
		self.window.getControl( self.CONTROL_TEXTBOX ).setText( text )

	def show(self, heading, text):
		# set controls

		self.message = heading, text
		self.setControls()		