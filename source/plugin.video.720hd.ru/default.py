#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2012, Silhouette, E-mail: 
# Rev. 3.3.0


import urllib, urllib2, os, re, sys, json, cookielib, base64, socket
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup
import requests
import lib.moonwalk as moonwalk

try:
  # Import UnifiedSearch
  sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
  from unified_search import UnifiedSearch
except: pass

__settings__ = xbmcaddon.Addon(id='plugin.video.720hd.ru')
use_translit = __settings__.getSetting('translit')

try:  
  import Translit as translit
  translit = translit.Translit()  
except: use_translit = 'false'

dbg = 0


socket.setdefaulttimeout(120)

QUALITY_TYPES = (360, 480, 720, 1080)

supported = {'vk.com', 'vkontakte.ru', 'kinolot.com', 'mail.ru', 'moonwalk.cc', 'moonwalk.co', 'hdgo.cc'}

pluginhandle = int(sys.argv[1])

start_pg = "http://720hd.ru/"
filmy_pg = "filmy/"
page_pg = "page/"
find_pg = "http://720hd.ru/?do=search&subaction=search&story="
search_start = "&search_start="

def gettranslit(msg):
    if use_translit == 'true': 
        return translit.rus(msg)
    else: return msg

def dbg_log(line):
    if dbg: xbmc.log(line)

# def get_url(url, data = None, cookie = None, save_cookie = False, referrer = None, opts=None):
#     dbg_log("get_url=>%s"%url)
#     if data: dbg_log("data=>%s"%data)
#     if cookie: dbg_log("cookie=>%s" % cookie)
#     if data: dbg_log("referrer=>%s" % referrer)
#     req = urllib2.Request(url)
#     req.add_header('User-Agent', 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0')
# #     req.add_header('Accept', 'text/html, application/xml, application/xhtml+xml, */*')
#     req.add_header('Accept', '*/*')
#     req.add_header('Accept-Language', 'ru,en;q=0.9')
#     if cookie: req.add_header('Cookie', cookie)
#     if referrer: req.add_header('Referer', referrer)
#     if opts:
#         for x1, x2 in opts:
#             req.add_header(x1, x2)
# 
#     if data: 
#         response = urllib2.urlopen(req, data)
#     else:
#         response = urllib2.urlopen(req,timeout=30)
#     link=response.read()
#     if save_cookie:
#         setcookie = response.info().get('Set-Cookie', None)
#         if setcookie:
#             setcookie = re.search('([^=]+=[^=;]+)', setcookie).group(1)
#             link = link + '<cookie>' + setcookie + '</cookie>'
#     
#     response.close()
#     return link

def req_url(url, opts = None, cookies = None, params = None, data = None):
    dbg_log("req_url=>%s"%url)
    dbg_log("_params=>%s"%str(params))
    

    headers = {'User-Agent' : 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0',
               'Accept' : '*/*',
               'Accept-Language' : 'ru,en;q=0.9'
               }
    if opts: 
        headers.update(opts)
        dbg_log("_opts=>%s"%str(opts))
        
    if data :
        dbg_log("_data=>%s"%str(data))
        r = requests.post(url, headers=headers, cookies = cookies, params = params, data = data)
    else:
        r = requests.get(url, headers=headers, cookies = cookies, params = params)
        
    return r


