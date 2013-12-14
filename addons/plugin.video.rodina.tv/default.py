#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2013, otaranda@hotmail.com
# Rev. 1.3.1


_VERSION_ = '1.0.0'
_ADDOD_ID_= 'plugin.video.rodina.tv'

import os, re, sys, time
import urllib, urllib2
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
#import uuid
import hashlib

#import io
#import inspect
import HTMLParser
import json



#import cookielib
#cookiejar = cookielib.LWPCookieJar()
#cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
#opener = urllib2.build_opener(cookie_handler)

def QT(url): return urllib.quote_plus(url)

class Helpers():
	def __init__(self):
		self.version = u"2.0.1"
		self.plugin = u"Helpers-" + self.version
		self.USERAGENT = u"Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"
		self.dbg = False
		self.dbglevel = 3

		# This function raises a keyboard for user input
	def getUserInput(self, title=u"Input", default=u"", hidden=False):
		self.log("", 5)
		result = None

		# Fix for when this functions is called with default=None
		if not default:
			default = u""

		keyboard = xbmc.Keyboard(default, title)
		keyboard.setHiddenInput(hidden)
		keyboard.doModal()

		if keyboard.isConfirmed():
			result = keyboard.getText()

		self.log(repr(result), 5)
		return result


	# This function raises a keyboard numpad for user input
	def getUserInputNumbers(self, title=u"Input", default=u""):
		self.log("", 5)
		result = None

		# Fix for when this functions is called with default=None
		if not default:
			default = u""

		keyboard = xbmcgui.Dialog()
		result = keyboard.numeric(0, title, default)

		self.log(repr(result), 5)
		return str(result)


	# Converts the request url passed on by xbmc to the plugin into a dict of key-value pairs
	def getParameters(self, parameterString):
		self.log("", 5)
		commands = {}
		#parameterString = urllib.unquote_plus(parameterString)
		splitCommands = parameterString[parameterString.find('?') + 1:].split('&')

		for command in splitCommands:
			if (len(command) > 0):
				splitCommand = command.split('=')
				key = splitCommand[0]
				value = splitCommand[1]
				commands[key] = value

		self.log(repr(commands), 5)
		return commands


	def replaceHTMLCodes(self, txt):
		self.log(repr(txt), 5)

		# Fix missing ; in &#<number>;
		txt = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", self.makeUTF8(txt))

		txt = HTMLParser.HTMLParser().unescape(txt)
		txt = txt.replace("&amp;", "&")
		self.log(repr(txt), 5)
		return txt


	def stripTags(self, html):
		self.log(repr(html), 5)
		sub_start = html.find("<")
		sub_end = html.find(">")
		while sub_start < sub_end and sub_start > -1:
			html = html.replace(html[sub_start:sub_end + 1], "").strip()
			sub_start = html.find("<")
			sub_end = html.find(">")

		self.log(repr(html), 5)
		return html


	def _getDOMContent(self, html, name, match, ret):  # Cleanup
		self.log("match: " + match, 3)

		endstr = "</" + name  # + ">"

		start = html.find(match)
		end = html.find(endstr, start)
		pos = html.find("<" + name, start + 1 )

		self.log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

		while pos < end and pos != -1:  # Ignore too early </endstr> return
			tend = html.find(endstr, end + len(endstr))
			if tend != -1:
				end = tend
			pos = html.find("<" + name, pos + 1)
			self.log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

		self.log("start: %s, len: %s, end: %s" % (start, len(match), end), 3)
		if start == -1 and end == -1:
			result = u""
		elif start > -1 and end > -1:
			result = html[start + len(match):end]
		elif end > -1:
			result = html[:end]
		elif start > -1:
			result = html[start + len(match):]

		if ret:
			endstr = html[end:html.find(">", html.find(endstr)) + 1]
			result = match + result + endstr

		self.log("done result length: " + str(len(result)), 3)
		return result

	def _getDOMAttributes(self, match, name, ret):
		self.log("", 3)
		lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
		ret = []
		for tmp in lst:
			cont_char = tmp[0]
			if cont_char in "'\"":
				self.log("Using %s as quotation mark" % cont_char, 3)

				# Limit down to next variable.
				if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
					tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

				# Limit to the last quotation mark
				if tmp.rfind(cont_char, 1) > -1:
					tmp = tmp[1:tmp.rfind(cont_char)]
			else:
				self.log("No quotation mark found", 3)
				if tmp.find(" ") > 0:
					tmp = tmp[:tmp.find(" ")]
				elif tmp.find("/") > 0:
					tmp = tmp[:tmp.find("/")]
				elif tmp.find(">") > 0:
					tmp = tmp[:tmp.find(">")]

			ret.append(tmp.strip())

		self.log("Done: " + repr(ret), 3)
		return ret

	def _getDOMElements(self, item, name, attrs):
		self.log("", 3)
		lst = []
		for key in attrs:
			lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
			if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
				lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

			if len(lst) == 0:
				self.log("Setting main list " + repr(lst2), 5)
				lst = lst2
				lst2 = []
			else:
				self.log("Setting new list " + repr(lst2), 5)
				test = range(len(lst))
				test.reverse()
				for i in test:  # Delete anything missing from the next list.
					if not lst[i] in lst2:
						self.log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 3)
						del(lst[i])

		if len(lst) == 0 and attrs == {}:
			self.log("No list found, trying to match on name only", 3)
			lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
			if len(lst) == 0:
				lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

		self.log("Done: " + str(type(lst)), 3)
		return lst

	def parseDOM(self, html, name=u"", attrs={}, ret=False):
		self.log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)
		#self.log("BLA: " + repr(type(html)) + " - " + repr(type(name)))

		if isinstance(name, str): # Should be handled
			try:
				name = name #.decode("utf-8")
			except:
				self.log("Couldn't decode name binary string: " + repr(name))

		if isinstance(html, str):
			try:
				html = [html.decode("utf-8")] # Replace with chardet thingy
			except:
				self.log("Couldn't decode html binary string. Data length: " + repr(len(html)))
				html = [html]
		elif isinstance(html, unicode):
			html = [html]
		elif not isinstance(html, list):
			self.log("Input isn't list or string/unicode.")
			return u""

		if not name.strip():
			self.log("Missing tag name")
			return u""

		ret_lst = []
		for item in html:
			temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
			for match in temp_item:
				item = item.replace(match, match.replace("\n", " "))

			lst = self._getDOMElements(item, name, attrs)

			if isinstance(ret, str):
				self.log("Getting attribute %s content for %s matches " % (ret, len(lst) ), 3)
				lst2 = []
				for match in lst:
					lst2 += self._getDOMAttributes(match, name, ret)
				lst = lst2
			else:
				self.log("Getting element content for %s matches " % len(lst), 3)
				lst2 = []
				for match in lst:
					self.log("Getting element content for %s" % match, 4)
					temp = self._getDOMContent(item, name, match, ret).strip()
					item = item[item.find(temp, item.find(match)) + len(temp):]
					lst2.append(temp)
				lst = lst2
			ret_lst += lst

		self.log("Done: " + repr(ret_lst), 3)
		return ret_lst


	def extractJS(self, data, function=False, variable=False, match=False, evaluate=False, values=False):
		self.log("")
		scripts = self.parseDOM(data, "script")
		if len(scripts) == 0:
			self.log("Couldn't find any script tags. Assuming javascript file was given.")
			scripts = [data]

		lst = []
		self.log("Extracting", 4)
		for script in scripts:
			tmp_lst = []
			if function:
				tmp_lst = re.compile(function + '\(.*?\).*?;', re.M | re.S).findall(script)
			elif variable:
				tmp_lst = re.compile(variable + '[ ]+=.*?;', re.M | re.S).findall(script)
			else:
				tmp_lst = [script]
			if len(tmp_lst) > 0:
				self.log("Found: " + repr(tmp_lst), 4)
				lst += tmp_lst
			else:
				self.log("Found nothing on: " + script, 4)

		test = range(0, len(lst))
		test.reverse()
		for i in test:
			if match and lst[i].find(match) == -1:
				self.log("Removing item: " + repr(lst[i]), 10)
				del lst[i]
			else:
				self.log("Cleaning item: " + repr(lst[i]), 4)
				if lst[i][0] == u"\n":
					lst[i] == lst[i][1:]
				if lst[i][len(lst) -1] == u"\n":
					lst[i] == lst[i][:len(lst)- 2]
				lst[i] = lst[i].strip()

		if values or evaluate:
			for i in range(0, len(lst)):
				self.log("Getting values %s" % lst[i])
				if function:
					if evaluate: # include the ( ) for evaluation
						data = re.compile("(\(.*?\))", re.M | re.S).findall(lst[i])
					else:
						data = re.compile("\((.*?)\)", re.M | re.S).findall(lst[i])
				elif variable:
					tlst = re.compile(variable +".*?=.*?;", re.M | re.S).findall(lst[i])
					data = []
					for tmp in tlst: # This breaks for some stuff. "ad_tag": "http://ad-emea.doubleclick.net/N4061/pfadx/com.ytpwatch.entertainment/main_563326'' # ends early, must end with }
						cont_char = tmp[0]
						cont_char = tmp[tmp.find("=") + 1:].strip()
						cont_char = cont_char[0]
						if cont_char in "'\"":
							self.log("Using %s as quotation mark" % cont_char, 1)
							tmp = tmp[tmp.find(cont_char) + 1:tmp.rfind(cont_char)]
						else:
							self.log("No quotation mark found", 1)
							tmp = tmp[tmp.find("=") + 1: tmp.rfind(";")]

						tmp = tmp.strip()
						if len(tmp) > 0:
							data.append(tmp)
				else:
					self.log("ERROR: Don't know what to extract values from")

				self.log("Values extracted: %s" % repr(data))
				if len(data) > 0:
					lst[i] = data[0]

		if evaluate:
			for i in range(0, len(lst)):
				self.log("Evaluating %s" % lst[i])
				data = lst[i].strip()
				try:
					try:
						lst[i] = json.loads(data)
					except:
						self.log("Couldn't json.loads, trying eval")
						lst[i] = eval(data)
				except:
					self.log("Couldn't eval: %s from %s" % (repr(data), repr(lst[i])))

		self.log("Done: " + str(len(lst)))
		return lst

	def fetchPage(self, params={}):
		get = params.get
		link = get("link")
		ret_obj = {}
		if get("post_data"):
			self.log("called for : " + repr(params['link']))
		else:
			self.log("called for : " + repr(params))

		if not link or int(get("error", "0")) > 2:
			self.log("giving up")
			ret_obj["status"] = 500
			return ret_obj

		if get("post_data"):
			if get("hide_post_data"):
				self.log("Posting data", 2)
			else:
				self.log("Posting data: " + urllib.urlencode(get("post_data")), 2)

			request = urllib2.Request(link, urllib.urlencode(get("post_data")))
			request.add_header('Content-Type', 'application/x-www-form-urlencoded')
		else:
			self.log("Got request", 2)
			request = urllib2.Request(link)

		if get("headers"):
			for head in get("headers"):
				request.add_header(head[0], head[1])

		request.add_header('User-Agent', self.USERAGENT)

		if get("cookie"):
			request.add_header('Cookie', get("cookie"))

		if get("refering"):
			request.add_header('Referer', get("refering"))

		try:
			self.log("connecting to server...", 1)

			con = urllib2.urlopen(request)
			ret_obj["header"] = con.info()
			ret_obj["new_url"] = con.geturl()
			if get("no-content", "false") == u"false" or get("no-content", "false") == "false":
				inputdata = con.read()
				#data_type = chardet.detect(inputdata)
				#inputdata = inputdata.decode(data_type["encoding"])
				ret_obj["content"] = inputdata #.decode("utf-8")

			con.close()

			self.log("Done")
			ret_obj["status"] = 200
			return ret_obj

		except urllib2.HTTPError, e:
			err = str(e)
			self.log("HTTPError : " + err)
			self.log("HTTPError - Headers: " + str(e.headers) + " - Content: " + e.fp.read())

			params["error"] = str(int(get("error", "0")) + 1)
			ret = self.fetchPage(params)

			if not "content" in ret and e.fp:
				ret["content"] = e.fp.read()
				return ret

			ret_obj["status"] = 500
			return ret_obj

		except urllib2.URLError, e:
			err = str(e)
			self.log("URLError : " + err)

			time.sleep(3)
			params["error"] = str(int(get("error", "0")) + 1)
			ret_obj = self.fetchPage(params)
			return ret_obj


