import os,sys
import urllib2
import xbmcaddon
from urllib2 import URLError, HTTPError
try: 
	import simplejson as json
except ImportError: 
	import json
class TransmogrifierAPI:

	def __init__(self, host='localhost', port=8750):
		self.host = host
		self.pin = xbmcaddon.Addon(id='service.transmogrifier').getSetting('auth_pin')
		self.token = xbmcaddon.Addon(id='service.transmogrifier').getSetting('auth_token')
		self.save_directory = xbmcaddon.Addon(id='service.transmogrifier').getSetting('save_directory')
		self.port = port
		self._authorize()
		
	def get_progress(self):
		return self._call('progress')
	
	def _authorize(self):
		if self.token == '':
			response = self._call("authorize")
			self.token = response['token']
			xbmcaddon.Addon(id='service.transmogrifier').setSetting('auth_token', self.token)
		else:
			response = self._call("validate_token")
			if 'success' not in response.keys():
				xbmcaddon.Addon(id='service.transmogrifier').setSetting('auth_token', '')
				
		
	def enqueue(self, videos):
		if type(videos) is dict: videos = [videos]
		data = {"videos": videos}
		return self._call('enqueue', data)
	
	def abort(self):
		return self._call('abort')
	
	def restart(self, ids):
		if type(ids) is int: ids = [ids]
		data = {"videos": []}
		for id in ids:
			data['videos'].append({"id": id})
		return self._call('restart', data)
	
	def delete(self, ids):
		if type(ids) is int: ids = [ids]
		data = {"videos": []}
		for id in ids:
			data['videos'].append({"id": id})
		return self._call('delete', data)
		
	def get_videos(self, media):
		from dudehere.routines.vfs import VFSClass
		vfs = VFSClass()
		if media == 'tv':
			path = vfs.join(self.save_directory, "TV Shows")
		else:
			path = vfs.join(self.save_directory, "Movies")
		videos = vfs.ls(path, pattern="avi$")[1]
		return path, videos
	
	def get_queue(self):
		return self._call('queue')
	
	def _build_url(self):
		url = "http://%s:%s/api.json" % (self.host, self.port)
		return url
	
	def _build_request(self, method):
		if method=='authorize':
			request = {"method": method, "pin": self.pin}
		else:
			request = {"method": method, "token": self.token}
		return request
	
	def _call(self, method, data=None):
		
		url = self._build_url()
		request = self._build_request(method)
		if data:
			for key in data.keys():
				request[key] = data[key]
		json_data = json.dumps(request)
		headers = {'Content-Type': 'application/json'}
		try:
			request = urllib2.Request(url, data=json_data, headers=headers)
			f = urllib2.urlopen(request)
			response = f.read()
			return json.loads(response)
		except HTTPError as e:
			print 'TransmogrifierAPI Error: %s' % e
