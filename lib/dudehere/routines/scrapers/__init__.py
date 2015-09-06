import sys
import os
import re
import urllib, urllib2
import json
import unicodedata
import xbmcgui
import urlresolver
import hashlib
from dudehere.routines import *
from dudehere.routines.threadpool import ThreadPool
from addon.common.net import Net
from BeautifulSoup import BeautifulSoup
from dudehere.routines.vfs import VFSClass
from __builtin__ import None
vfs = VFSClass()
DECAY = 2
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_PATH = vfs.join(DATA_PATH,'cookies')
if not vfs.exists(COOKIE_PATH): vfs.mkdir(COOKIE_PATH, recursive=True)
sys.path.append(SCRAPER_DIR)

from dudehere.routines.database import SQLiteDatabase as DatabaseAPI	
class MyDatabaseAPI(DatabaseAPI):
	def _initialize(self):
		SQL = 'CREATE TABLE IF NOT EXISTS "search_cache"("cache_id" INTEGER PRIMARY KEY AUTOINCREMENT, "hash" TEXT NOT NULL, "display" TEXT NOT NULL, "url" TEXT NOT NULL, "ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
		self.execute(SQL)
		self.commit()
		ADDON.addon.setSetting('database_init_sqlite', 'true')
DB_TYPE = 'sqlite'
DB_FILE = vfs.join(DATA_PATH, "cache.db")
DB=MyDatabaseAPI(DB_FILE)

class ScraperResult():
	bitrate_color = 'purple'
	hostname_color = 'red'
	size_color = 'blue'
	extension_color = 'green'
	quality_color = 'yellow'
	service_color = 'white'
	

	def __init__(self, service, hostname, url, text=None):
		self.hostname = hostname
		self.service = service
		self.text = text
		self.url = url
		self.bitrate = None
		self.size = None
		self.extension = None
		self.quality = None
	
	def colorize(self, attrib, value):
		color = getattr(self, attrib+'_color')
		if attrib == 'bitrate':
			return "[COLOR %s]%s kb/s[/COLOR]" % (color, value)
		elif attrib == 'quality':
			quality = QUALITY.r_map[value]
			return "[COLOR %s]%s[/COLOR]" % (color, quality)
		else:
			return "[COLOR %s]%s[/COLOR]" % (color, value)
		
	def ck(self, attrib):
		if getattr(self, attrib):
			self.attributes.append(self.colorize(attrib, getattr(self, attrib)))
		
	def format(self):
		self.attributes = []
		self.attributes.append(self.colorize('hostname', self.hostname))
		self.attributes.append(self.colorize('service', self.service))
		for foo in ['size', 'bitrate', 'extension', 'quality']:
			self.ck(foo)
		
		format = "[%s]: %s"	
		if self.text is None: self.text = self.hostname
		return format % (' | '.join(self.attributes), self.text)

