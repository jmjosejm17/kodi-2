# -*- coding: utf-8 -*-
#!/usr/bin/python
# Writer (c) 2012, Silhouette, E-mail: otaranda@hotmail.com
# Rev. 0.1.1


import urllib,urllib2,re,sys,os,time,random
import xbmcplugin,xbmcgui,xbmcaddon

dbg = 0
dbg_gd = 0

pluginhandle = int(sys.argv[1])

start_pg = "http://sonet.by/video/"
main_pg = "#page:0"
list_pg = "#page:1"
find_pg = "#page:3"

__settings__ = xbmcaddon.Addon(id='plugin.video.sonet.by')
usr_log = __settings__.getSetting('usr_log')
usr_pwd = __settings__.getSetting('usr_pwd')


def dbg_log(line):
    if dbg: print line
    
def raw2uni(raw):
    unis = u''
    raw_sz = len(raw)
    i = 0
    while  i < raw_sz:
        if i < (raw_sz - 6) and raw[i] == '\\' and raw[i + 1]=='u':
            unis += unichr(int(raw[i + 2] + raw[i + 3] + raw[i + 4] + raw[i + 5], 16))
            i += 6
        else:
            unis += raw[i]
            i += 1
    return unis
                        
    
def get_url(url, data = None, cookie = None, save_cookie = False, referrer = None):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.7.62 Version/11.00')
    req.add_header('Accept', 'text/html, application/xml, application/xhtml+xml, */*')
    req.add_header('Accept-Language', 'ru,en;q=0.9')
    if cookie: req.add_header('Cookie', cookie)
    if referrer: req.add_header('Referer', referrer)
    if data: 
        response = urllib2.urlopen(req, data)
    else:
        response = urllib2.urlopen(req)
    link=response.read()
    if save_cookie:
        setcookie = response.info().get('Set-Cookie', None)
        if setcookie:
            setcookie = re.search('([^=]+=[^=;]+)', setcookie).group(1)
            link = link + '<cookie>' + setcookie + '</cookie>'
    
    response.close()
    return link

def SNB_mnpg(url):
    dbg_log('-SNB_mnpg:' + '\n')
    ext_ls = [('ПОИСК', find_pg, '?mode=fdpg'),\
             ('КАТАЛОГ', list_pg, '?mode=lspg')]


    http = get_url(url, save_cookie = True)
    mycookie = re.search('<cookie>(.+?)</cookie>', http).group(1)
    http = get_url(url, data = "logon=1&login=" + usr_log + "&pass=" + usr_pwd, cookie = mycookie)
    oneline = re.sub( '\n', ' ', http)
    fm_ls = re.compile("<td class='FilmTD'(.*?)\s+<a title='(.*?)' href='#(.*?)'>\s+<img width='(.*?)px' height='(.*?)px' src='(.*?)' border='(.*?)'").findall(oneline)

    if len(fm_ls):
		    
        for ctTitle, ctLink, ctMode  in ext_ls:
            item = xbmcgui.ListItem(ctTitle)
            uri = sys.argv[0] + ctMode \
            + '&url=' + urllib.quote_plus(url + find_pg) + '&cook=' + urllib.quote_plus(mycookie)
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)  
            dbg_log('- uri:'+  uri + '\n')

        for tr, title, href, iw, ih, logo, ib in fm_ls:
            #print href + logo + title
            item = xbmcgui.ListItem(title, iconImage=url + logo, thumbnailImage=url + logo)
            uri = sys.argv[0] + '?mode=plpg' \
            + '&url=' + urllib.quote_plus(href) + '&logo=' + urllib.quote_plus(url + logo) + \
            '&rfr=' + urllib.quote_plus(url) +'&cook=' + urllib.quote_plus(mycookie)
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)  
            dbg_log('- uri:'+  uri + '\n')
 
    xbmcplugin.endOfDirectory(pluginhandle) 
    
def SNB_plpg(url, logo, cook, rfr):     
    dbg_log('-SNB_plpg:'+ '\n')
    fval = url.split(':')
    furl = start_pg + 'actions.php?action=getfilm&' + fval[0] + '=' + fval[1] + '&PHPSESSID=' + cook
    #actions.php?action=getfilm&film=4822&PHPSESSID=377bb3ff4ffebc07ec2570f94e840cb7&JsHttpRequest=133226256496112-xml

    http = get_url(furl, cookie = cook, referrer = rfr)
    files = re.compile('"files":\[\{(.*?)\}\]').findall(http)
    infos = re.compile('"Description":"(.*?)"').findall(http)

    if len(files):
        links = re.compile('"ftp":"(.*?)"').findall(files[0])
        titles = re.compile('"Name":"(.*?)"').findall(files[0])
        n_titles = len(titles)
        
        for i in range(len(links)):
            descr = u''
            if( i < n_titles):
                descr = raw2uni(titles[i])
            else:
                descr = str(i + 1)
                
            newlnk = re.sub('\\\/','/',links[i])
 
            item = xbmcgui.ListItem(descr, iconImage=logo)
            uri = sys.argv[0] + '?mode=play' + \
            '&url=' + urllib.quote_plus(newlnk) + '&logo=' + urllib.quote_plus(logo) + '&cook=' + urllib.quote_plus(cook)
    
            title = descr
            thumbnail = logo
            if len(infos): plot = raw2uni(infos[0])
            else: plot = descr
    
            item.setInfo( type='video', infoLabels={'title': title, 'plot': plot})
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(pluginhandle,uri,item)
            dbg_log('- uri:'+  uri + '\n')
           
    xbmcplugin.endOfDirectory(pluginhandle)

def SNB_play(url, logo, cook):     
    dbg_log('-SNB_play:'+ '\n')
    #url='http://sonet.by/get/syrovatko/2011.12.03-2016.%20%EA%EE%ED%E5%F6%20%ED%EE%F7%E8%20%28hell%29%20%28%EF%F0%EE%EC%EE%29.2011.avi'
    item = xbmcgui.ListItem(path = url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)
           
          
def lsChan():
    xbmcplugin.endOfDirectory(pluginhandle)

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
rfr = ''
lspg = ''
fdpg = ''
mode=''
logo=''
url=''

try:
    mode=params['mode']
    dbg_log('-MODE:'+ mode + '\n')
except: pass
try: 
    cook=urllib.unquote_plus(params['cook'])
    dbg_log('-COOK:'+ cook + '\n')
except: pass
try: 
    rfr=urllib.unquote_plus(params['rfr'])
    dbg_log('-RFR:'+ rfr + '\n')
except: pass
try: 
    lspg=urllib.unquote_plus(params['lspg'])
    dbg_log('-LSPG:'+ lspg + '\n')
except: pass
try: 
    fdpg=urllib.unquote_plus(params['fdpg'])
    dbg_log('-FDPG:'+ fdpg + '\n')
except: pass
try: 
    logo=urllib.unquote_plus(params['logo'])
    dbg_log('-LOGO:'+ logo + '\n')
except: pass    
try: 
    url=urllib.unquote_plus(params['url'])
    dbg_log('-URL:'+ url + '\n')
except: pass  

if mode == 'fdpg': lsChan() #SNB_fdpg(start_pg, cook)
elif mode == 'lspg': lsChan() #SNB_lspg(start_pg, cook)
elif mode == 'plpg': SNB_plpg(url, logo, cook, rfr)
elif mode == 'play': SNB_play(url, logo, cook)
elif mode == '': SNB_mnpg(start_pg)

