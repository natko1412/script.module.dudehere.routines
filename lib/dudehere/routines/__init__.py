import sys
import os
import xbmc
import xbmcaddon
import os
import unicodedata
from addon.common.addon import Addon

ARGS = sys.argv
try:
	int(ARGS[1])
except:
	ARGS.insert(1, -1)
try: 
	str(ARGS[2])
except:
	ARGS.insert(2, "?/fake")

def enum(*sequential, **named):
	enums = dict(zip(sequential, range(len(sequential))), **named)
	reverse = dict((value, key) for key, value in enums.iteritems())
	enums['r_map'] = reverse
	return type('Enum', (), enums)

class MyAddon(Addon):
	def log(self, msg, level=0):
		if level==1 or self.get_setting('log_level')=="1":
			msg = unicodedata.normalize('NFKD', unicode(msg)).encode('ascii','ignore')
			xbmc.log('%s: %s' % (self.get_name(), msg))
	def str2bool(self, v):
		if not v: return False
		return v.lower() in ("yes", "true", "t", "1")
	def get_bool_setting(self, k):
		return(self.str2bool(self.get_setting(k)))
	def raise_notify(self, title, message, time=3000):
		xbmc.executebuiltin("XBMC.Notification('"+title+"','"+message+"',time)")

ADDON_ID = xbmcaddon.Addon().getAddonInfo('id')
ADDON_NAME =  xbmcaddon.Addon().getAddonInfo('name')
ADDON = MyAddon(ADDON_ID,ARGS)
ADDON_NAME = ADDON.get_name()
VERSION = ADDON.get_version()
ROOT_PATH = ADDON.get_path()
DATA_PATH = ADDON.get_profile()
ARTWORK = 'resources/artwork'
QUALITY = enum(HD1080=6, HD720=5, SD480=4, UNKNOWN=3, LOW=2, POOR=1)

