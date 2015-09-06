import sys
import os
import re
import urllib
from dudehere.routines import *
from dudehere.routines.scrapers import CommonScraper, ScraperResult
class alluc_apiScraper(CommonScraper):
	def __init__(self):
		self._settings = {}
		self.service='alluc_api'
		self.name = 'alluc.com'
		self.referrer = 'https://www.alluc.com'
		self.base_url = 'https://www.alluc.com/api/search'
		self.username = ADDON.get_setting(self.service + '_username')
		self.password = ADDON.get_setting(self.service + '_password')
		self.apikey = ADDON.get_setting(self.service + '_apikey')
		self.max_results = 10
	
	
	def search_tvshow(self, args):
		self.domains = args['domains']
		results = []
		uri = self.prepair_query('tvshow', args['showname'], args['season'], args['episode'], apikey=True)
		data = self.request(uri, return_json=True)
		results = self.process_results(data)
		return results
	
	def search_movie(self, args):
		self.domains = args['domains']
		results = []
		uri = self.prepair_query('movie', args['title'], args['year'], apikey=True)
		print uri
		data = self.request(uri, return_json=True)
		results = self.process_results(data)
		return results
	
	def process_results(self, data):
		results = []
		for result in data['result']:
			title = self.normalize(result['title'])
			sourcetitle = self.normalize(result['sourcetitle'])
			hoster = result['hosterurls']
			extension = result['extension']
			size = result['sizeinternal']
			extension = result['extension']
			host_name = result['hostername']
			hosts = result['hosterurls']
			for host in hosts:				
				if host_name in self.domains:
					url = "%s://%s" % (self.service, host['url'])
					quality = self.test_quality(title+sourcetitle+self.normalize(url))
					result = ScraperResult(self.service, host_name, url, title)
					result.quality = quality
					result.size = size
					result.extension = extension
					results.append(result)
		return results
		
	def prepair_query(self, media, *args, **kwards):
		uri = "/stream/?%s"
		params = {"from": 0, "count": self.max_results, "getmeta":0}
		#if 'apikey' in kwards.keys():
		#params['apikey'] = self.apikey
		#else:
		params['user'] = self.username
		params['password'] = self.password
		if media == 'tvshow':
			params['query'] = "%s S%sE%s" % args
		else:
			params['query'] = "%s %s" % args
		if 'host' in kwards.keys():
			params['query'] = params['query'] + + ' host:' + kwards['host']
		if 'lang' in kwards.keys():
			params['query'] = params['query'] + + ' lang:' + kwards['lang']	

		return uri % urllib.urlencode(params)