#	def getCookieInfoAsHTML(self, ):
#		self.log("", 5)

#		cookie = repr(cookiejar)
#		cookie = cookie.replace("<_LWPCookieJar.LWPCookieJar[", "")
#		cookie = cookie.replace("), Cookie(version=0,", "></cookie><cookie ")
#		cookie = cookie.replace(")]>", "></cookie>")
#		cookie = cookie.replace("Cookie(version=0,", "<cookie ")
#		cookie = cookie.replace(", ", " ")
#		self.log(repr(cookie), 5)
#		return cookie


	# This function implements a horrible hack related to python 2.4's terrible unicode handling.
#	def makeAscii(self, data):
#		self.log(repr(data), 5)
		#if sys.hexversion >= 0x02050000:
		#        return data

#		try:
#			return data.encode('ascii', "ignore")
#		except:
#			self.log("Hit except on : " + repr(data))
#			s = u""
#			for i in data:
#				try:
#					i.encode("ascii", "ignore")
#				except:
#					self.log("Can't convert character", 4)
#					continue
#				else:
#					s += i

#			self.log(repr(s), 5)
#			return s


	# This function handles stupid utf handling in python.
	def makeUTF8(self, data):
		self.log(repr(data), 5)
		return data
		try:
			return data.decode('utf8', 'xmlcharrefreplace') # was 'ignore'
		except:
			self.log("Hit except on : " + repr(data))
			s = u""
			for i in data:
				try:
					i.decode("utf8", "xmlcharrefreplace")
				except:
					self.log("Can't convert character", 4)
					continue
				else:
					s += i
			self.log(repr(s), 5)
			return s


