import urllib2, urllib
from urllib2 import URLError, HTTPError
from datetime import datetime
import re, time
import json

CLIENT_ID = "7fe0eea41783130c7c3c3c0a99153740e19964bcd84cc488ef0691881e2c5da9"
SECRET_ID = "d0858eff6524270fc1e5dfb6e32583b22aa1111cf5d097214b54f74cc207cce0"
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
BASE_URL = "https://api-v2launch.trakt.tv"
PIN_URL = "http://trakt.tv/pin/4428"
DAYS_TO_GET = 21
DECAY = 2
#from dudehere.routines.database import SQLiteDatabase
from dudehere.routines import *
from dudehere.routines.vfs import VFSClass
vfs = VFSClass()

class TraktAPI():
	def __init__(self, token="", quiet=False):
		self.quiet = quiet
		#self.token = token
		if ADDON.get_setting('trakt_oauth_token') == '':
			pin = plugin.dialog_input('Enter pin from %s' % PIN_URL)
			response = trakt._authorize(pin)
		else:
			self._authorize()
	
	def search(self, query, media='show'):
		uri = '/search'
		return self._call(uri, params={'query': query, 'type': media})
		
	def get_calendar_shows(self):
		from datetime import date, timedelta
		d = date.today() - timedelta(days=DAYS_TO_GET)
		today = d.strftime("%Y-%m-%d")
		uri = '/calendars/my/shows/%s/%s' % (today, DAYS_TO_GET)
		media='episode'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=True)
	
	def get_similar_tvshows(self, imdb_id):
		uri = '/shows/%s/related' % imdb_id
		media = 'show'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=False)
	
	def get_trending_tvshows(self):
		uri = '/shows/trending'
		media='show'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=False)
	
	def get_popular_tvshows(self):
		uri = '/shows/popular'
		media='show'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=False)
	
	def get_recommended_tvshows(self):
		uri = '/recommendations/shows'
		media='show'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=True)
	
	def get_show_seasons(self, imdb_id):
		uri = '/shows/%s/seasons' % imdb_id
		return self._call(uri, params={'extended': 'images'})
	
	def get_show_episodes(self, imdb_id, season):
		uri = '/shows/%s/seasons/%s' % (imdb_id, season)
		media='episode'
		return self._call(uri, params={'extended': 'full,images'}, cache=media)
	
	def get_watchlist_tvshows(self):
		uri = '/users/me/watchlist/shows'
		media = 'tvshow'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=True)
	
	def get_watchlist_movies(self):
		uri = '/users/me/watchlist/movies'
		return self._call(uri, params={'extended': 'full,images'}, auth=True)
	
	def get_trending_movies(self):
		uri = '/movies/trending'
		media='movie'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=False)
	
	def get_popular_movies(self):
		uri = '/movies/popular'
		media = 'movie'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=True)
	
	def get_recommended_movies(self):
		uri = '/recommendations/movies'
		media = 'movie'
		return self._call(uri, params={'extended': 'full,images'}, cache=media, auth=True)
	
	def get_show_info(self, imdb_id, episodes=False):
		if episodes:
			uri = '/shows/%s/seasons' % imdb_id
			return self._call(uri, params={'extended': 'episodes,full'})
		else:
			uri = '/shows/%s' % imdb_id
			return self._call(uri)
	
	def _authorize(self, pin=None):
		uri = '/oauth/token'
		data = {'client_id': CLIENT_ID, 'client_secret': SECRET_ID, 'redirect_uri': REDIRECT_URI}
		if pin:
			data['code'] = pin
			data['grant_type'] = 'authorization_code'
		else:
			refresh_token = ADDON.get_setting('trakt_refresh_token')
			if refresh_token:
				data['refresh_token'] = refresh_token
				data['grant_type'] = 'refresh_token'
			else:
				ADDON.set_setting('trakt_oauth_token', '')
				ADDON.set_setting('trakt_refresh_token', '')
				ADDON.log("Authentication Error, Please you must authorize Alluc with Tratk.")
				return False
		response = self._call(uri, data, auth=False)
		if response is False:
			ADDON.set_setting('trakt_oauth_token', '')
			ADDON.set_setting('trakt_refresh_token', '')
			return False
		if 'access_token' in response.keys() and 'refresh_token' in response.keys():
			ADDON.set_setting('trakt_oauth_token', response['access_token'])
			ADDON.set_setting('trakt_refresh_token', response['refresh_token'])
			self.token = response['access_token']
			return True
	
	def process_record(self, record, media=None):
		'''print record
		if 'episode' in record.keys():
			meta = self.process_episode(record)
			return meta
		if 'movie' in record.keys():
			meta = self.process_movie(record)
			return meta'''
		if media=='movie':
			meta = self.process_movie(record)
			return meta
		elif media=='episode':
			meta = self.process_episode(record)
			return meta
		elif media=='tvshow':
			meta = self.process_show(record)
			return meta
	
	def process_show(self, record):
		try:
			show = record['show']
		except:
			show = record
		meta = {}
		meta['imdb_id'] = show['ids']['imdb']
		meta['tvdb_id'] = show['ids']['tvdb']
		meta['title'] = show['title']
		meta['TVShowTitle'] = show['title']
		meta['rating'] = show['rating']
		meta['duration'] = show['runtime']
		meta['plot'] = show['overview']
		meta['mpaa'] = show['certification']
		meta['premiered'] = show['first_aired']
		meta['year'] = show['year']
		meta['trailer_url'] = show['trailer']
		meta['genre'] = show['genres']
		meta['studio'] = show['network']
		meta['status'] = show['status']       
		meta['cast'] = []
		meta['banner_url'] = show['images']['thumb']['full']	
		meta['cover_url'] = show['images']['poster']['full']
		meta['backdrop_url'] = show['images']['fanart']['full']
		meta['overlay'] = 6
		meta['episode'] = 0
		meta['playcount'] = 0
		return meta
		
	def process_movie(self, record):
		try:
			movie = record['movie']
		except:
			movie = record
		meta = {}
		meta['imdb_id'] = movie['ids']['imdb']
		meta['tmdb_id'] = movie['ids']['tmdb']
		meta['title'] = movie['title']
		meta['year'] = int(movie['year'])
		meta['writer'] = ''
		meta['director'] = ''
		meta['tagline'] = movie['tagline']
		meta['cast'] = []
		meta['rating'] = movie['rating']
		meta['votes'] = movie['votes']
		meta['duration'] = movie['runtime']
		meta['plot'] = movie['overview']
		meta['mpaa'] = movie['certification']
		meta['premiered'] = movie['released']
		meta['trailer_url'] = movie['trailer']
		meta['genre'] = movie['genres']
		meta['studio'] = ''
		meta['thumb_url'] = movie['images']['thumb']['full']
		meta['cover_url'] = movie['images']['poster']['full']
		meta['backdrop_url'] = movie['images']['fanart']['full']
		meta['overlay'] = 6
		return meta
	
	def process_episode(self, record):
		try:
			show = record['show']
			episode = record['episode']
			meta = {}
			meta['imdb_id']= show['ids']['imdb']
			meta['tvdb_id']=show['ids']['tvdb']
			meta['year'] = int(show['year'])
			meta['episode_id'] = ''                
			meta['season']= int(episode['season'])
			meta['episode']= int(episode['number'])
			meta['title']= episode['title']
			meta['showtitle'] = show['title']
			meta['director'] = ''
			meta['writer'] = ''
			meta['plot'] = episode['overview']
			meta['rating'] = episode['rating']
			meta['premiered'] = episode['first_aired']
			meta['poster'] = show['images']['poster']['full']
			meta['cover_url']= episode['images']['screenshot']['full']
			meta['trailer_url']=''
			meta['backdrop_url'] = show['images']['fanart']['full']
			meta['overlay'] = 6
			return meta
		except:
			episode = record
			tmp = re.match('^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.000Z', record['first_aired'])
			aired = datetime(int(tmp.group(1)), int(tmp.group(2)),int(tmp.group(3)),int(tmp.group(4)),int(tmp.group(5)),int(tmp.group(6)))
			aired = time.mktime(aired.timetuple())
			now = time.mktime(datetime.now().timetuple())
			if aired < now:
				meta = {}
				meta['imdb_id']= episode['ids']['imdb']
				meta['tvdb_id']=episode['ids']['tvdb']
				meta['year'] = 0
				meta['episode_id'] = ''                
				meta['season']= int(episode['season'])
				meta['episode']= int(episode['number'])
				meta['title']= episode['title']
				meta['showtitle'] = ''
				meta['director'] = ''
				meta['writer'] = ''
				meta['plot'] = episode['overview']
				meta['rating'] = episode['rating']
				meta['premiered'] = episode['first_aired']
				meta['poster'] = ''
				meta['cover_url']= episode['images']['screenshot']['full']
				meta['trailer_url']=''
				meta['backdrop_url'] = ''
				meta['overlay'] = 6
				return meta
			return False
	
	def _call(self, uri, data=None, params=None, auth=False, cache=False):
		'''if cache:
			cached = self.DB.query("SELECT cache_id, cache_type,strftime('%s','now') -  strftime('%s',ts) < (3600 * ?) as 'fresh' FROM trakt_cache WHERE uri=? AND fresh=1", [DECAY, uri])
			if len(cached) > 0:
				ADDON.log("Loading cached trakt results", LOGVERBOSE)
				self._cached = cache
				return cached
			else:
				self.DB.execute("INSERT INTO trakt_cache(cache_type, uri) VALUES(?,?)", [cache, uri])
				self.DB.commit()
				self.cache_id = self.DB.lastrowid
				self._cached = False
		'''		

		json_data = json.dumps(data) if data else None
		headers = {'Content-Type': 'application/json', 'trakt-api-key': CLIENT_ID, 'trakt-api-version': 2}
		if auth: headers.update({'Authorization': 'Bearer %s' % (self.token)})
		url = '%s%s' % (BASE_URL, uri)
		if params:
			params['limit'] = 100
		else:
			params = {'limit': 100}
		url = url + '?' + urllib.urlencode(params)
		ADDON.log(url)
		try:
			request = urllib2.Request(url, data=json_data, headers=headers)
			f = urllib2.urlopen(request)
			result = f.read()
			response = json.loads(result)
		except HTTPError as e:
			ADDON.log(url)
			ADDON.log(headers)
			print e
			#error_msg = 'Trakt HTTP Error %s: %s' % ( e.code, e.reason)
			
		except URLError as e:
			ADDON.log(url)
			error_msg = 'Trakt URL Error %s: %s' % ( e.code, e.reason)

		else:
			return response
		