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

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon_ = xbmcaddon.Addon('plugin.video.tvba.sk')
_scriptname_ = _addon_.getAddonInfo('name')
home = _addon_.getAddonInfo('path')
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'


FEEDS = OrderedDict([
        ('Relácie','http://www.tvba.sk/relacie/'),   
        ])

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(_scriptname_,msg.__str__()), level)

def logDbg(msg):
    log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg,level=xbmc.LOGERROR)

def fetchUrl(url, label, ref=''):
    logErr("fetchUrl " + url + ", label:" + label)
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
      
        url = get_url(action='listing', category=category)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        logErr("category " + category + " added")
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    
    xbmcplugin.endOfDirectory(_handle)

def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    if 'tvba.sk' not in category:
        path=FEEDS[category]
    else:
        path=category
    httpdata = fetchUrl(path, "Loading categories...")
    #handle shows
    for item in re.findall(r'<div class="segment_cat_img_height_cutter">(.*?)<\/div>\s*<\/div>\s*<\/div>', httpdata, re.DOTALL):
        url=re.search(r'<a href="(\S+?)">',item).group(1)
        thumb = re.search(r'src="(\S+?)"',item).group(1)
        title = re.search(r'alt="(.+?)"',item).group(1)
        plot = re.search(r'<div class="prod_description segment_cat_desc_div">(.*)',item).group(1)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': plot.strip(),
                                    'mediatype': 'video'})
                                    
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})

        list_item.setProperty('IsPlayable', 'false')
        
        url='plugin://plugin.video.tvba.sk/?action=listing&category=' +url
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = True

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    #handle episodes
    for item in re.findall(r'<div class="article_holder article_holder_4c(.*?)</span></div>', httpdata, re.DOTALL):
        url=re.search(r'<a href="(\S+?)">',item).group(1)
        thumb = re.search(r'src="(\S+?)"',item).group(1)
        title = re.search(r'<span class="packed_article_title">(.*?)<\/span>',item).group(1)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': '',
                                    'mediatype': 'video'})
                                    
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})

        list_item.setProperty('IsPlayable', 'true')
        
        url='plugin://plugin.video.tvba.sk/?action=play&video=' +url
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    next=re.search(r'"next_prev_page_nums_act".*?document\.location\.href=\'(.+?)\'',httpdata)
    if next:
        url = get_url(action='listing', category=path+next.group(1))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label='Ďalšie'), is_folder)    
    
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
        url = re.search(r'src="(https:\/\/video\.onnetwork\.tv\S+?)"><\/script>',html).group(1)
        html = fetchUrl(url, "Loading video...")
        videoID=re.search(r'"SID videoID:(\d+)"',html).group(1)
        url=re.search(r'frameSrc : "(\S+?),', html).group(1)
        html = fetchUrl(url, "Loading video...",path)
        videolink=re.search(r'id : '+videoID+r',.*?],url:"(\S*3u8)',html).group(1)
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
            # Display the list of videos in a provided category.
            list_videos(params['category'])
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