#	def openFile(self, filepath, options=u"r"):
#		self.log(repr(filepath) + " - " + repr(options))
#		if options.find("b") == -1:  # Toggle binary mode on failure
#			alternate = options + u"b"
#		else:
#			alternate = options.replace(u"b", u"")

#		try:
#			self.log("Trying normal: %s" % options)
#			return io.open(filepath, options)
#		except:
#			self.log("Fallback to binary: %s" % alternate)
#			return io.open(filepath, alternate)


	def log(self, description, level=0):
		if self.dbg and self.dbglevel > level:
			try:
				xbmc.log((u"[%s] : '%s'" % (self.plugin, description)).decode("utf-8"), xbmc.LOGNOTICE)
			except:
				xbmc.log(u"FALLBACK [%s] : '%s'" % (self.plugin, repr(description)), xbmc.LOGNOTICE)


common = Helpers()
common.plugin = "Rodina TV"
    
#def dt(u): return datetime.datetime.utcfromtimestamp(u)
class ccache():
    def __init__(self):
        self.type = ''
        self.query = ''
        self.fname = ''
        self.ttl = 0
        self.ctime = 0.0
    

class RodinaTV():
    def __init__(self):
        self.id = _ADDOD_ID_
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'http://rodina.tv'
        self.api = 'http://api.rodina.tv'
        self.auth = self.api + '/auth.xml'
        self.get_auth = False

        self.token = ''
        self.portal = ''
        self.ttl = ''
        
        self.cat = ''
        self.has_pwd = ''
        self.has_rec = ''
        self.pid = ''
        
        self.count = ''
        self.offset = ''
        self.word = ''
                        
        self.timeserver = ''
       
        self.path = xbmc.translatePath(self.addon.getAddonInfo('path')).decode('utf-8')
        self.path_resources = xbmc.translatePath(self.path + '/resources')
        self.path_icons = xbmc.translatePath(self.path_resources + '/icons')
        self.path_icons_tv = xbmc.translatePath(self.path_icons + '/icon_tv_small.png')
        self.path_icons_td = xbmc.translatePath(self.path_icons + '/icon_timedelay_small.png')
        self.path_icons_ts = xbmc.translatePath(self.path_icons + '/icon_timeshift_small.png')
        self.path_icons_kino = xbmc.translatePath(self.path_icons + '/icon_kinozal_small.png')
        self.path_icons_info = xbmc.translatePath(self.path_icons + '/icon_info_small.png')
                
        self.cache_chan = xbmc.translatePath('special://temp/' + 'rodinatvc.tmp')
        self.cache_epg = xbmc.translatePath('special://temp/' + 'rodinatve.tmp')

        self.uid = self.addon.getSetting('uid')
        self.pwd = self.addon.getSetting('pwd')
        self.tsd = self.addon.getSetting('tsd')
        self.br = '141' if self.addon.getSetting('br') == 'high' else '148'
        self.ss = self.addon.getSetting('ss')
        self.view_mode = self.addon.getSetting('view_mode')
        self.view_epg = self.addon.getSetting('view_epg')
        self.serial = self.addon.getSetting('serial')

        self.debug = True
        common.dbg = self.debug

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)
        
        mode = params['mode'] if 'mode' in params else None
        self.cat = params['cat'] if 'cat' in params else ''
        self.token = params['token'] if 'token' in params else ''
        self.portal = urllib.unquote_plus(params['portal']) if 'portal' in params else ''
        self.numb = params['numb'] if 'numb' in params else ''
        self.has_pwd = params['pwd'] if 'pwd' in params else ''    
        self.has_rec = params['rec'] if 'rec' in params else '' 
        self.ts = params['ts'] if 'ts' in params else '' 
        self.cicon = urllib.unquote_plus(params['icon']) if 'icon' in params else '' 
        self.adt = params['dt'] if 'dt' in params else ''
        self.pid = params['pid'] if 'pid' in params else ''
        self.fid = params['fid'] if 'fid' in params else ''
        self.lid = params['lid'] if 'lid' in params else ''
        self.count = params['count'] if 'count' in params else ''
        self.offset = params['offset'] if 'offset' in params else ''
        self.word = params['word'] if 'word' in params else ''
        self.sort = params['sort'] if 'sort' in params else ''
                                
        if mode == 'tv':
            self.m_tv()
        elif mode == 'cat':
            self.m_cat()
        elif mode == 'tvplay':
            self.tv_play()
        elif mode == 'arch':
            self.m_arch()       
        elif mode == 'atv':
            self.m_atv()   
        elif mode == 'adate':
            self.m_adate()  
        elif mode == 'aepg':
            self.m_aepg()              
        elif mode == 'kino':
            self.m_kino() 
        elif mode == 'search':
            self.m_search() 
        elif mode == 'genres':
            self.m_genres() 
        elif mode == 'all':
            self.m_all() 
        elif mode == 'film':
            self.m_film()             
        elif mode == 'set':
            self.m_set() 
        elif mode == 'sort':
            self.m_sort()             
        else:
            self.m_main()
            
    def xmlerror(self, xml):
        msg = common.parseDOM(xml, "item", attrs={"name": "message"})[0]
        code  = common.parseDOM(xml, "item", attrs={"name": "code"})[0]
        if code == '4002':
            self.log('%s: %s' % (code, msg));
            self.get_auth = True
            return 
        self.showErrorMessage('%s: %s' % (code, msg))
        
    def alarm_set(self):
        xbmc.executebuiltin("XBMC.AlarmClock(%s,XBMC.Container.Refresh,%s,True)" % (('%s_refresh_list' % self.id), self.ttl))

    def alarm_reset(self):
        xbmc.executebuiltin("XBMC.CancelAlarm(%s,True)" % ('%s_refresh_list' % self.id))
 
    def cached_rst(self, fn):
        self.log("-cached_rst:")
 
        if os.path.isfile(fn) == True:
            self.log("--exist")
            try: os.remove(fn)
            except: pass

               
    def cached_get(self, type):
        self.log("-cached_get: %s" % type)
        cache = ''
        if type == 'tv':
            cquery = '&query=%s' % 'get_channels'
            fn = self.cache_chan
            tt = time.time()
        elif type == 'etv':
            cquery = '&query=%s&key="period|count"&value="%s|%s"' % ('get_epg', 60*60*3, 3)
            fn = self.cache_epg
            tt = time.time()
        elif type == 'dtv':
            tstart = str(int(time.time()))
            cquery = '&query=%s&key="start|period|count"&value="%s|%s|%s"' % ('get_epg', tstart, 60*60*3, 3)
            fn = self.cache_epg
            tt = time.time()
        elif type == 'atv':
            cquery = '&query=%s&key="start|period|number"&value="%s|%s|%s"' % ('get_epg', self.adt, 60*60*24, self.numb)
            fn = self.cache_epg
            tt = float(self.adt)
            type += self.numb
        else: return
        self.log("-tt: %s" % tt)
        
        if os.path.isfile(fn) == True:
            self.log("--exist")
            try:
                cf = open(fn, 'r')
                self.log("--opened")
                slast = cf.readline()
                flast = float(slast)
            except: flast = 0.0
            
            if abs(tt - flast) < 300:
                self.log("--toread")
                try: 
                    ctype = cf.readline()
                    if ctype.strip() == type:
                        cache = cf.readline()
                        self.log("--readline")
                except: pass
            cf.close()
            
        if cache == '':
            self.log("--empty")
