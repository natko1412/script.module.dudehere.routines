import sys
import os
import re
import urllib
import random
from BeautifulSoup import BeautifulSoup
from dudehere.routines import *
from dudehere.routines.scrapers import CommonScraper, ScraperResult


class icefilmsScraper(CommonScraper):
	def __init__(self):
		self._settings = {}
		self.service='icefilms'
		self.name = 'icefilms.info'
		self.referrer = 'http://www.icefilms.info'
		self.base_url = 'http://www.icefilms.info'
	
	
	def search_tvshow(self, args):
		results = []
		uri = "/tv/a-z/%s" % re.sub('^(A )|(An )|(The )', '', args['showname'], re.IGNORECASE)[0:1]
		html = self.request(uri)
		pattern = "<a href=/tv/series/(\d+?)/(\d+?)>%s \(%s\)</a>" % (args['showname'], args['year'])
		show = re.search(pattern, html)
		if show:
			pattern = '%sx%s' % (args['season'], str(args['episode']).zfill(2))
			uri = "/tv/series/%s/%s" % (show.group(1), show.group(2))
			soup = self.request(uri, return_soup=True)
			for star in soup.findAll("img", {"class": "star"}):
				a = star.nextSibling
				if re.search(pattern, a.string):
					uri = a['href']
					vid = re.search('=(\d+?)&', uri).group(1)
					return self._get_sources(vid)
					break
		return results
	
	def search_movie(self, args):
		self.domains = args['domains']
		results = []
		uri = "/movies/a-z/%s" % re.sub('^(A )|(An )|(The )', '', args['title'], re.IGNORECASE)[0:1]
		html = self.request(uri)
		pattern = "<a href=/ip.php\?v=(\d+?)&>%s \(%s\)</a>" % (args['title'], args['year'])
		movie = re.search(pattern, html)
		if movie:
			return self._get_sources(movie.group(1))
		return results
	
	def get_resolved_url(self, raw_url):
		import urlparse
		import urllib2
		url, query = raw_url.split('?', 1)
		data = urlparse.parse_qs(query, True)
		url = urlparse.urljoin(self.base_url, url)
		url += '?s=%s&t=%s' % (data['id'][0], data['t'][0])
		referer = 'http://www.icefilms.info/membersonly/components/com_iceplayer/video.php?h=374&w=631&vid=%s&img=' % (data['t'][0])
		data = urllib.urlencode(data, True)
		request = urllib2.Request(url, data=data)
		request.add_header('User-Agent', "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko")
		request.add_unredirected_header('Host', request.get_host())
		request.add_unredirected_header('Referer', referer)
		response = urllib2.urlopen(request)
		html = response.read()
		match = re.search('url=(.*)', html)
		if match:
			import urlresolver
			raw_url = urllib.unquote_plus(match.group(1))
			source = urlresolver.HostedMediaFile(url=raw_url)
			resolved_url = source.resolve() if source else None
			return resolved_url
		return ''
	
	def _get_sources(self, vid):
		uri = '/membersonly/components/com_iceplayer/video.php?h=374&w=631&vid=%s&img=' % vid
		results = []
		html = self.request(uri)
		soup = BeautifulSoup(html)
		
		match = re.search('lastChild\.value="([^"]+)"(?:\s*\+\s*"([^"]+))?', html)
		secret = ''.join(match.groups(''))

		match = re.search('"&t=([^"]+)', html)
		t = match.group(1)

		match = re.search('(?:\s+|,)s\s*=(\d+)', html)
		s_start = int(match.group(1))

		match = re.search('(?:\s+|,)m\s*=(\d+)', html)
		m_start = int(match.group(1))

		match = re.search('<iframe[^>]*src="([^"]+)', html)
		ad_url = urllib.quote(match.group(1))
		
			
		for block in soup.findAll('div', {"class": "ripdiv"}):
			isHD = block.find('b').string == 'HD 720p'
			if isHD: quality = QUALITY.HD720
			else: quality = QUALITY.SD480
			
			mirrors = block.findAll("p")
			for mirror in mirrors:
				links = mirror.findAll("a")
				for link in links:
					mirror_id = link['onclick'][3:len(link['onclick'])-1]
					host_name, title = self.get_provider(link)
					if host_name:
						'''attribs = [
							self.name, 
							self.set_color(QUALITY.r_map[quality], self.QUALITY_COLOR), 
							self.set_color(host_name, self.HOST_COLOR)
						]'''
						s = s_start + random.randint(1, 100)
						m = m_start + (s - s_start) + random.randint(1, 100)
						url = '%s:///membersonly/components/com_iceplayer/video.phpAjaxResp.php?id=%s&s=%s&iqs=&url=&m=%s&cap= &sec=%s&t=%s' % (self.service, mirror_id, s, m, secret, t)
						#display = "[%s]: %s" % (' | '.join(attribs), title)
						#record = {"title": display, "url": url, "host": host_name, "service": self.service, "quality": quality}
						result = ScraperResult(self.service, host_name, url, title)
						result.quality = quality
						results.append(result)
		return results
		
	def get_provider(self, link):
		title = link.next[0:len(link.next)-2]
		s = re.search('Source #(\d+): (.+?)</a>', str(link))
		skey = self.strip_tags(s.group(2)).lower()
		table = {
				'180upload': 		'180upload.com',
				'hugefiles':		'hugefiles.net',
				'clicknupload':		'clicknupload.com',
				'tusfiles':			'tusfiles.net',
				'xfileload':		'xfileload.com',
				'mightyupload':		'mightyupload.com',
				'movreel':			'movreel.com',
				'donevideo':		'donevideo.com',
				'vidplay':			'vidplay.net',
				'24uploading':		'24uploading.com',
				'xvidstage':		'xvidstage.com',
				'2shared':			'2shared.com'
		}
		if skey in table.keys():
			return table[skey], title
		else: 
			print skey		
		return None, None

	def strip_tags(self, html):
		import htmlentitydefs
		from HTMLParser import HTMLParser
		class HTMLTextExtractor(HTMLParser):
			def __init__(self):
				HTMLParser.__init__(self)
				self.result = [ ]
		
			def handle_data(self, d):
				self.result.append(d)
		
			def handle_charref(self, number):
				codepoint = int(number[1:], 16) if number[0] in (u'x', u'X') else int(number)
				self.result.append(unichr(codepoint))
		
			def handle_entityref(self, name):
				codepoint = htmlentitydefs.name2codepoint[name]
				self.result.append(unichr(codepoint))
				
			def get_text(self):
				return u''.join(self.result)	
				
		s = HTMLTextExtractor()
		s.feed(html)
		return s.get_text()
		