class CommonScraper():
	USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36'
	ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HOST_COLOR = 'red'
	SIZE_COLOR = 'blue'
	EXTENSION_COLOR = 'green'
	QUALITY_COLOR = 'yellow'
	BITRATE_COLOR = 'purple'
	def __init__(self, load = None):
		self._load_list = load	
		self.enabled_scrapers = 0
		self.active_scrapers = []
		self._active_scrapers = []
		self._load_scrapers()
		self._enable_scrapers()
		self.search_results = []
	
	def normalize(self, string):
		return unicodedata.normalize('NFKD', unicode(string)).encode('utf-8','ignore')
	
	def get_setting(self, k):
		return self._settings[k]
	
	def set_setting(self, k, v):
		self._settings[k] = v
	
	def _load_scrapers(self):
		for filename in sorted(os.listdir(SCRAPER_DIR)):
			if not re.search('(__)|(common\.py)|(example\.py)|(all\.py)', filename) and re.search('py$', filename):
				name = filename[0:len(filename)-3]
				skip = False
				if self._load_list is not None:
					skip = True
					if name in self._load_list:
						skip = False
				if skip is False:	
					classname = name+'Scraper'
					scraper = __import__(name, globals(), locals(), [classname], -1)
					klass = getattr(scraper, classname)
					scraper = klass()
					self.put_scraper(scraper.service, scraper)
				
	def get_scraper_by_name(self, name):
		try:
			index = self.active_scrapers.index(name)
			return self.get_scraper_by_index(index)
		except:
			return None
		
	def get_scraper_by_index(self, index):
		try:
			return self._active_scrapers[index]
		except:
			return None
	
	def _enable_scrapers(self):
		for index in range(0, len(self.active_scrapers)):
			self.enabled_scrapers += 1
		
	def put_scraper(self, name, scraper):
		self.active_scrapers.append(name)
		self._active_scrapers.append(scraper)
		
	def process_results(self, results):
		#values = []
		#for r in results: values.append([self.hashid, r.format(), r.url])
		#DB=MyDatabaseAPI(DB_FILE)
		#DB.execute_many("INSERT INTO search_cache(hash, display, url) VALUES(?,?,?)", values)
		#DB.commit()
		self.search_results += results
		
	def search_tvshow(self, showname, season, episode, year=''):
		'''self.hashid = hashlib.md5(showname+str(season)+str(episode)).hexdigest()
		DB.execute("DELETE FROM search_cache WHERE hash=? AND strftime('%s','now') -  strftime('%s',ts) > (3600 * ?)", [self.hashid, DECAY])
		DB.commit()
		cached = DB.query_assoc("SELECT display as title, url, strftime('%s','now') -  strftime('%s',ts) < (3600 * ?) as 'fresh' FROM search_cache WHERE hash=? AND fresh=1", [DECAY, self.hashid])
		'''
		cached=False
		if cached:
			self.search_results = cached
		else:
			self._get_active_resolvers()
			args = {"showname": showname, "season": season, "episode": episode, "year": year, "domains": self.domains}
			workers = ThreadPool(5)
			for index in range(0, self.enabled_scrapers):
				workers.queueTask(self.get_scraper_by_index(index).search_tvshow, args, self.process_results)
			workers.joinAll()
		resolved_url = None
		raw_url =  self.select_stream()
		if raw_url:
			resolved_url = self.resolve_url(raw_url)
		return resolved_url	
	
	def search_movie(self, title, year):
		'''self.hashid = hashlib.md5(title+str(year)).hexdigest()
		DB=MyDatabaseAPI(DB_FILE)
		DB.execute("DELETE FROM search_cache WHERE hash=? AND strftime('%s','now') -  strftime('%s',ts) > (3600 * ?)", [self.hashid, DECAY])
		DB.commit()
		cached = DB.query_assoc("SELECT display as title, url, strftime('%s','now') -  strftime('%s',ts) < (3600 * ?) as 'fresh' FROM search_cache WHERE hash=? AND fresh=1", [DECAY, self.hashid])
		'''
		cached = False
		if cached:
			self.search_results = cached
		else:
			self._get_active_resolvers()
			args = {"title": title, "year": year, "domains": self.domains}
			workers = ThreadPool(5)
			for index in range(0, self.enabled_scrapers):
				workers.queueTask(self.get_scraper_by_index(index).search_movie, args, self.process_results)
			workers.joinAll()
		resolved_url = None
		raw_url =  self.select_stream()
		if raw_url:
			resolved_url = self.resolve_url(raw_url)
		return resolved_url	
	
	def _get_active_resolvers(self):		
		self.domains = []
		try:
			for resolver in urlresolver.UrlResolver.implementors():
				for self.domain in resolver.domains:
					if re.match('^(.+?)\.(.+?)$', domain): self.domains.append(domain)
		except:
			pass
		if len(self.domains) ==0:
			self.domains = ['promptfile.com', 'crunchyroll.com', 'xvidstage.com', 'yourupload.com', 'dailymotion.com', 'cloudy.ec', 'cloudy.eu', 'cloudy.sx', 'cloudy.ch', 'cloudy.com', 'thevideo.me', 'videobb.com', 'stagevu.com', 'mp4stream.com', 'youwatch.org', 'rapidvideo.com', 'play44.net', 'castamp.com', 'daclips.in', 'daclips.com', 'videozed.net', 'videomega.tv', 'movieshd.co', 'bayfiles.com', 'vidzi.tv', 'vidxden.com', 'vidxden.to', 'divxden.com', 'vidbux.com', 'vidbux.to', 'purevid.com', 'thefile.me', 'shared.sx', 'vimeo.com', 'vidplay.net', 'vidspot.net', 'movshare.net', 'speedvideo.net', 'uploadc.com', 'streamcloud.eu', 'sockshare.com', 'vk.com', 'videohut.to', 'letwatch.us', 'royalvids.eu', 'veoh.com', 'donevideo.com', 'mp4star.com', 'vidto.me', 'vivo.sx', 'videotanker.co', 'hugefiles.net', 'youtube.com', 'youtu.be', 'primeshare.tv', 'sharevid.org', 'sharerepo.com', 'video44.net', 'billionuploads.com', 'realvid.net', 'filenuke.com', 'bestreams.net', 'exashare.com', 'limevideo.net', 'videovalley.net', 'divxstage.eu', 'divxstage.net', 'divxstage.to', 'cloudtime.to', 'vidzur.com', 'gorillavid.in', 'gorillavid.com', 'trollvid.net', 'ecostream.tv', 'muchshare.net', 'streamin.to', 'video.tt', '180upload.com', 'auengine.com', 'novamov.com', 'vodlocker.com', 'watchfreeinhd.com', 'uploadcrazy.net', 'tubeplus.me', 'mp4upload.com', 'cyberlocker.ch', 'googlevideo.com', 'picasaweb.google.com', 'jumbofiles.com', 'vidstream.in', 'veehd.com', 'movdivx.com', 'mightyupload.com', 'vidup.org', 'tune.pk', 'facebook.com', 'mrfile.me', 'nowvideo.eu', 'nowvideo.ch', 'nowvideo.sx', 'flashx.tv', 'videoboxone.com', 'vidcrazy.net', 'movreel.com', 'hostingbulk.com', 'played.to', 'putlocker.com', 'filedrive.com', 'firedrive.com', 'mooshare.biz', 'zalaa.com', 'playwire.com', 'vidbull.com', 'sharesix.com', 'movpod.net', 'movpod.in', 'justmp4.com', 'cloudyvideos.com', 'mega-vids.com', 'nosvideo.com', 'movzap.com', 'zuzvideo.com', 'allmyvideos.net', 'videofun.me', 'videoweed.es', 'videoraj.ec', 'videoraj.eu', 'videoraj.sx', 'videoraj.ch', 'videoraj.com']
		
	def resolve_url(self, raw_url):
		test = re.search("^(.+?)(://)(.+?)$", raw_url)
		scraper = test.group(1)
		raw_url = test.group(3)
		if 'get_resolved_url' in dir(self.get_scraper_by_name(scraper)):
			resolved_url = self.get_scraper_by_name(scraper).get_resolved_url(raw_url)
			return resolved_url
		else:
			source = urlresolver.HostedMediaFile(url=raw_url)
			resolved_url = source.resolve() if source else None
			return resolved_url

	
	def select_stream(self):
		streams = []
		options = []
		try:
			self.search_results.sort(reverse=True, key=lambda k: (k.quality, k.hostname))
		except: pass
		for result in self.search_results:
			streams.append(result.format())
			options.append(result.url)
		dialog = xbmcgui.Dialog()
		select = dialog.select("Select a stream", streams)
		if select < 0:
			return False
		return options[select]
	
	def test_quality(self, string):
		if re.search('1080p', string): return QUALITY.HD1080
		if re.search('720p', string): return QUALITY.HD720
		if re.search('480p', string): return QUALITY.SD480
		if re.search('(320p)|(240p)', string): return QUALITY.LOW
		return QUALITY.UNKNOWN
	
	def set_color(self, text, color):
		return "[COLOR %s]%s[/COLOR]" % (color, text)
	
	def format_size(self, size):
		size = int(size) / (1024 * 1024)
		if size > 2000:
			size = size / 1024
			unit = 'GB'
		else :
			unit = 'MB'
		size = "%s %s" % (size, unit)
		return size
	
	def request(self, uri, params=None, query=None, headers=None, return_soup=False, return_json=False):
		COOKIE_JAR = vfs.join(COOKIE_PATH,self.service + '.lwp')
		net = Net()
		net.set_cookies(COOKIE_JAR)
		if headers:
			headers['Referer'] = self.referrer
			headers['Accept'] = self.ACCEPT
			headers['User-Agent'] = self.USER_AGENT
		else:
			headers = {
			'Referer': self.referrer,
			'Accept': self.ACCEPT,
			'User-Agent': self.USER_AGENT
			}
		if query:
			uri = uri % urllib.urlencode(query)	
		if params:
			html = net.http_POST(self.base_url + uri, params, headers=headers).content
		else:
			html = net.http_GET(self.base_url + uri, headers=headers).content
		net.save_cookies(COOKIE_JAR) 	
		if return_soup:
			return BeautifulSoup(html)
		elif return_json:
			return json.loads(html)
		else: 
			return html
				
	def get_redirect(self, uri):
		from dudehere.routines import httplib2
		h = httplib2.Http()
		h.follow_redirects = True
		(response, body) = h.request(self.base_url + uri)
		return response['content-location']
			