#            tv = self.portal + '?token=%s&query=%s' % (self.token, 'get_channels')
#            resp = self.getPage({"link": tv})       
#            if self.get_auth == True:
#                self.log("--get_auth")
#                self.authorize()
#                if self.get_auth == False:
#                    self.log("--getpage")
#                    resp = self.getPage({"link": tv})

            self.authorize()
            if self.get_auth == False:
                self.log("--getpage")
                req = self.portal + '?token=%s' % self.token + cquery
                resp = self.getPage({"link": req})


            if resp != None:
                self.log("--gotit")
                cf = open(fn, 'w')
                cf.write(str(tt) + '\n')
                cf.write(type + '\n')
                cf.write(resp + '\n')
                cf.close()
                cache = resp
                
        return cache

    def getPage(self, cdict):
        self.log("-getPage:")
        resp = common.fetchPage(cdict)
        if resp["status"] == 200:
            status = common.parseDOM(resp["content"], "entity", ret="status")[0]
            self.timeserver = common.parseDOM(resp["content"], "entity", ret="timeserver")[0]
            if status == "success":
                self.get_auth = False
#                print resp["content"]
                return resp["content"]
            else:
                self.xmlerror(resp["content"])
            
        else:
            self.showErrorMessage('Error: %s' % (str(resp["status"])))
            
        return None
        
    def epg2dict(self, sepg):
        self.log("-epg2dict:")
        depg = {}
        a_raw = common.parseDOM(sepg, "row")
        for raw in a_raw:
            try: numb = common.parseDOM(raw, "item", attrs={"name": "number"})[0]
            except: numb = ''
            if numb != '':
                a_progs = common.parseDOM(raw, "array", attrs={"name": "programmes"})
                l_progs = []
                for progs in a_progs:
                    a_title = common.parseDOM(progs, "item", attrs={"name": "title"})
                    a_pid = common.parseDOM(progs, "item", attrs={"name": "pid"})
                    a_utstart = common.parseDOM(progs, "item", attrs={"name": "ut_start"})
                    a_utstop = common.parseDOM(progs, "item", attrs={"name": "ut_stop"})
                    a_has_desc = common.parseDOM(progs, "item", attrs={"name": "has_desc"})
                    a_desc = common.parseDOM(progs, "item", attrs={"name": "desc"})
                    a_has_rec = common.parseDOM(progs, "item", attrs={"name": "has_record"})
 
                    j = 0
                    for i in range(len(a_title)):
                        if a_has_desc[i] == '1':
                            desc = a_desc[j]
                            j += 1
                        else: desc = ''
                        
                        ststart = time.strftime("%H:%M",time.localtime(float(a_utstart[i])))
                        ststop = time.strftime("%H:%M",time.localtime(float(a_utstop[i])))
                        l_progs.append([ststart, ststop, a_title[i], desc, a_pid[i], a_has_rec[i]])
                    
                    depg[numb] = l_progs

#        print depg
        return depg        
        
    def authorize(self):

        device = 'xbmc'
        version = _VERSION_
        
        resp = self.getPage({"link": self.auth})
        if resp != None:
        
            tmserv = common.parseDOM(resp, "entity", ret="timeserver")[0]
            rand = common.parseDOM(resp, "item", attrs={"name": "rand"})[0]
            sid  = common.parseDOM(resp, "item", attrs={"name": "sid"})[0]
        
            resp = self.getPage({"link": self.auth 
                    + '?device=%s&version=%s&sid=%s&login=%s&passwd=%s&serial=%s' % 
                    (device, version, sid, self.uid, 
                    hashlib.md5( rand + hashlib.md5(self.pwd).hexdigest()).hexdigest(),
                    self.serial)})
                    
            if resp != None:
                self.get_auth = False
                self.token = common.parseDOM(resp, "item", attrs={"name": "token"})[0]
                self.portal = common.parseDOM(resp, "item", attrs={"name": "portal"})[0]
                self.ttl = common.parseDOM(resp, "item", attrs={"name": "ttl"})[0]
                
    def list_items(self, ictlg, view, films=False):
        self.log("-list_items:")
        
        for ctUrl, ctIcon, ctFolder, ctLabels  in ictlg:
            ctTitle = ctLabels['title']
            item = xbmcgui.ListItem(ctTitle, iconImage=ctIcon, thumbnailImage=ctIcon)