def HD7_start(url, page, cook):
    dbg_log('-HD7_start:' + '\n')
    dbg_log('- url:'+  url + '\n')
    dbg_log('- page:'+  page + '\n')
    dbg_log('- cook:'+  cook + '\n')    
    ext_ls = [('<КАТАЛОГ>', '?mode=ctlg'),
              ('<ПОИСК>', '?mode=find')]
    unis_res = []
    unis_en = False
    unds_en = False
    
    if cook == "unis":
        cook = ""
        unis_en = True
    elif cook == "unds":
        cook = ""
        unds_en = True
    else:
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')#movies episodes tvshows    
              
    if url.find(find_pg) != -1:
        n_url = url + search_start + page
    elif page == "0":
        n_url = url
    else:
        n_url = url + filmy_pg + page_pg + page + '/'
        
    dbg_log('- n_url:'+  n_url + '\n')

    if cook : cookies = json.loads(cook)
    else: cookies = None

    req = req_url(n_url, cookies = cookies)
    horg = req.content
    if req.cookies.get_dict():
        cook = json.dumps(req.cookies.get_dict())
    else: cook = ''

    i = 0
    
    if not unis_en and not unds_en:
      for ctTitle, ctMode  in ext_ls:
        item = xbmcgui.ListItem(ctTitle)
        uri = sys.argv[0] + ctMode + '&cook=' + urllib.quote_plus(cook)
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)  
        dbg_log('- uri:'+  uri + '\n')    
    

#     dbg_log('- horg:'+  horg + '\n')
    
    articles = BeautifulSoup(horg).findAll('div',{"class":"article-film"})
#     dbg_log('- articles:'+  str(articles) + '\n')

    for article in articles:
        
#         dbg_log('- article:'+  str(article) + '\n')
        
        hrefs = re.compile('<div class="article-film-title"><a href="(.*?)">(.*?)</a></div>').findall(str(article))
        
        try: img = start_pg + re.compile('<img class="article-img" src="(.*?)"').findall(str(article))[0][1:]
        except: img = ''
        try: plot = re.compile('<div class="article-film-descr-content">(.*?)</div>').findall(str(article))[0]
        except: plot = ''
        try: r1 = re.compile('КиноПоиск: (.*?) ').findall(plot)[0]
        except: r1 = ''
        try: r2 = re.compile('IMDB: (.*?) ').findall(plot)[0]
        except: r2 = ''
        
        if len(hrefs):
            href = hrefs[0][0]
            title = "%s (%s/%s)"%(hrefs[0][1],r1,r2)
            dbg_log('-HREF %s'%href)
            dbg_log('-TITLE %s'%title)
            dbg_log('-IMG %s'%img)
            dbg_log('-PLOT %s'%plot)
            dbg_log('-R1 %s'%r1)
            dbg_log('-R2 %s'%r2)

            if unis_en == False:
                item = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                try: item.setInfo( type='video', infoLabels={'title': title, 'plot': plot})
                except: item.setInfo( type='video', infoLabels={'title': title})
                item.setArt({'thumb': img, 'poster': img})
#                     item.setArt({'thumb': img, 'poster': img, 'fanart': img})
                uri = sys.argv[0] + '?mode=view' \
                + '&url=' + urllib.quote_plus(href) + '&img=' + urllib.quote_plus(img) \
                 + '&name=' + urllib.quote_plus(title)+ '&cook=' + urllib.quote_plus(cook)
                xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)  
                dbg_log('- uri:'+  uri + '\n')
            else:
                try: unis_res.append({'title':  title, 'url': href, 'image': img, 'plugin': 'plugin.video.new-kino.net'})
                except: pass
                
            i = i + 1
    
    if unis_en == True:
      try: UnifiedSearch().collect(unis_res)
      except:  pass
    else:
      if i and not unds_en:
        item = xbmcgui.ListItem('<NEXT PAGE>')
        uri = sys.argv[0] + '?page=' + str(int(page) + 1) + '&url=' + urllib.quote_plus(url)+ '&cook=' + urllib.quote_plus(cook)
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)
        dbg_log('- uri:'+  uri + '\n')
        item = xbmcgui.ListItem('<NEXT PAGE +10>')
        uri = sys.argv[0] + '?page=' + str(int(page) + 10) + '&url=' + urllib.quote_plus(url)+ '&cook=' + urllib.quote_plus(cook)
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)
        dbg_log('- uri:'+  uri + '\n')        
 
      xbmcplugin.endOfDirectory(pluginhandle) 

