# -*- coding: utf-8 -*-
# Module: default
# Author: rywko
# Created on: 15.11.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys, os
from collections import OrderedDict
from urllib import urlencode
import urllib2
from urlparse import parse_qsl
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re
import resolver

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon_ = xbmcaddon.Addon('plugin.video.tvba.sk')
_scriptname_ = _addon_.getAddonInfo('name')
home = _addon_.getAddonInfo('path')
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'


FEEDS = OrderedDict([
        ('Najnovšie','http://www.tvba.sk/cely-archiv/podla-datumu/'),
        ('Pravidelné programy','http://www.tvba.sk/relacie/'),
        ('Ostatné relácie a videá','http://www.tvba.sk/cely-archiv/ostatne-relacie-a-videa/'),  
        ])

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(_scriptname_,msg.__str__()), level)

def logN(msg):
    log(msg,level=xbmc.LOGNOTICE)

def fetchUrl(url, label, ref=''):
    logN("fetchUrl " + url + ", label:" + label)
    httpdata = ''	
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
    if ref!='':
       req.add_header('Referer', ref)
    resp = urllib2.urlopen(req)
    httpdata = resp.read()
    resp.close()
    return httpdata


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    xbmcplugin.setContent(_handle, 'videos')

    for category in FEEDS.iterkeys():
        list_item = xbmcgui.ListItem(label=category)
        url = get_url(action='listing', url=FEEDS[category])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        logN("category " + category + " added")
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    
    xbmcplugin.endOfDirectory(_handle)

def list_videos(url):
    """
    Create the list of playable videos in the Kodi interface.

    :param url: Url to video directory
    :type url: str
    """
    path=url
    httpdata = fetchUrl(path, "Loading categories...")
    #handle shows
    for item in re.findall(r'<div class="segment_cat_img_height_cutter">(.*?)<\/div>\s*<\/div>\s*<\/div>', httpdata, re.DOTALL):
        url=re.search(r'<a href="(\S+?)">',item).group(1)
        thumb = re.search(r'src="(\S+?)"',item).group(1)
        title = re.search(r'alt="(.+?)"',item).group(1)
        plot = re.search(r'<div class="prod_description segment_cat_desc_div">(.*)',item).group(1).strip()
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': plot,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        list_item.setProperty('IsPlayable', 'false')       
        url = get_url(action='listing', url=url)
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
 
    #handle episodes
    for item in re.findall(r'<div class="article_holder article_holder_4c(.*?)</span></div>', httpdata, re.DOTALL):
        url=re.search(r'<a href="(\S+?)"',item).group(1)
        thumb=re.search(r'src="(\S*?)"',item)
        thumb = thumb.group(1) if thumb else ''
        title = re.search(r'<span class="packed_article_title">(.*?)<\/span>',item).group(1)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': title,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        list_item.setProperty('IsPlayable', 'true')    
        url = get_url(action='play', video=url)
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    next=re.search(r'"next_prev_page_nums_act".*?document\.location\.href=\'(.+?)\'',httpdata)
    if next:
        path=path.split('?')[0]
        url = get_url(action='listing', url=path+next.group(1))
        xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label='Ďalšie'), True)    
    
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # get video link
    html = fetchUrl(path, "Loading video...")
    if html:
        url = re.search(r'src="(https:\/\/video\.onnetwork\.tv\S+?)"><\/script>',html)
        if url:
            url=url.group(1)
            html = fetchUrl(url, "Loading video...")
            videoID=re.search(r' videoID:(\d+)"',html).group(1)
            url=re.search(r'frameSrc : "(\S+?)"', html).group(1)
            html = fetchUrl(url, "Loading video...",path)
            url=re.search(r'id : '+videoID+r',.*?],url:"(\S*3u8)',html).group(1)
            #choose highest quality
            httpdata = fetchUrl(url, "Loading playlist...")
            streams = re.compile('RESOLUTION=\d+x(\d+).*\n([^#].+)').findall(httpdata) 
            streams.sort(key=lambda x: int(x[0]),reverse=True)
            videolink=url.rsplit('/', 1)[0] + '/' +  streams[0][1]
        else:
            resolved = resolver.findstreams(html,['src="(?P<url>https:\/\/www.youtube.com\/\S+?)"'])
            if not resolved:
                xbmcgui.Dialog().ok('Chyba', 'Video nie je dostupné', '', '')
                return False
            videolink=resolved[0]['url']
        logN("Playing video " + videolink)
        play_item = xbmcgui.ListItem(path=videolink)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
     

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos
            list_videos(params['url'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