#            infoLabels = {'title':ename,
#              'tvshowtitle':sport,
#              'plot':plot,
#              'aired':start,
#              'premiered':start,
#              'duration':length}

            item.setInfo( type='Video', infoLabels=ctLabels)
            if ctFolder == False: item.setProperty('IsPlayable', 'true')
            item.setProperty('fanart_image', self.fanart)
            xbmcplugin.addDirectoryItem(self.handle, sys.argv[0] + ctUrl, item, ctFolder) 
            self.log("ctTitle: %s"  % ctTitle) 
            self.log("ctUrl: %s"  % ctUrl) 
            self.log("ctIcon: %s"  % ctIcon) 
            
        if self.view_mode == 'true':
            if films == False:
                xbmcplugin.setContent(self.handle, 'Episodes')
                self.log('Episodes')
            else:
                xbmcplugin.setContent(self.handle, 'Movies')
                self.log('Movies')
                if view: 
                    xbmc.executebuiltin('Container.SetViewMode("515")')
                    self.log('SetViewMode("515")')
                else:
                    xbmc.executebuiltin('Container.SetViewMode("503")')
                    self.log('SetViewMode("503")')   
        
        xbmcplugin.endOfDirectory(self.handle)
        
    def get_client(self):
        self.log("-get_client:")
        
        req = self.portal + '?token=%s&query=%s' % (self.token, 'get_client_info')
        resp = self.getPage({"link": req})
        if resp != None:
            if self.debug: print resp
  
    def get_settings(self):
        self.log("-get_settings:")
        
        req = self.portal + '?token=%s&query=%s' % (self.token, 'get_settings')
        resp = self.getPage({"link": req})
        if resp != None:
            if self.debug: print resp
                    
    def get_tstatus(self):
        self.log("-get_tstatus:")
        
        req = self.portal + '?token=%s&query=%s' % (self.token, 'get_token_status')
        resp = self.getPage({"link": req})
        if resp != None:
            if self.debug: print resp

    def set_settings(self, ts='0'):
        self.log("-set_settings:")
        
        key = 'bitrate|tshift'
        value = '%s|%s' % (self.br, ts)
        req = self.portal + '?token=%s&query=%s&key="%s"&value="%s"' % (self.token, 'set_settings', key, value)
        resp = self.getPage({"link": req})
        if resp != None:
            self.log('--resp:%s' % resp)
            
    def m_main(self):
        self.log("-m_main:")
        if self.uid == "":
            if not self.m_set(): return
            
        if self.serial == '':
            import uuid
            self.serial = '%s' % uuid.uuid4()
            self.addon.setSetting('serial', self.serial)

        self.authorize()
        if self.token == '':
            return
        self.set_settings(self.tsd)

#        self.get_tstatus()
#        self.get_client()
#        self.get_settings()
        
        ct_main = [('?mode=%s&token=%s&portal=%s&icon=%s' % ('cat', self.token, QT(self.portal), self.path_icons_tv,), self.path_icons_tv,   True, {'title': self.language(2000)} ),
#                  ('?mode=%s&token=%s&portal=%s&ts=%s' % ('cat', self.token, QT(self.portal), self.tsd),   self.path_icons_td,   True, {'title': self.language(2001)}),
                   ('?mode=%s&token=%s&portal=%s&icon=%s' % ('arch', self.token, QT(self.portal), self.path_icons_ts), self.path_icons_ts,   True, {'title': self.language(2002)}),
                   ('?mode=%s&token=%s&portal=%s&icon=%s' % ('kino', self.token, QT(self.portal), self.path_icons_kino), self.path_icons_kino, True, {'title': self.language(1001)}),
                   ('?mode=%s&token=%s&portal=%s&icon=%s' % ('set', self.token, QT(self.portal), self.path_icons_info), self.path_icons_info, True, {'title': self.language(2003)}) ]
                                          
        self.list_items(ct_main, True)
        
        self.cached_rst(self.cache_chan)
        self.cached_rst(self.cache_epg)

    def m_cat(self, nmode='tv'):
        self.log("-m_cat:")

        ct_cat = []    

        resp = self.cached_get('tv')

        if resp != '':
            a_cat = common.parseDOM(resp, "array", attrs={"name": "categories"})
            for cat in a_cat:
                a_title = common.parseDOM(cat, "item", attrs={"name": "title"})
                a_numb = common.parseDOM(cat, "item", attrs={"name": "number"})
                a_comb = zip(a_title, a_numb)
                for title, numb in a_comb:
                    params = '?mode=%s&cat=%s&token=%s&portal=%s' % (nmode, numb, self.token, QT(self.portal))
                    if self.ts != '': params += ('&ts=%s' % self.ts)
                    ct_cat.append((params, self.cicon, True, {'title': title}))

            self.list_items(ct_cat, True)
            
    def m_tv(self):
        self.log("-m_tv:")

        ct_chan = []    
        resp = self.cached_get('tv')
        if resp != None:
            if self.ts != '':
                d_epg = self.epg2dict(self.cached_get('dtv'))
            else:
                d_epg = self.epg2dict(self.cached_get('etv'))
            a_chan = common.parseDOM(resp, "array", attrs={"name": "channels"})
            for chan in a_chan:
                a_raw = common.parseDOM(chan, "row")
                for raw in a_raw:
                    try: cats = common.parseDOM(raw, "array", attrs={"name": "categories"})[0]
                    except: cats = ''
                    try: cat = common.parseDOM(cats, "item")[0]
                    except: cat = ''
                    if cat == self.cat:
                        try: has_passwd = common.parseDOM(raw, "item", attrs={"name": "has_passwd"})[0]
                        except: has_passwd = '0'
                        try: title = common.parseDOM(raw, "item", attrs={"name": "title"})[0]
                        except: title = ''
                        try: number = common.parseDOM(raw, "item", attrs={"name": "number"})[0]
                        except: number = ''