def getSite(s):

    try: full = re.compile('//(.*?)/').findall(s)[0]
    except: 
        try: full = re.compile('(.*?)/').findall(s)[0]
        except:
            try: full = re.compile('//(.*?)').findall(s)[0]
            except: full = s
    parts = full.split('.')
    psz = len(parts)
    if psz == 4:
      site = full
    elif psz > 1:
        site = '%s.%s'%(parts[psz - 2], parts[psz - 1])
    else: site = full
    
    return site

def HD7_view(url, img, name, cook):     
    dbg_log('-HD7_view:'+ '\n')
    dbg_log('- url:'+  url + '\n')
    dbg_log('- img:'+  img + '\n')
    dbg_log('- name:'+  name + '\n')
        
    if cook : cookies = json.loads(cook)
    else: cookies = None
    
    req = req_url(url, cookies = cookies)
    http = req.content
    
    if req.cookies.get_dict():
        cook = json.dumps(req.cookies.get_dict())
    else: cook = ''
    
    dbg_log('- ncook:'+  cook + '\n')

    frames = re.compile('<iframe src="(.*?)"').findall(http)
    xtraf = re.compile('<div id="hdgoplayer">.+?src="(.*?)"', re.MULTILINE|re.DOTALL).findall(http)
    if len(xtraf): frames.extend(xtraf)

    if len(frames) > 0:

        i = 1
        try: plot = re.compile('<br>.+?<center>(.*?)<br />', re.MULTILINE|re.DOTALL).findall(http)[0].decode('cp1251').encode('utf-8')
        except: plot = ''
#         xbmc.log(str(plot).decode('cp1251').encode('utf-8'))     
#        http = re.sub('<br />', '', horg)
        wdic = { '' : 0}
        for file in frames:
            

            if 'facebook' not in file:
                try: 
                    web = getSite(file)
                except: 
                    web = ''
                    
                dbg_log('- web:'+  str(web) + '\n')

                if web in wdic: 
                    t = wdic[web] + 1
                    wdic[web] = t
                else: wdic[web] = 1
                
                if web[0].isdigit():
                    title = '[[COLOR FFFFFF00]%s-%s[/COLOR]] %s'%(str(wdic[web]),web,name)
                elif web not in supported:
                    title = '[[COLOR FFFF0000]%s-%s[/COLOR]] %s'%(str(wdic[web]),web,name)
                else:
                    title = '[%s-%s] %s'%(str(wdic[web]),web,name)
                
                if 'http' not in file:
                    file = 'http:' + file 
                    
                dbg_log('- file:'+  file + '\n')
    
                item = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                uri = sys.argv[0] + '?mode=play' \
                + '&name=' + urllib.quote_plus(name) \
                + '&web=' + urllib.quote_plus(web) \
                + '&ref=' + urllib.quote_plus(url) \
                + '&url=' + urllib.quote_plus(file) + '&cook=' + urllib.quote_plus(cook)
                item.setProperty('IsPlayable', 'true')
                item.setInfo( type='video', infoLabels={'title': title, 'plot': plot})
                item.setArt({'thumb': img, 'poster': img})
                xbmcplugin.addDirectoryItem(pluginhandle, uri, item)  
                dbg_log('- uri:'+  uri + '\n')

        xbmcplugin.endOfDirectory(pluginhandle)


def Decode2(param):
        try:
            hk = ("0123456789WGXMHRUZID=NQVBLihbzaclmepsJxdftioYkngryTwuvihv7ec41D6GpBtXx3QJRiN5WwMf=ihngU08IuldVHosTmZz9kYL2bayE").split('ih')
            hash_key = hk[0]+'\n'+hk[1]

            #-- define variables
            loc_3 = [0,0,0,0]
            loc_4 = [0,0,0]
            loc_2 = ''

            #-- define hash parameters for decoding
            dec = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
            hash1 = hash_key.split('\n')[0]
            hash2 = hash_key.split('\n')[1]

            #-- decode
            for i in range(0, len(hash1)):
                re1 = hash1[i]
                re2 = hash2[i]

                param = param.replace(re1, '___')
                param = param.replace(re2, re1)
                param = param.replace('___', re2)

            i = 0
            while i < len(param):
                j = 0
                while j < 4 and i+j < len(param):
                    loc_3[j] = dec.find(param[i+j])
                    j = j + 1

                loc_4[0] = (loc_3[0] << 2) + ((loc_3[1] & 48) >> 4);
                loc_4[1] = ((loc_3[1] & 15) << 4) + ((loc_3[2] & 60) >> 2);
                loc_4[2] = ((loc_3[2] & 3) << 6) + loc_3[3];

                j = 0
                while j < 3:
                    if loc_3[j + 1] == 64 or loc_4[j] == 0:
                        break

                    loc_2 += unichr(loc_4[j])

                    j = j + 1
                i = i + 4;
        except:
            loc_2 = ''

        return loc_2