#                        has_record = common.parseDOM(raw, "item", attrs={"name": "has_record"})[0]
                        a_icon45 = common.parseDOM(raw, "item", attrs={"name": "icon_45_45"})
                        a_icon100 = common.parseDOM(raw, "item", attrs={"name": "icon_100_100"})
                        if len(a_icon100) > 0:
                            try: icon = a_icon100[0]
                            except: icon = ''
                        elif len(a_icon45) > 0:
                            try: icon = a_icon45[0]
                            except: icon = ''
                        if icon == '': icon = self.path_icons_tv

                        plot = ''
                        if title != '' and number != '':
                            try:
                                lepg = d_epg[number]
                                title2nd = ''
                                for ebgn, eend, ename, edescr, pid, rec in lepg:
                                    if self.view_epg == 'true' and title2nd == '':
                                        title2nd = '[COLOR FF0084FF]%s-%s[/COLOR] %s' % (ebgn, eend, ename)
                                    plot += '[B][COLOR FF0084FF]%s-%s[/COLOR] [COLOR FFFFFFFF] %s[/COLOR][/B][COLOR FF999999]\n%s[/COLOR]\n' % (ebgn, eend, ename, edescr)
                            except: pass
                            plot = plot.replace('&quot;','`').replace('&amp;',' & ')
                            title2nd = title2nd.replace('&quot;','`').replace('&amp;',' & ')
                            ct_chan.append(('?mode=%s&token=%s&portal=%s&numb=%s&pwd=%s&icon=%s' % ('tvplay', self.token, self.portal, number, has_passwd, icon),
                                            icon, False, {'title': '[B]%s[/B]\n%s' % (title, title2nd), 'plot':plot}))

            self.list_items(ct_chan, True)            


    def tv_play(self):
        self.log("-tv_play:")
        
        if self.has_rec == '0': return
        
        if self.has_pwd == '1': pcode = common.getUserInput(self.language(11005), '', True)
        
        resp = None
        self.authorize()
        if self.get_auth == False:
            req = self.portal + '?token=%s&query=%s' % (self.token, 'get_url')

            if self.pid == '' and self.lid == '':
                key = "number"
                value = self.numb
            elif self.lid == '':
                key = "pid"
                value = self.pid
            else:
                key = "lid"
                value = self.lid
            if self.has_pwd == '1':
                key += "|passwd"
                value += '|' + hashlib.md5( self.token + hashlib.md5(pcode).hexdigest()).hexdigest()
            req += '&key="%s"&value="%s"' % (key, value)
            resp = self.getPage({"link": req})

        if resp != None:
            try: url = common.parseDOM(resp, "item", attrs={"name": "url"})[0]
            except: return
            item = xbmcgui.ListItem(path = url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)
            self.log("-play_url:%s" % url)
 
                

    def m_arch(self):
        self.log("-m_arch:")
        self.m_cat(nmode='atv')

    def m_atv(self):
        self.log("-m_atv:")
        ct_chan = []    
        resp = self.cached_get('tv')
        if resp != None:
            a_chan = common.parseDOM(resp, "array", attrs={"name": "channels"})
            for chan in a_chan:
                a_raw = common.parseDOM(chan, "row")
                for raw in a_raw:
                    try: cats = common.parseDOM(raw, "array", attrs={"name": "categories"})[0]
                    except: cats = ''
                    try: cat = common.parseDOM(cats, "item")[0]
                    except: cat = ''
                    if cat == self.cat:
                        try: has_record = common.parseDOM(raw, "item", attrs={"name": "has_record"})[0]
                        except: has_record = ''
                        if has_record == '1':
                            try: has_passwd = common.parseDOM(raw, "item", attrs={"name": "has_passwd"})[0]
                            except: has_passwd = '0'
                            try: title = common.parseDOM(raw, "item", attrs={"name": "title"})[0]
                            except: title = ''
                            try: number = common.parseDOM(raw, "item", attrs={"name": "number"})[0]
                            except: number = ''
                            a_icon45 = common.parseDOM(raw, "item", attrs={"name": "icon_45_45"})
                            a_icon100 = common.parseDOM(raw, "item", attrs={"name": "icon_100_100"})
                            if len(a_icon100) > 0:
                                try: icon = a_icon100[0]
                                except: icon = ''
                            elif len(a_icon45) > 0:
                                try: icon = a_icon45[0]
                                except: icon = ''
                            if icon == '' : icon = self.path_icons_tv
                            if title != '' and number != '':
                                ct_chan.append(('?mode=%s&token=%s&portal=%s&numb=%s&pwd=%s&rec=%s&icon=%s' % ('adate', self.token, self.portal, number, has_passwd, has_record, icon), icon, True, {'title': title}))

            self.list_items(ct_chan, True)   
            
                    
    def m_adate(self):
        self.log("-m_adate:")
        
        dweek = {   0: self.language(20001),
                    1: self.language(20002),
                    2: self.language(20003),
                    3: self.language(20004),
                    4: self.language(20005),
                    5: self.language(20006),
                    6: self.language(20007)
                }

        ct_date = [] 
        dts = time.localtime()
        dnow = int(time.mktime((dts.tm_year, dts.tm_mon, dts.tm_mday, 0, 0, 0, 0, 0, 0)))
        for dt in range(dnow+(24*60*60), dnow - (14*24*60*60), -(24*60*60)):
            lt = time.localtime(dt)
            title = time.strftime("%x ", lt) + dweek[lt.tm_wday]
            ct_date.append(('?mode=%s&token=%s&portal=%s&numb=%s&pwd=%s&icon=%s&dt=%s' % 
            ('aepg', self.token, self.portal, self.numb, self.has_pwd, self.cicon, dt), self.cicon, True, {'title': title}))
            
        self.list_items(ct_date, True)

    def m_aepg(self):
        self.log("-m_aepg:")

        ct_chan = []    
        d_epg = self.epg2dict(self.cached_get('atv'))
        lepg = d_epg[self.numb]
        for ebgn, eend, ename, edescr, pid, rec in lepg:
            title = '%s-%s %s' % (ebgn, eend, ename)
            plot = '[COLOR FF999999]%s[/COLOR]' % (edescr)
            if rec != '1': title = '[COLOR FFdc5310]%s[/COLOR]' % (title)


            ct_chan.append(('?mode=%s&token=%s&portal=%s&numb=%s&pwd=%s&icon=%s&pid=%s&rec=%s' % ('tvplay', self.token, self.portal, self.numb, self.has_pwd, self.cicon, pid, rec), self.cicon, False, {'title': title, 'plot':plot}))

        self.list_items(ct_chan, False)   
                 
    def m_set(self):
        self.log("-m_set:")
        self.addon.openSettings()
        if self.uid == "": return False
        
        self.authorize()
        if self.get_auth == False:
            self.set_settings(self.tsd)
            self.get_settings()
        else:
            self.error('Authorization failed')

        self.cached_rst(self.cache_chan)
        self.cached_rst(self.cache_epg)        
        self.params = ''
        
        return True
        
    def m_kino(self):
        self.log("-m_kino:")
        
        ct_main = [('?mode=%s&token=%s&portal=%s&icon=%s' % ('search', self.token, QT(self.portal), self.path_icons_kino), self.path_icons_kino, True, {'title': self.language(1002)}),
                   ('?mode=%s&token=%s&portal=%s&icon=%s' % ('genres', self.token, QT(self.portal), self.path_icons_kino), self.path_icons_kino, True, {'title': self.language(1003)}),
                   ('?mode=%s&token=%s&portal=%s&icon=%s&offset=%s' % ('all', self.token, QT(self.portal), self.path_icons_kino, '0'), self.path_icons_kino,    True, {'title': self.language(1004)}) ]
                                          
        self.list_items(ct_main, True)

    def uni2enc(self, ustr):
        raw = ''
        uni = unicode(ustr, 'utf8')
        uni_sz = len(uni)
        for i in xrange(len(ustr)):
            raw += ('%%%02X') % ord(ustr[i])        
        return raw
    
    def m_search(self):
        self.log("-m_kino:")

        if self.word == '':
            self.word = self.uni2enc(common.getUserInput('', ''))
            self.offset = '0'
#            self.word = '%D0%BB%D0%B5%D1%82%D0%BE'

        
        if self.word != '':
            self.authorize()
            if self.get_auth == False:
                key = 'word|offset|count'
                value = '%s|%s|%s' % (self.word, self.offset, '12')
                req = self.portal + '?token=%s&query=%s' % (self.token, 'get_cinema_search')
                req += '&key="%s"&value="%s"' % (key, value)
                resp = self.getPage({"link": req})
                
                if resp != None:
                    ct_search = []
                    a_raw = common.parseDOM(resp, "row")
                    for raw in a_raw:
                        try: title = common.parseDOM(raw, "item", attrs={"name": "title"})[0]
                        except: title = ''
                        try: small_desc = common.parseDOM(raw, "item", attrs={"name": "small_desc"})[0]
                        except: small_desc = ''
                        try: kp_rate = common.parseDOM(raw, "item", attrs={"name": "kp_rate"})[0]
                        except: kp_rate= ''
                        try: imdb_rate = common.parseDOM(raw, "item", attrs={"name": "imdb_rate"})[0]
                        except: imdb_rate = kp_rate
                        try: file_count = common.parseDOM(raw, "item", attrs={"name": "file_count"})[0]
                        except: file_count= ''
                        try: fid = common.parseDOM(raw, "item", attrs={"name": "fid"})[0]
                        except: fid= ''
                        try: year = common.parseDOM(raw, "item", attrs={"name": "year"})[0]
                        except: year= ''
                        try: small_cover = common.parseDOM(raw, "item", attrs={"name": "small_cover"})[0]
                        except: small_cover= ''

                        if title != '' and fid != '':
                            ct_search.append(('?mode=%s&token=%s&portal=%s&fid=%s' % ('film', self.token, self.portal, fid), small_cover, True,
                             {'title': title, 
                             'rating': imdb_rate, 
                              'plot': '%s IMDB: %s Kinopoisk:%s\n%s' % (year, imdb_rate, kp_rate, small_desc),
                              'year':year} ))

                    if len(a_raw) >= 12:
                        ct_search.append(('?mode=%s&token=%s&portal=%s&word=%s&offset=%s' % ('search', self.token, self.portal, self.word, str(int(self.offset) + 12)), '', True, {'title': self.language(20008)}))
                    self.list_items(ct_search, True) 

    def m_genres(self):
        self.log("-m_genres:")
        
        resp = None
        self.authorize()
        if self.get_auth == False:
            req = self.portal + '?token=%s&query=%s' % (self.token, 'get_cinema_genre_info')
            resp = self.getPage({"link": req})

        if resp != None:
            ct_genres = []
            try: genres = common.parseDOM(resp, "array", attrs={"name": "genres"})[0]
            except: genres = ''
            a_raw = common.parseDOM(genres, "row")
            for raw in a_raw:
                try: cnt = common.parseDOM(raw, "item", attrs={"name": "count"})[0]
                except: cnt = ''
                try: title = common.parseDOM(raw, "item", attrs={"name": "title"})[0]
                except: title = ''
                try: number = common.parseDOM(raw, "item", attrs={"name": "number"})[0]
                except: number = ''
                if title != '' and number != '':
                    ct_genres.append(( '?mode=%s&token=%s&portal=%s&numb=%s&offset=%s&icon=%s' % ('all', self.token, self.portal, number, '0', self.cicon), 
                    self.cicon, True, {'title': '[B]%s [/B][COLOR FF999999](%s)[/COLOR]' % (title, cnt)} ))

            self.list_items(ct_genres, True)   


    def m_all(self):
        self.log("-m_kino:")
        
        resp = None
        self.authorize()
        if self.get_auth == False:
            key = 'offset|count'
            value = '%s|%s' % (self.offset, '12')
            if self.numb != '':
                key += '|num_genre'
                value += '|%s' % (self.numb)
            if self.sort != '':
                key += '|sort'
                value += '|%s' % (self.sort)                
            req = self.portal + '?token=%s&query=%s' % (self.token, 'get_cinema_films')
            req += '&key="%s"&value="%s"' % (key, value)
            resp = self.getPage({"link": req})
            
            if resp != None:
                ct_search = []
                a_raw = common.parseDOM(resp, "row")
                print len(a_raw)
                if len(a_raw) >= 12:
                    req = '?mode=%s&token=%s&portal=%s' % ('sort', self.token, self.portal)
                    if self.numb != '': req += '&numb=%s' % self.numb
                    ct_search.append((req, self.path_icons_kino, True, {'title': self.language(1005)}))
                print ct_search
                for raw in a_raw:
                    try: title = common.parseDOM(raw, "item", attrs={"name": "title"})[0]
                    except: title = ''
                    try: small_desc = common.parseDOM(raw, "item", attrs={"name": "small_desc"})[0]
                    except: small_desc = ''
                    try: kp_rate = common.parseDOM(raw, "item", attrs={"name": "kp_rate"})[0]
                    except: kp_rate = ''
                    try: imdb_rate = common.parseDOM(raw, "item", attrs={"name": "imdb_rate"})[0]
                    except: imdb_rate = kp_rate
                    try: file_count = common.parseDOM(raw, "item", attrs={"name": "file_count"})[0]
                    except: file_count = ''
                    try: fid = common.parseDOM(raw, "item", attrs={"name": "fid"})[0]
                    except: fid = ''
                    try: year = common.parseDOM(raw, "item", attrs={"name": "year"})[0]
                    except: year = ''
                    try: small_cover = common.parseDOM(raw, "item", attrs={"name": "small_cover"})[0]
                    except: small_cover = ''
                    if title != '' and fid != '':
                        ct_search.append(('?mode=%s&token=%s&portal=%s&fid=%s' % ('film', self.token, self.portal, fid), small_cover, True,
                         {'title': title, 
                          'rating': imdb_rate,                         
                          'plot': '%s IMDB: %s Kinopoisk:%s\n%s' % (year, imdb_rate, kp_rate, small_desc),
                          'year':year} ))
                if len(a_raw) >= 12:
                    req = '?mode=%s&token=%s&portal=%s&offset=%s' % ('all', self.token, self.portal, str(int(self.offset) + 12))
                    if self.numb != '': req += '&numb=%s' % self.numb
                    if self.sort != '': req += '&sort=%s' % self.sort
                    ct_search.append((req, '', True, {'title': self.language(20008)}))
                self.list_items(ct_search, True, True) 

 
    def m_film(self):
        self.log("-f_play:")
        
        resp = None
        self.authorize()
        if self.get_auth == False:

            req = self.portal + '?token=%s&query=%s' % (self.token, 'get_cinema_desc')
            key = "fid"
            value = self.fid
            req += '&key="%s"&value="%s"' % (key, value)
            resp = self.getPage({"link": req})
        
        if resp != None:
            ct_films = []
            a_files = common.parseDOM(resp, "array", attrs={"name": "files"})
            try: desc = common.parseDOM(resp, "item", attrs={"name": "full_desc"})[0]
            except: desc = ''
            try: icon = common.parseDOM(resp, "item", attrs={"name": "big_cover"})[0]
            except: icon = ''
            
            try: country = common.parseDOM(resp, "item", attrs={"name": "country"})[0]
            except: country = ''
            try: prod_date = common.parseDOM(resp, "item", attrs={"name": "prod_date"})[0]
            except: prod_date = ''

            try: rate_imdb = common.parseDOM(resp, "item", attrs={"name": "rate_imdb"})[0]
            except: rate_imdb = ''
            try: rate_kp = common.parseDOM(resp, "item", attrs={"name": "rate_kp"})[0]
            except: rate_kp = ''
            if rate_imdb == '': rate_imdb = rate_kp
                                    
            a_genres = common.parseDOM(resp, "array", attrs={"name": "genres"})
            genre = ''
            for genres in a_genres:
                a_gen = common.parseDOM(genres, "item", attrs={"name": "title"})
                for gen in a_gen:
                    genre += '%s, ' % gen 
            
            a_actors = common.parseDOM(resp, "array", attrs={"name": "actors"})
            cast = []
            for actors in a_actors:
                a_act = common.parseDOM(actors, "item", attrs={"name": "title"})
                for act in a_act:
                    cast.append(act)

            a_dir = common.parseDOM(resp, "array", attrs={"name": "producers"})
            director = ''
            for dirs in a_dir:
                a_dir = common.parseDOM(dirs, "item", attrs={"name": "title"})
                for dir in a_dir:
                    director += '%s, ' % dir 
                                 
            rest = resp
            try: rest = rest.replace(common.parseDOM(resp, "array", attrs={"name": "producers"})[0].encode('utf8'), '@@')
            except: pass
            try: rest = rest.replace(common.parseDOM(resp, "array", attrs={"name": "genres"})[0].encode('utf8'), '@@')
            except: pass
            try: rest = rest.replace(common.parseDOM(resp, "array", attrs={"name": "actors"})[0].encode('utf8'), '@@')
            except: pass
            try: title = common.parseDOM(rest, "item", attrs={"name": "title"})[-1]
            except: title = ''

            for efile in a_files:
                a_quals = common.parseDOM(resp, "array", attrs={"name": "qualities"})
                if len(a_quals) > 1: i = 1
                else: i = 0
                for quals in a_quals:
                    a_lid = common.parseDOM(quals, "item", attrs={"name": "lid"})
                    a_qual= common.parseDOM(quals, "item", attrs={"name": "quality_number"})
                    a_comb = zip(a_lid, a_qual)
                    if len(a_qual) > 1: q = 1
                    else: q = 0
                    for lid, qual in a_comb:
                        if q > 0: qn = 'Q%s-' % qual
                        else: qn = ''
                        if i > 0: 
                            name = '%s%s (%s %s)' % (qn, title, self.language(20009), str(i))
                            i += 1
                        else: name = '%s%s' % (qn, title)
                        
                        ct_films.append(('?mode=%s&token=%s&portal=%s&lid=%s' % ('tvplay', self.token, self.portal, lid), icon, False,
                                {'title': name, 
                                 'genre': genre[0:-2], 
                                 'director': director[0:-2], 
                                 'country': country, 
                                 'year': prod_date, 
                                 'rating': rate_imdb, 
                                 'plot': desc} ))
                        
            self.list_items(ct_films, False, True) 

       
    def m_sort(self):
        self.log("-m_sort:")
        
        ct_smode = [(self.language(1006), 'imdb'),
                    (self.language(1007), 'kp'),
                    (self.language(1008), 'proddate'),
                    (self.language(1009), 'pubdate')]
                    
        ct_sort = []
        creq = '?mode=%s&token=%s&portal=%s&offset=%s' % ('all', self.token, QT(self.portal), '0')
        if self.numb != '':
            creq += '&numb=%s' % (self.numb)
        for smode in ct_smode:
            req = creq + '&sort=%s' % (smode[1])
            ct_sort.append( (req, self.path_icons_kino, True, {'title': smode[0]}))
                                         
        self.list_items(ct_sort, True)
        
    # *** Add-on helpers
    def log(self, message):
        if self.debug:
            print "[%s LOG]: %s" % (common.plugin, message.encode('utf8'))

    def error(self, message):
        print "[%s ERROR]: %s" % (common.plugin, message)

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')
        
rodina = RodinaTV()
rodina.main()        