def DecodeUppodText2(sData):
  hash = "0123456789WGXMHRUZID=NQVBLihbzaclmepsJxdftioYkngryTwuvihv7ec41D6GpBtXx3QJRiN5WwMf=ihngU08IuldVHosTmZz9kYL2bayE"

#  Проверяем, может не нужно раскодировать (json или ссылка)
#  if ((Pos("{", sData)>0) || (LeftCopy(sData, 4)=="http")) return HmsUtf8Decode(sData);

  sData = DecodeUppod_tr(sData, "r", "A")
  
  hash = hash.replace('ih', '\n')
  if sData[-1] == '!' :
    sData = sData[:len(sData)-1]
    tab_a = hash.split('\n')[3]
    tab_b = hash.split('\n')[2]
  else:
    tab_a = hash.split('\n')[1]
    tab_b = hash.split('\n')[0]

  sData = sData.replace("\n", "")
  
  for i in range(1, len(tab_a)):
    char1 = tab_b[i]
    char2 = tab_a[i]
    sData = sData.replace(char1, "___")
    sData = sData.replace(char2, char1)
    sData = sData.replace("___", char2)

  sData = DecodeUppod_Base64(sData)
  sData = sData.replace("hthp:", "http:")
  return sData

def DecodeUppod_tr(sData, ch1, ch2):
  s = ""
  if (sData[len(sData)-1] == ch1) and (sData[3] == ch2):
    nLen = len(sData);
    for i in range(nLen, 1, -1): s += sData[i]
    loc3 = Int(Int(s[nLen-1:nLen])/2)
    s = s[3, nLen-2]
    i = loc3
    if loc3 < len(s):
      while (i < len(s)):
        s = s[:i] + s[i+2:]
        i+= loc3
    sData = s + "!"

  return sData
  
  
def DecodeUppod_Base64(param):
    #-- define variables
    loc_3 = [0,0,0,0]
    loc_4 = [0,0,0]
    loc_2 = ''
    #-- define hash parameters for decoding
    dec = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    i = 0
    while i < len(param):
        j = 0
        while j < 4 and i+j < len(param):
            loc_3[j] = dec.find(param[i+j])
            j = j + 1

        loc_4[0] = (loc_3[0] << 2) + ((loc_3[1] & 48) >> 4);
        loc_4[1] = ((loc_3[1] & 15) << 4) + ((loc_3[2] & 60) >> 2);
        loc_4[2] = ((loc_3[2] & 3) << 6) + loc_3[3];

        j = 0
        while j < 3:
            if loc_3[j + 1] == 64: break
            loc_2 += unichr(loc_4[j])
            j = j + 1
        i = i + 4

    return loc_2        
    
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
# This is not clearly defined otherwise
compiled_regex_type = type(re.compile(''))

def int_or_none(v, scale=1, default=None, get_attr=None, invscale=1):
    if get_attr:
        if v is not None:
            v = getattr(v, get_attr, None)
    if v == '':
        v = None
    if v is None:
        return default
    try:
        return int(v) * invscale // scale
    except ValueError:
        return default

class VKIE():
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                (?:(?:m|new)\.)?vk\.com/video_|
                                (?:www\.)?daxab.com/
                            )
                            ext\.php\?(?P<embed_query>.*?\boid=(?P<oid>-?\d+).*?\bid=(?P<id>\d+).*)|
                            (?:
                                (?:(?:m|new)\.)?vk\.com/(?:.+?\?.*?z=)?video|
                                (?:www\.)?daxab.com/embed/
                            )
                            (?P<videoid>-?\d+_\d+)(?:.*\blist=(?P<list_id>[\da-f]+))?
                        )
                    '''


    def _search_regex(self, pattern, string, name, flags=0, group=None):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj:
                    break

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            else:
                return mobj.group(group)
        else:
            return None

    def _html_search_regex(self, pattern, string, name, flags=0, group=None):
        """
        Like _search_regex, but strips HTML tags and unescapes entities.
        """
        res = self._search_regex(pattern, string, name, flags, group)
        if res:
            return res.strip()
        else:
            return res

    def _real_extract(self, url):
        dbg_log('-_real_extract:\n')
        dbg_log('-url:' + url + '\n')
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        dbg_log('--video_id:' + str(video_id) + '\n')
        if not video_id:
            info_url = 'http://vk.com/video_ext.php?' + mobj.group('embed_query')
            dbg_log('--info_url:' + info_url + '\n')
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))
            dbg_log('--video_id:' + video_id + '\n')
            
        if video_id:
            info_url = 'https://vk.com/al_video.php?act=show&al=1&module=video&video=%s' % video_id
            dbg_log('--info_url:' + info_url + '\n')
            # Some videos (removed?) can only be downloaded with list id specified
            list_id = mobj.group('list_id')
            if list_id:
                info_url += '&list=%s' % list_id
                dbg_log('--info_url:' + info_url + '\n')

        info_page = req_url(info_url).content

        error_message = self._html_search_regex(
            [r'(?s)<!><div[^>]+class="video_layer_message"[^>]*>(.+?)</div>',
             r'(?s)<div[^>]+id="video_ext_msg"[^>]*>(.+?)</div>'],
            info_page, 'error message')

        if error_message:
            return None

        if re.search(r'<!>/login\.php\?.*\bact=security_check', info_page):
            return None

        m_rutube = re.search(
            r'\ssrc="((?:https?:)?//rutube\.ru\\?/(?:video|play)\\?/embed(?:.*?))\\?"', info_page)
        if m_rutube is not None:
            return m_rutube.group(1).replace('\\', '')

        m_opts = re.search(r'(?s)var\s+opts\s*=\s*({.+?});', info_page)
        if m_opts:
            m_opts_url = re.search(r"url\s*:\s*'((?!/\b)[^']+)", m_opts.group(1))
            dbg_log('--m_opts_url:' + m_opts_url + '\n')
            if m_opts_url:
                opts_url = m_opts_url.group(1)
                if opts_url.startswith('//'):
                    opts_url = 'http:' + opts_url
                dbg_log('--opts_url:' + opts_url + '\n')
                return self.url_result(opts_url)

        rdata = self._search_regex(r'<!json>\s*({.+?})\s*<!>', info_page, 'json')
        jdata = json.loads(rdata.decode('cp1251').encode('utf-8'))
        data = jdata['player']['params'][0]

        formats = []
        for format_id, format_url in data.items():
            if not isinstance(format_url, compat_str) or not format_url.startswith(('http', '//', 'rtmp')):
                continue
            if format_id.startswith(('url', 'cache')) or format_id in ('extra_data', 'live_mp4'):
                height = int_or_none(self._search_regex(
                    r'^(?:url|cache)(\d+)', format_id, 'height'))
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'height': height,
                })
            # elif format_id == 'hls':
            #     formats.extend(self._extract_m3u8_formats(
            #         format_url, video_id, 'mp4', m3u8_id=format_id,
            #         fatal=False, live=True))
            # elif format_id == 'rtmp':
            #     formats.append({
            #         'format_id': format_id,
            #         'url': format_url,
            #         'ext': 'flv',
            #     })
        return self._sort_fid(formats)
        #         self._sort_formats(formats)

    def _sort_fid(self, uslist):
        nurl = None
        fids = ['url720', 'cache720', 'url480', 'cache480', 'url360', 'cache360', 'url240', 'cache240']
        for fid in fids:
            for item in uslist:
                if item['format_id'] == fid:
                    dbg_log('- nurl:' + str(nurl) + '\n')
                    nurl = item['url']
                    break

            if nurl != None: break

        return nurl

def get_rutube(url, videoId=None):
    dbg_log('-get_rutube:' + '\n')
    dbg_log('- url-in:' + url + '\n')
    c = 0
    if not videoId:
        if 'rutube.ru' in url:
            try:
                videoId = re.findall('rutube.ru/play/embed/(.*?)"', url)[0]
            except:
                try:
                    videoId = re.findall('rutube.ru/video/(.*?)/', url)[0]
                except:
                    pass

    if videoId:
        url = 'http://rutube.ru/api/play/options/' + videoId + '?format=json'
        dbg_log('- url-req:' + url + '\n')
        request = urllib2.Request(url)
        request.add_header('User-agent',
                           'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
        try:
            response = urllib2.urlopen(request)
            resp = response.read()
        except:
            pass

        jsonDict = json.loads(resp)
        link = urllib.quote_plus(jsonDict['video_balancer']['m3u8'])

        return link
    else:
        return None

def get_VK(url, n = 0):
    dbg_log('-get_VK:' + '\n')
    dbg_log('- url:' + url + '\n')

    newVK = VKIE()
    nurl = newVK._real_extract(url)

    if nurl and 'rutube' in nurl:
        nurl = get_rutube(nurl.replace('?','"'))

    return nurl
    
def get_YTD(url):
    import YDStreamExtractor
    
    vid = YDStreamExtractor.getVideoInfo(url,resolve_redirects=True)
    dbg_log('- YTD: \n')
    if vid:
        dbg_log('- YTD: Try\n')
        stream_url = vid.streamURL()
#         stream_url = vid.streamURL().split('|')[0]
        dbg_log('- surl:'+  stream_url + '\n')

    else: 
        dbg_log('- YTD: None\n')
        return None
              
        
def get_mailru(url):
    try:
        url = url.replace('/my.mail.ru/video/', '/api.video.mail.ru/videos/embed/')
        url = url.replace('/my.mail.ru/mail/', '/api.video.mail.ru/videos/embed/mail/')
        url = url.replace('/videoapi.my.mail.ru/', '/api.video.mail.ru/')
        result = req_url(url).content

        url = re.compile('"metadataUrl" *: *"(.+?)"').findall(result)[0]
        req = req_url(url)
        if req.cookies.get_dict():
            cookie = json.dumps(req.cookies.get_dict())
        else: cookie = ''
        h = "|Cookie=%s" % urllib.quote(cookie)

        result = ret_url(url).content
        result = json.loads(result)
        result = result['videos']

        url = []
        url += [{'quality': '1080p', 'url': i['url'] + h} for i in result if i['key'] == '1080p']
        url += [{'quality': 'HD', 'url': i['url'] + h} for i in result if i['key'] == '720p']
        url += [{'quality': 'SD', 'url': i['url'] + h} for i in result if not (i['key'] == '1080p' or i ['key'] == '720p')]

        if url == []: return None
        return url
    except:
        return None


def get_hdgo(url, ref, cook):
    dbg_log('-get_hdgo:' + '\n')
    dbg_log('- url:'+  url + '\n')
    dbg_log('- ref:'+  ref + '\n')
    dbg_log('- cook:'+  str(cook) + '\n')
    
    if 'api' in url:
        req = req_url(url, opts = {'Referer' : ref})
        page = req.content
        try: url = re.findall('"src", "(.*?)"', page)[0]
        except: return None
    
    req = req_url(url, opts = {'Referer' : ref})
    page = req.content
        
    xbmc.log(page)
    try: src = re.findall('<iframe src="(.*?)"', page)[0]
    except: return None    
    req = req_url(src, opts = {'Referer' : url})
    page = req.content
        
    xbmc.log(page)
    
    try: urls = re.findall("{url: '(.*?)'", page)
    except: return None
    
    nurls = []
    for iurl in urls:
        nurls.append(iurl + "|Referer="+src)
 
    xbmc.log(str(nurls))
    
    return nurls

def get_moonwalk(url, ref):
    dbg_log('-get_moonwalk:'+ '\n')
    dbg_log('- url:'+  url + '\n')    
    dbg_log('- ref:'+  ref + '\n') 

    
    manifest_links, subtitles, season, episode = moonwalk.get_playlist(url)
#     values, attrs = moonwalk.get_access_attrs(http, url)
#     print values
#     print attrs
#     print manifest_links
    
    r0 = [str(key) for key in manifest_links.keys()]
    dbg_log('- r0:'+  str(r0) + '\n')
    i = xbmcgui.Dialog().select('Video Quality', r0)

    return manifest_links[int(r0[i])]


def HD7_play(url, cook, name, web, ref):
    dbg_log('-HD7_play:'+ '\n')
    dbg_log('- url:'+  url.replace('&amp;', '&') + '\n')
    url = url.replace('&amp;', '&')
    furls = []

    if cook : cookies = json.loads(cook)
    else: cookies = None
    
    if 'kinolot.com' in web:
        req = req_url(url, cookies = cookies)
        http = req.content
        files = re.compile('file=(.*?)&').findall(http)
        if len(files):
            furls.append(Decode2(Decode2(urllib.unquote_plus(files[0]))))
    elif 'hdgo.cc' in web:
#        furl = get_YTD(url)
        furl = get_hdgo(url, ref, cookies)
        if furl != None: furls.extend(furl)
        else:  dbg_log('HDGO : no url returned')
    elif 'vk.com' in web:
#        furl = get_YTD(url)
        furl = get_VK(url)
        if furl != None: furls.append(furl)
        else:  dbg_log('VK : no url returned')
    elif 'vkontakte.ru' in web:
        furl = get_YTD(url)
        if furl != None: furls.append(furl)
        else:  dbg_log('VK : no url returned')
    elif 'mail.ru' in web:
        quals = get_mailru(url)
        try:        
          for d in quals: 
            if d['quality'] == 'HD' : 
                furls.append(d['url'])
                break
            if d['quality'] == '1080p' : 
                furls.append(d['url'])
                break
            if d['quality'] == 'SD' : 
                furls.append(d['url'])
                break
        except: pass
    elif 'moonwalk.c' in web or web[0].isdigit():
        furl = get_moonwalk(url.replace('.co','.cc'), ref)
        if furl != None: furls.append(furl)
        else:  dbg_log('Moonwalk : no url returned')
    
    if len(furls) == 0:
        furl = get_YTD(url)
        if furl != None: furls.append(furl)
        else:  dbg_log('OTHER : no url returned')        
        
    if len(furls) == 1:
        dbg_log('- furl:'+  furls[0] + '\n')
        item = xbmcgui.ListItem(path = furls[0])
        xbmcplugin.setResolvedUrl(pluginhandle, True, item)
    elif len(furls):
        sPlayList   = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 
        sPlayer     = xbmc.Player()
        sPlayList.clear()
        runRes = False
        for furl in furls:
            item = xbmcgui.ListItem(name, path = furl)
            item.setProperty('mimetype', 'video/x-msvideo')
            item.setProperty('IsPlayable', 'true')
            sPlayList.add(furl, item) #, 0) 
            if not runRes: 
                xbmcplugin.setResolvedUrl(pluginhandle, True, item)
                runRes = True
        sPlayer.play(sPlayList)
         

def HD7_ctlg(url, cook):
    dbg_log('-HD7_ctlg:' + '\n')
    dbg_log('- url:'+  url + '\n')

    catalog =  [("filmy/boevik/", "Боевик"),
                ("filmy/triller/", "Триллер"),
                ("filmy/priklyucheniya/", "Приключения"),
                ("filmy/fantastika/", "Фантастика"),
                ("filmy/fentezi/", "Фэнтези"),
                ("filmy/detektiv/", "Детектив"),
                ("filmy/komediya/", "Комедия"),
                ("filmy/drama/", "Драма"),
                ("filmy/melodrama/", "Мелодрама"),
                ("filmy/uzhasy/", "Ужасы"),
                ("filmy/semeynyy/", "Семейный"),
                ("filmy/voennyy/", "Военный"),
                ("filmy/istoricheskiy/", "Исторический"),
                ("filmy/muzykalnyy/", "Музыкальный"),
                ("treylery/", "Трейлер"),
                ("serialy/", "Сериалы"),
                ("multfilmy/", "Мультфильмы"),
                ("anime-multfilmy/", "Аниме"),
                ("dokumentalnyy/", "Документальные"),
                ("russkie-serialy/", "Русские сериалы")]
               
    for ctLink, ctTitle  in catalog:
        item = xbmcgui.ListItem(ctTitle)
        uri = sys.argv[0] \
        + '?url=' + urllib.quote_plus(start_pg + ctLink) + '&cook=' + urllib.quote_plus(cook)
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)  
        dbg_log('- uri:'+  uri + '\n')
        
    xbmcplugin.endOfDirectory(pluginhandle)

def uni2cp(ustr):
    raw = ''
    uni = unicode(ustr, 'utf8')
    uni_sz = len(uni)
    for i in range(uni_sz):
        raw += ('%%%02X') % ord(uni[i].encode('cp1251'))
    return raw  

def HD7_find(cook):     
    dbg_log('-HD7_find:'+ '\n')
    dbg_log('- cook:'+  cook + '\n')      
    
    kbd = xbmc.Keyboard()
    kbd.setHeading('ПОИСК')
    kbd.doModal()
    if kbd.isConfirmed():
        stxt = uni2cp(kbd.getText())
        furl = find_pg + stxt
        dbg_log('- furl:'+  furl + '\n')
        HD7_start(furl, '1', cook)

def get_params():
    param=[]
    #print sys.argv[2]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

params=get_params()


cook = ''
mode=''
url=''
ordr='0'
dir='0'
off='0'
gnrs=''
imag=''
name=''
web = ''
ref = ''
type = ''

try:
    mode=params['mode']
    dbg_log('-MODE:'+ mode + '\n')
except: pass
try: 
    url=urllib.unquote_plus(params['url'])
    dbg_log('-URL:'+ url + '\n')
except: pass  
try: 
    page=urllib.unquote_plus(params['page'])
    dbg_log('-PAGE:'+ page + '\n')
except: page = '0'
try: 
    imag=urllib.unquote_plus(params['img'])
    dbg_log('-IMaG:'+ imag + '\n')
except: pass 
try: 
    name=urllib.unquote_plus(params['name'])
    dbg_log('-NAME:'+ name + '\n')
except: pass 
try: 
    cook=urllib.unquote_plus(params['cook'])
    dbg_log('-COOK:'+ cook + '\n')
except: pass
try: 
    web=urllib.unquote_plus(params['web'])
    dbg_log('-WEB:'+ web + '\n')
except: pass
try: 
    ref=urllib.unquote_plus(params['ref'])
    dbg_log('-REF:'+ ref + '\n')
except: pass

keyword = params['keyword'] if 'keyword' in params else None
unified = params['unified'] if 'unified' in params else None
usearch = params['usearch'] if 'usearch' in params else None
if unified: type = 'unis'
if usearch: type = 'unds'

if url=='':
    url = start_pg

if mode == '': HD7_start(url, page, cook)
elif mode == 'ctlg': HD7_ctlg(url, cook)
elif mode == 'view': HD7_view(url, imag, name, cook)
elif mode == 'play': HD7_play(url, cook, name, web, ref)
elif mode == 'find': HD7_find(cook)
elif mode == 'show': HD7_view(url, imag, "Play Video", cook)
elif mode == 'search': 
    url = find_pg + uni2cp(gettranslit(urllib.unquote_plus(keyword)))
    HD7_start(url, '1', type)



