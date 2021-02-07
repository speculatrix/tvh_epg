#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
a really really basic EPG for TVHeadend

Main information:
    https://github.com/speculatrix/tvh_epg

Chromecast information:
    https://github.com/speculatrix/tvh_epg/blob/master/CHROMECAST.md

    note that not only do you need to download pychromecast from
        https://github.com/balloob/pychromecast
    and put it into a subdirectory alongside this cgi-bin, but you
    need to pip install zeroconf to get it to work.
'''

import cgi
import cgitb
import codecs
import configparser
import datetime
import hashlib
import json
import os
import stat
import sys
import time

import collections
import socket
import urllib
import requests

# chromecast support is optional, and since it needs manually installing
# have to not die if it can't be found
try:
    import pychromecast
    CAST_SUPPORT = True
except ImportError:
    CAST_SUPPORT = False


# pylint:disable=global-statement

# requires making code less readable:
# pylint:disable=too-many-branches
# pylint:disable=too-many-lines
# pylint:disable=too-many-locals
# pylint:disable=too-many-nested-blocks
# pylint:disable=too-many-statements
# broken in pylint3:
# pylint:disable=global-variable-not-assigned

##########################################################################################

URL_GITHUB_HASH_SELF = 'https://api.github.com/repos/speculatrix/tvh_epg/contents/tvh_epg.py'

TS_URL_CHN = 'api/channel/grid'
TS_URL_CTG = 'api/channeltag/grid'
TS_URL_CBE = 'api/dvr/entry/create_by_event'
TS_URL_DCG = 'api/dvr/config/grid'
TS_URL_DEG = 'api/dvr/entry/grid_finished'
TS_URL_EPG = 'api/epg/events/grid'

TS_URL_STC = 'api/status/connections'
TS_URL_STI = 'api/status/inputs'
TS_URL_SVI = 'api/serverinfo'

TS_URL_STR = 'stream/channel'

TS_URL_DVF = 'dvrfile/'

CGI_PARAMS = cgi.FieldStorage()

EPG = 'epg'

SECS_P_PIXEL = 10  # how many seconds per pixel

MAX_FUTURE = 9000  # 2.5 hours - how far into the future to show a prog

INPUT_FORM_ESCAPE_TABLE = {
    '"': "&quot;",
    "'": "&apos;",
}

URL_ESCAPE_TABLE = {
    " ": "%20",
}

TD_EMPTY_CELL = '<td>&nbsp;</td>'

# state files, queues, logs and so on are stored in this directory
CONTROL_DIR = '/var/lib/tvh_epg'

# the settings file is stored in the control directory
SETTINGS_FILE = 'tvh_epg_settings.ini'
SETTINGS_SECTION = 'user'

TS_URL = 'ts_url'
TS_URL_ICONS = 'ts_url_icons'
TS_URL_CAST = 'ts_url_icon_cast'
TS_USER = 'ts_user'
TS_PASS = 'ts_pass'
TS_PAUTH = 'ts_pauth'
SH_LOGO = 'sh_ch_logo'
MAX_CHANS = 'max_chans'
TITLE = 'title'
DFLT = 'default'
TYPE = 'type'
ICON_WIDTH = 'forced_icon_width'
ICON_HEIGHT = 'forced_icon_height'

# default values of the settings when being created
SETTINGS_DEFAULTS = {
    TS_URL: {
        TITLE: 'URL of TV Headend Server',
        DFLT: 'http://tvh.example.com:9981',
        TYPE: 'text',
    },
    TS_URL_ICONS: {
        TITLE: 'URL to picons',
        DFLT: 'http://tvh.eample.com/TVLogos/',
        TYPE: 'text',
    },
    TS_URL_CAST: {
        TITLE: 'URL to chromecast icon',
        DFLT: 'http://tvh.eample.com/ic_cast_connected_white_24dp.png',
        TYPE: 'text',
    },
    TS_USER: {
        TITLE: 'Username on TVH server',
        DFLT: TS_USER,
        TYPE: 'text',
    },
    TS_PASS: {
        TITLE: 'Password on TVH server',
        DFLT: TS_PASS,
        TYPE: 'password',
    },
    TS_PAUTH: {
        TITLE: 'Persistent Auth Token',
        DFLT: TS_PAUTH,
        TYPE: 'password',
    },
    SH_LOGO: {
        TITLE: 'Show Channel Logos',
        DFLT: '0',
        TYPE: 'number',
    },
    MAX_CHANS: {
        TITLE: 'Maximum Number Of Channels',
        DFLT: '500',
        TYPE: 'number',
    },
    ICON_HEIGHT: {
        TITLE: 'Force icon height to this, 0 for off',
        DFLT: '64',
        TYPE: 'text',
    },
    ICON_WIDTH: {
        TITLE: 'Force icon width to this, 0 for off',
        DFLT: '80',
        TYPE: 'text',
    },
}

DOCROOT_DEFAULT = '/home/hts'


##########################################################################################
def check_load_config_file():
# pylint:disable=too-many-return-statements
    '''check there's a config file which is writable;
       returns 0 if OK, -1 if the rest of the page should be aborted,
       > 0 to trigger rendering of the settings page'''

    global CONFIG_FILE_NAME
    global MY_SETTINGS

    # who am i?
    my_euser_id = os.geteuid()
    my_egroup_id = os.getegid()

    config_bad = 1

    ################################################
    # verify that CONTROL_DIR exists and is writable
    try:
        cdir_stat = os.stat(CONTROL_DIR)
    except OSError:
        error_text = '''Error, directory "%s" doesn\'t appear to exist.
Please do the following - needs root:
\tsudo mkdir "%s" && sudo chgrp %s "%s" && sudo chmod g+ws "%s"''' \
% (CONTROL_DIR, CONTROL_DIR, str(my_egroup_id), CONTROL_DIR, CONTROL_DIR)
        config_bad = -1
        return (config_bad,
                error_text)  # error so severe, no point in continuing

    # owned by me and writable by me, or same group as me and writable through that group?
    if ((cdir_stat.st_uid == my_euser_id and
         (cdir_stat.st_mode & stat.S_IWUSR) != 0)
            or (cdir_stat.st_gid == my_egroup_id and
                (cdir_stat.st_mode & stat.S_IWGRP) != 0)):
        #print 'OK, %s exists and is writable' % CONTROL_DIR
        config_bad = 0
    else:
        error_text = '''Error, won\'t be able to write to directory "%s".
Please do the following:
\tsudo chgrp %s "%s" && sudo chmod g+ws "%s"''' \
% (CONTROL_DIR, str(my_egroup_id), CONTROL_DIR, CONTROL_DIR, )
        return (-1, error_text)  # error so severe, no point in continuing

    ########
    # verify the settings file exists and is writable
    if not os.path.isfile(CONFIG_FILE_NAME):
        error_text = '''Error, can\'t open "%s" for reading.
Please do the following - needs root:
\tsudo touch "%s" && sudo chgrp %s "%s" && sudo chmod g+w "%s"''' \
% (CONFIG_FILE_NAME, CONFIG_FILE_NAME, str(my_egroup_id), CONFIG_FILE_NAME, CONFIG_FILE_NAME)
        return (-1, error_text)

    # owned by me and writable by me, or same group as me and writable through that group?
    config_stat = os.stat(CONFIG_FILE_NAME)
    if ((config_stat.st_uid == my_euser_id and
         (config_stat.st_mode & stat.S_IWUSR) != 0)
            or (config_stat.st_gid == my_egroup_id and
                (config_stat.st_mode & stat.S_IWGRP) != 0)):
        config_bad = 0
    else:
        error_text = '''Error, won\'t be able to write to file "%s"
Please do the following - needs root:
\tsudo chgrp %s "%s" && sudo chmod g+w %s''' \
% (CONFIG_FILE_NAME, CONFIG_FILE_NAME, my_egroup_id, CONFIG_FILE_NAME, )
        return (-1, error_text)

    # file is zero bytes?
    if config_stat.st_size == 0:
        error_text = 'Config file is empty, please go to settings and submit to save\n'
        return (1, error_text)

    if not MY_SETTINGS.read(CONFIG_FILE_NAME):
        error_text = ('<b>Error</b>, failed to open and read config file "%s"' \
                      % (CONFIG_FILE_NAME, ))
        return (-1, error_text)

    return (0, 'OK')


##########################################################################################
def get_github_hash_self():
    """calculates the git hash of the version of this script in github"""

    gh_resp = requests.get(URL_GITHUB_HASH_SELF)
    gh_json = gh_resp.json()

    return gh_json['sha']


##########################################################################################
def get_githash_self():
    """calculates the git hash of the running script"""

    # stat this file
    fullfile_name = __file__
    fullfile_stat = os.stat(fullfile_name)

    # read this entire file into memory
    fullfile_content = ''
    with open(fullfile_name, 'rb') as fullfile_fh:
        fullfile_content = fullfile_fh.read()

    # do what "git hash-object" does
    sha_obj = hashlib.sha1()
    sha_obj.update(b'blob %d\0' % fullfile_stat.st_size)
    sha_obj.update(fullfile_content)

    return sha_obj.hexdigest()


##########################################################################################
def epoch_to_human_duration(epoch_time):
    '''takes numeric sec since unix epoch and returns humanly readable time'''

    #return time.asctime(time.localtime(epoch_time))

    human_dt = datetime.datetime.fromtimestamp(epoch_time)
    return human_dt.strftime("%H:%M")


##########################################################################################
def epoch_to_human_date(epoch_time):
    '''takes numeric sec since unix epoch and returns humanly readable time'''

    #return time.asctime(time.localtime(epoch_time))

    human_dt = datetime.datetime.fromtimestamp(epoch_time)
    return human_dt.strftime("%d-%m-%Y %H:%M")


##########################################################################################
#def load_channel_dict_from_cache():
#    '''load channel dict from cache file - FIXME'''
#

##########################################################################################
#def save_channel_dict_to_cache():
#    '''saves channel dict to cache file - FIXME'''
#


##########################################################################################
def get_channeltag_grid():
    '''gets the channeltag/grid values'''

    global MY_SETTINGS

    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_CTG,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    print('<!-- get_channeltag_grid URL %s -->' % (ts_query, ))
    if ts_response.status_code != 200:
        print('<pre>Error code %d\n%s</pre>' % (ts_response.status_code, ts_response.content, ))
        return {}

    ts_json = json.loads(ts_response.text, strict=False)
    #print('<pre>%s</pre>' % json.dumps(ts_json, sort_keys=True, \
    #                                   indent=4, separators=(',', ': ')) )

    return ts_json


##########################################################################################
def get_channel_dict():
    '''gets the channel listing and generats an ordered dict by name'''

    global MY_SETTINGS

    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_max_ch = MY_SETTINGS.get(SETTINGS_SECTION, MAX_CHANS)
    ts_query = '%s/%s?limit=%s' % (
        ts_url,
        TS_URL_CHN,
        ts_max_ch,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    print('<!-- get_channel_dict URL %s -->' % (ts_query, ))
    if ts_response.status_code != 200:
        print('<pre>Error code %d\n%s</pre>' % (ts_response.status_code, ts_response.content, ))
        return {}

    ts_text = ts_response.text
    #print('<pre>Extreme Debug!\n\n%s\n<pre>' % (ts_text,))
    ts_json = json.loads(ts_text, strict=False)
    #print('<pre>%s</pre>' % json.dumps(ts_json, sort_keys=True, \
    #                                   indent=4, separators=(',', ': ')) )

    channel_map = {}  # full channel info
    channel_list = []  # build a list of channel names
    ordered_channel_map = collections.OrderedDict()
    if 'entries' in ts_json:

        # grab all channel info
        name_unknown = 0
        number_unknown = -1
        for entry in ts_json['entries']:
            # start building a dict with channel name as key
            if 'name' in entry:
                channel_name = entry['name']
            else:
                channel_name = 'unknown ' + str(name_unknown)
                name_unknown += 1

            channel_list.append(channel_name)
            if channel_name not in channel_map:
                channel_map[channel_name] = {}

            # store the channel specific info
            ch_map = channel_map[channel_name]

            if 'tags' in entry:
                ch_map['tags'] = entry['tags']

            if 'number' in entry:
                ch_map['number'] = entry['number']
            else:
                ch_map['number'] = number_unknown
                name_unknown -= 1

            ch_map['uuid'] = entry['uuid']
            if 'icon_public_url' in entry:
                ch_map['icon_public_url'] = entry['icon_public_url']

        channel_list_sorted = sorted(channel_list, key=lambda s: s.casefold())

        # case insensitive sort of channel list
        for chan in channel_list_sorted:
            # ... produces an ordered dict
            #print('adding %s<br />' % (chan, ))
            ordered_channel_map[chan] = channel_map[chan]

    return ordered_channel_map


##########################################################################################
def get_dvr_config_grid():
    '''gets the dvr/config/grid dict'''

    global MY_SETTINGS

    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_DCG,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    print('<!-- get_dvr_config_grid URL %s -->' % (ts_query, ))
    ts_json = json.loads(ts_response.text, strict=False)

    #print('<pre>%s</pre>' % json.dumps(ts_json, sort_keys=True, \
    #                                   indent=4, separators=(',', ': ')) )

    return ts_json


##########################################################################################
def html_page_footer():
    '''no surprises'''

    print('''</body>
</html>''')


##########################################################################################
def input_form_escape(text):
    """escape special characters into html input forms"""
    return "".join(INPUT_FORM_ESCAPE_TABLE.get(c, c) for c in text)


##########################################################################################
def page_channels():
    '''prints the channel list to stdout'''

    global MY_SETTINGS

    if 'tag' in CGI_PARAMS:
        p_tag = CGI_PARAMS.getlist('tag')
    else:
        p_tag = []

    print('<h1>Channels</h1>')

    channel_dict = get_channel_dict()
    channel_tag = get_channeltag_grid()

    cdl = len(channel_dict)
    print('''<p><b>Channel count: %d</b></p>
<p>Maximum number of channels viewable %s</p>
<p>Note, the links are the streams, open in VLC
- you can drag and drop the link into a VLC window</p>''' \
% (cdl, MY_SETTINGS.get(SETTINGS_SECTION, MAX_CHANS)
  ))

    # channel labels
    if cdl:
        print('  <form method="get" action="">')
        print("<b>Tag filters</b>:")
        for tag in channel_tag['entries']:
            if tag['uuid'] in p_tag:
                checked = ' checked'
            else:
                checked = ''
            print(
                '<input type="checkbox" name="tag" value="%s" %s/>%s&nbsp;&nbsp;'
                % (
                    tag['uuid'],
                    checked,
                    tag['name'],
                ))
        print('''    <input type="hidden" name="page" value="channels" />
    <input type="submit" name="apply" value="apply" />
  </form>''')


        #####################################################################
        # channel table

        print('''  <table>
    <tr>''')
        if int(MY_SETTINGS.get(SETTINGS_SECTION, SH_LOGO)) != 0:
            print('      <th>Channel Logo</th>')
        print('''       <th>Channel Name</th>
      <th>Channel Number</th>
    </tr>
''')
        #ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
        icon_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL_ICONS)
        icon_width = MY_SETTINGS.get(SETTINGS_SECTION, ICON_WIDTH)
        icon_height = MY_SETTINGS.get(SETTINGS_SECTION, ICON_HEIGHT)
        for chan_name in channel_dict:
            chan = channel_dict[chan_name]
            show_channel = 0
            if 'tags' not in chan or len(p_tag) == 0:
                show_channel = 1
            else:
                for tag in p_tag:
                    if tag in chan['tags']:
                        show_channel = 1

            if show_channel:
                print('    <tr>')
                if int(MY_SETTINGS.get(SETTINGS_SECTION, SH_LOGO)) != 0:
                    if 'icon_public_url' in channel_dict[chan_name]:
                        # chop +1 channel names for icons
                        if chan_name[-2:] == '+1':
                            chan_name_ref = chan_name[:-2]
                        else:
                            chan_name_ref = chan_name
                        chan_img_url = '%s/%s.png' % (icon_url, chan_name_ref, )
                        print('<td width="100px" align="right" class="chan_icon">'
                              '<img src="%s"' % (chan_img_url, ), end='')
                        if icon_width != '' and icon_width != '0':
                            print(' width="%s"' % (icon_width, ), end='')
                        if icon_height != '' and icon_height != '0':
                            print(' height="%s"' % (icon_height, ), end='')
                        print(' /></td>')
                    else:
                        print('<td>&nbsp;</td>')

                play_url = '?page=m3u&amp;uuid=/%s/%s' % (TS_URL_STR, chan['uuid'], )
                print('<td><a href="%s" download="tvheadend.m3u">%s</a>' % (play_url, chan_name, ))
                if CAST_SUPPORT:
                    print('<br /><a href="?page=chromecast&uri=/%s/%s"><img src="%s" /></a>' % \
                          (TS_URL_STR,
                           chan['uuid'],
                           MY_SETTINGS.get(SETTINGS_SECTION, TS_URL_CAST),
                          ))

                print('</td>\n      <td>%s</td>\n        </tr>' % (chan['number'], ))

        print('</table>')


##########################################################################################
def page_chromecast(p_uri, p_cast_device):
    '''chromecast "pop up"
        uri is /dvrfile/aaaaaaa...
            or /stream/channel/aaaaaa
        and missing the httpX://hostname:port bit
    '''

    global MY_SETTINGS

    (chromecasts, browser) = pychromecast.get_chromecasts()
    if isinstance(chromecasts, tuple):
        chromecasts, browser = chromecasts
    browser.close()


    browser.close()


    # split the TVH server URL up so we can get its IP address
    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    try:
        ts_url_parsed = urllib.parse.urlparse(ts_url)
    except urllib.error.URLError as url_excpt:
        ##print(str(url_excpt))
        print('<p>Error parsing %s</p>' % (str(url_excpt), ))
        return

    print('<p>hostname %s, netloc %s</p>' % (ts_url_parsed.hostname, ts_url_parsed.netloc, ))


    print('<br /><br />Debug: uri "%s"<br />' % (p_uri, ))
    # now for abominable hacks
    ts_ip = socket.gethostbyname(ts_url_parsed.hostname)
    if TS_URL_DVF in p_uri:
        # recordings need to get a username/password
        full_url = '%s://%s:%s@%s:%s/%s?profile=chromecast' \
                   % (ts_url_parsed.scheme,
                      MY_SETTINGS.get(SETTINGS_SECTION, TS_USER),
                      MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS),
                      ts_ip,
                      ts_url_parsed.port,
                      p_uri,
                     )
    else:
        # live streams use persistent auth
        full_url = '%s://%s:%s%s?AUTH=%s&profile=chromecast' \
                   % (ts_url_parsed.scheme,
                      ts_ip, ts_url_parsed.port,
                      p_uri, MY_SETTINGS.get(SETTINGS_SECTION, TS_PAUTH),
                     )



    print('fullurl is "%s"<br />' % full_url)


    print("<p>Please be patient, scanning for chromecast devices can take up to ten seconds</p>")

    ####
    # user must choose a device to cast to
    if p_cast_device == '':
        print('<form method="get" action="">\n'
              '<input type="hidden" name="page" value="chromecast" />\n'
              '<input type="hidden" name="uri" value="%s" />' % (p_uri, ))
        print('Select device')
        print('<select name="cast_device">')

        for cast_dev in chromecasts:
            print('<option value="%s">%s</option>' % \
                  (cast_dev.device.friendly_name,
                   cast_dev.device.friendly_name,
                  ))
        print('''</select>
<input type="submit" name="Choose Device" value="Choose Device">
</form>''')
        return

    ####
    # find the cast device which user chose from friendly name
    print('<br />Debug, finding device with friendly name "%s"<br />' % (p_cast_device, ))
    cast = None
    for cast_dev in chromecasts:
        if cast_dev.device.friendly_name == p_cast_device:
            cast = cast_dev
    if cast is None:
        print('Error, couldn\'t find the cast device<br />')
        return

    ####
    # can now actually get the chromecast to do the streaming
    #return     # stop the actual casting
    cast.wait()
    print('<pre')
    print(cast.device)
    print(cast.status)

    c_m_c = cast.media_controller
    c_m_c.play_media(full_url, 'video/mp4')

    c_m_c.block_until_active()
    print(c_m_c.status)
    c_m_c.pause()
    time.sleep(5)
    c_m_c.play()
    print('</pre')
    print('<p>chromecast page completed</p>')


##########################################################################################
def page_epg():
    '''prints the EPG to stdout'''

    global MY_SETTINGS

    if 'tag' in CGI_PARAMS:
        p_tag = CGI_PARAMS.getlist('tag')
    else:
        p_tag = []

    print('<h1>EPG</h1>')

    epoch_time = time.time()

    channel_dict = get_channel_dict()
    channel_tag = get_channeltag_grid()
    cdl = len(channel_dict)
    if cdl:
        print('  <form method="get" action="">')
        print("<b>Tag filters</b>:")
        for tag in channel_tag['entries']:
            if tag['uuid'] in p_tag:
                checked = ' checked'
            else:
                checked = ''
            print(
                '<input type="checkbox" name="tag" value="%s" %s/>%s&nbsp;&nbsp;'
                % (
                    tag['uuid'],
                    checked,
                    tag['name'],
                ))
        print('''    <input type="hidden" name="page" value="epg" />
    <input type="submit" name="apply" value="apply" />
  </form>''')

        print('''<p><b>Channel count: %d</b></p>
<p>Maximum number of channels viewable %s</p>
<p>Note, the links are the streams, open in VLC
- you can drag and drop the link into a VLC window</p>''' \
% (cdl, MY_SETTINGS.get(SETTINGS_SECTION, MAX_CHANS)
  ))

        # get the EPG data for each channel
        print('''  <table width="1700px">
    <tr>''')
        if int(MY_SETTINGS.get(SETTINGS_SECTION, SH_LOGO)) != 0:
            print('      <th width="100px">Channel Logo</th>')
        print('''       <th>Channel Name</th>
      <th>Channel Number</th>
    </tr>
''')

        ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
        icon_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL_ICONS)
        ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
        ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
        icon_width = MY_SETTINGS.get(SETTINGS_SECTION, ICON_WIDTH)
        icon_height = MY_SETTINGS.get(SETTINGS_SECTION, ICON_HEIGHT)

        # iterate through the channel list by name
        for chan_name in channel_dict:
            chan = channel_dict[chan_name]
            show_channel = 0
            if 'tags' not in chan or len(p_tag) == 0:
                show_channel = 1
            else:
                for tag in p_tag:
                    if tag in chan['tags']:
                        show_channel = 1

            if show_channel:
                print('    <tr>')
                if int(MY_SETTINGS.get(SETTINGS_SECTION, SH_LOGO)) != 0:
                    if 'icon_public_url' in chan:
                        # chop +1 channel names for icons
                        if chan_name[-2:] == '+1':
                            chan_name_ref = chan_name[:-2]
                        else:
                            chan_name_ref = chan_name
                        chan_img_url = '%s/%s.png' % (icon_url, chan_name_ref, )
                        print('<td width="100px" align="right" class="chan_icon">'
                              '<img src="%s"' % (chan_img_url, ), end='')
                        if icon_width != '' and icon_width != '0':
                            print(' width="%s"' % (icon_width, ), end='')
                        if icon_height != '' and icon_height != '0':
                            print(' height="%s"' % (icon_height, ), end='')
                        print(' /></td>')
                    else:
                        print('<td>&nbsp;</td>')

                play_url = '?page=m3u&amp;uuid=/%s/%s' % (TS_URL_STR, chan['uuid'], )
                print('      <td width="100px" align="right"><a href="%s" '
                      'download="tvheadend.m3u">%s</a> <br />%d' \
                      % (play_url, chan_name, chan['number']))
                if CAST_SUPPORT:
                    print('<br /><a href="?page=chromecast&uri=/%s/%s"><img src="%s" /></a>' % \
                          (TS_URL_STR,
                           chan['uuid'],
                           MY_SETTINGS.get(SETTINGS_SECTION, TS_URL_CAST),
                          ))
                print('</td>')


                # grab the EPG data for the channel
                ts_query = '%s/%s?limit=10&channel=%s' % (
                    ts_url,
                    TS_URL_EPG,
                    chan['uuid'],
                )
                print('<!-- channel EPG URL %s -->' % (ts_query, ))
                ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
                print('<!-- requests.response code %d -->' % (ts_response.status_code, ))
                ts_text = ts_response.text
                #print('<td><pre>Extreme Debug!\n\n%s\n<pre></td>' % (ts_text,))
                ts_json = json.loads(ts_text, strict=False)

                if len(ts_json['entries']):
                    #chan[EPG] = ts_json['entries']
                    print(
                        '       <td valign="top" nowrap width="1600px"><div class="epg_row">'
                    )

                    entry_num = 0
                    for entry in ts_json['entries']:
                        time_start = int(entry['start'])
                        time_stop = int(entry['stop'])

                        # don't show far future, stop screen being too wide
                        if time_start - epoch_time < MAX_FUTURE:
                            if 'title' in entry:
                                title = entry['title']
                            else:
                                title = '</i>Untitled</i>'

                            if 'summary' in entry:
                                summary = entry['summary']
                            else:
                                summary = ''

                            duration = time_stop - time_start
                            time_left = duration
                            box_width = duration / SECS_P_PIXEL

                            # print the boxes containing each program
                            time_offset = time_start - epoch_time
                            if time_offset < 0:
                                time_left = time_stop - epoch_time
                                box_width = time_left / SECS_P_PIXEL
                                print('<div class="epg_now" style="width: '
                                      '%dpx; max-width: %dpx">' % (
                                          box_width,
                                          box_width,
                                      ))
                            elif entry_num == 0:
                                width_offset = time_offset / SECS_P_PIXEL
                                print(
                                    '<div class="epg_none" style="width: %dpx; '
                                    'max-width: %dpx">%d</div>' % (
                                        width_offset,
                                        width_offset,
                                        width_offset,
                                    ))
                            else:
                                print('<div class="epg_next" style="width: '
                                      '%dpx; max-width: %dpx">' % (
                                          box_width,
                                          box_width,
                                      ))
                            # print the programme details
                            try:
                                print(
                                    '<a title="record this" href="?page=record&amp;event_id=%s"'
                                    ' target="tvh_epg_record" width="320" height="320">'
                                    '&reg;</a>&nbsp;<b>%s</b><br />' % (
                                        entry['eventId'],
                                        title,
                                    ))
                                print(
                                    '<div class="tooltip"><span class="tooltiptext">'
                                    '%s</span>' % (summary, ))
                            except UnicodeEncodeError as uc_ex:
                                print('EXCEPTION: "<i>%s - %s</i>"' % (
                                    type(uc_ex).__name__,
                                    str(uc_ex),
                                ), )

                            if time_offset > 0:
                                print('start %s<br />duration %s'            \
                                      % (epoch_to_human_duration(time_start), \
                                         secs_to_human(duration), ))
                            else:
                                print('%s left of %s' % (
                                    secs_to_human(time_left),
                                    secs_to_human(duration),
                                ))
                            print('      </div></div>')
                            entry_num += 1
                    print(
                        '<div style="clear:both; font-size:1px;"></div></div></td>'
                    )
                else:
                    print('      <td>&nbsp</td>')
                print('    </tr>')

        print('</table>')


##########################################################################################
def page_error(error_text):
    '''prints error page contents'''

    global MY_SETTINGS

    print('<h1>Error</h1>')
    print('<p>Something went wrong</p>')
    print('<pre>%s</pre>' % (error_text, ))
    print('<pre>settings sections: %s</pre>' % (MY_SETTINGS.sections(), ))


##########################################################################################
def page_m3u(p_uuid):
    '''generates an m3u file to be played in e.g. vlc'''

    global MY_SETTINGS

    if TS_PAUTH in MY_SETTINGS[SETTINGS_SECTION]:
        ts_pauth = '?AUTH=%s' % (MY_SETTINGS.get(SETTINGS_SECTION, TS_PAUTH), )
    else:
        ts_pauth = ''

    # split the TVH server URL up so we can get its IP address
    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    try:
        ts_url_parsed = urllib.parse.urlparse(ts_url)
    except urllib.error.URLError as url_excpt:
        ##print(str(url_excpt))
        print('<p>Error parsing %s</p>' % (str(url_excpt), ))
        return

    if TS_URL_DVF in p_uuid:
        # recordings need to get a username/password
        full_url = '%s://%s:%s@%s:%s/%s?profile=chromecast' \
                   % (ts_url_parsed.scheme,
                      MY_SETTINGS.get(SETTINGS_SECTION, TS_USER),
                      MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS),
                      ts_url_parsed.hostname,
                      ts_url_parsed.port,
                      p_uuid,
                     )
    else:
        # live streams use persistent auth
        full_url = '%s://%s:%s%s%s' \
               % (ts_url_parsed.scheme,
                  ts_url_parsed.hostname,
                  ts_url_parsed.port,
                  p_uuid,
                  ts_pauth, )

    print('#EXTM3U')
    print(full_url)


##########################################################################################
def page_record(p_event_id, p_profile):
    '''checks the recording param and generated DVR record'''

    global MY_SETTINGS

    print('<h1>Record Item</h1>')

    if p_profile == '':
        dcg_json = get_dvr_config_grid()

        if 'entries' in dcg_json:
            # if multiple profiles, ask the user
            if len(dcg_json['entries']) > 1:
                print('<form method="get">')
                print('<input type="hidden" name="page" value="record" />')
                print('<select name="profile">')
                for entry in dcg_json['entries']:
                    print('<option value=%s>profile: %s</p>' % (
                        entry['uuid'],
                        entry['profile'],
                    ))
                print('</select>')
                print('<input type="hidden" name="event_id" value="%s" />' %
                      (p_event_id, ))
                print('<input type="submit" name="Go" value="Go" />')
                print(
                    '<input type="submit" name="Cancel" value="Cancel" onclick="self.close()" />'
                )
                print('</form method="get">')
            # if only one profile, just select it
            else:
                p_profile = dcg_json['entries'][0]['profile']
        else:
            print('<p><b>Error<b>, there were no DCG profiles</p>')

    if p_profile != '':
        print('Generating DVR record...')
        print('<p>Work In Progress</p>')

        ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
        ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
        ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
        ts_query = '%s/%s?config_uuid=%s&event_id=%s' %    \
                  (ts_url, TS_URL_CBE, p_profile, p_event_id,)
        ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
        print('<!-- page_record CBE URL %s -->' % (ts_url, ))
        ts_json = json.loads(ts_response.text, strict=False)

        #print('<pre>%s</pre>' % json.dumps(ts_json, sort_keys=True, \
        #                                   indent=4, separators=(',', ': ')) )

        if 'uuid' in ts_json:
            print('<p><b>Success</b></p>')
        else:
            print('<p><b>Failed</b></p>')
        print('<input type="hidden" name="page" value="record" />')
        print(
            '<input type="submit" name="Close" value="Close" onclick="self.close()" />'
        )
        print('</form method="get">')


##########################################################################################
def page_recordings():
    '''prints the status information, useful to check the API call is working at all'''

    global MY_SETTINGS

    print('<h1>Recordings</h1>')

    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_DEG,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    print('<!-- status inputs URL %s -->' % (ts_query, ))
    if ts_response.status_code != 200:
        print('<p>HTTP error response %d'
              '- does configured user have admin rights?</p>' %
              (ts_response.status_code, ))
        return

    ts_json = ts_response.json()
    if 'entries' in ts_json:
        print(
            '<table><tr><th>Channel Name</th><th>Title</th><th>Date</th><th>Summary</th></tr>'
        )
        for entry in ts_json['entries']:
            print('<tr>')
            if 'channelname' in entry:
                print('<td>%s</td>' % (entry['channelname'], ))
            else:
                print(TD_EMPTY_CELL)

            if 'title' in entry and 'eng' in entry['title']:
                print('<td><a href="?page=m3u&amp;uuid=play/%s" download="tvheadend.m3u">%s</a>'
                      % (entry['url'], entry['title']['eng'], ))
                if CAST_SUPPORT:
                    print('<br /><a href="?page=chromecast&uri=%s"><img src="%s" /></a>' % \
                          (entry['url'],
                           MY_SETTINGS.get(SETTINGS_SECTION, TS_URL_CAST),
                          ))
                print('</td>')
            else:
                print(TD_EMPTY_CELL)

            if 'start' in entry:
                print('<td>%s</td>' % (epoch_to_human_date(entry['start']), ))
            else:
                print(TD_EMPTY_CELL)

            if 'summary' in entry and 'eng' in entry['title']:
                print('<td>%s</td>' % (entry['summary']['eng'], ))
            elif 'subtitle' in entry and 'eng' in entry['title']:
                print('<td>%s</td>' % (entry['subtitle']['eng'], ))
            else:
                print(TD_EMPTY_CELL)

            print('</tr>')
        print('</table>')

    print('<pre>%s</pre>' % json.dumps(
        ts_json, sort_keys=True, indent=4, separators=(',', ': ')))


#########################################################################################
def page_serverinfo():
    '''prints the server information, useful to check the API call is working at all'''

    global MY_SETTINGS

    print('<h1>Server Info</h1>')

    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_SVI,
    )
    print('<!-- serverinfo URL %s -->' % (ts_query, ))
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    ts_json = ts_response.json()

    print('<pre>%s</pre>' % json.dumps(
        ts_json, sort_keys=True, indent=4, separators=(',', ': ')))


##########################################################################################
def page_settings():
    '''the configuration page'''

    global CONFIG_FILE_NAME
    global MY_SETTINGS

    # the check load config function doesn't populate an empty file
    if SETTINGS_SECTION not in MY_SETTINGS.sections():
        print('section %s doesn\'t exit' % SETTINGS_SECTION)
        MY_SETTINGS.add_section(SETTINGS_SECTION)

    # attempt to find the value of each setting, either from the params
    # submitted by the browser, or from the file, or from the defaults
    for setting in sorted(SETTINGS_DEFAULTS):
        setting_value = ''

        # get the value if possible from the URL/form
        cgi_param_name = 'c_' + setting
        if cgi_param_name in CGI_PARAMS:
            setting_value = CGI_PARAMS.getvalue(cgi_param_name)
        else:
            # otherwise get it from the config file
            try:
                setting_value = str(MY_SETTINGS.get(SETTINGS_SECTION, setting))
            except configparser.NoOptionError:
                #except configparser.NoOptionError as noex:
                #print('<p>Exception "%s"<br />' % (noex, ))
                #print('failed getting value for setting "%s" from config, '
                #      'using default</p>' % (SETTINGS_DEFAULTS[setting][TITLE], ))
                if DFLT in SETTINGS_DEFAULTS[setting]:
                    setting_value = SETTINGS_DEFAULTS[setting][DFLT]
                else:
                    setting_value = ''

        MY_SETTINGS.set(SETTINGS_SECTION, setting, setting_value)


    print('<form method="get" action="">'                           \
          '<input type="hidden" name="page" value="settings" />'    \
          '<table>'                                                 \
          '  <tr>'                                                  \
          '    <th align="right">Key</th>'                          \
          '    <th align="right">Setting</th>'                      \
          '    <th>Value</th>'                                      \
          '    <th>Default</th>\n'                                  \
          '  </tr>')

    for setting in sorted(SETTINGS_DEFAULTS):
        print('    <tr>')
        print('      <td align="right">%s&nbsp;&nbsp;</td>' % (setting, ))
        print('      <td align="right">%s&nbsp;&nbsp;</td>' %
              (SETTINGS_DEFAULTS[setting][TITLE], ))
        if setting in MY_SETTINGS[SETTINGS_SECTION]:
            setting_value = MY_SETTINGS.get(SETTINGS_SECTION, setting)
        else:
            setting_value = SETTINGS_DEFAULTS[setting][DFLT]

        print('      <td width="50%%"><input type="%s" name="c_%s" '
              'value="%s" style="display:table-cell; width:100%%" /></td>' \
              % (SETTINGS_DEFAULTS[setting][TYPE], setting, setting_value, ))
        print('      <td>&nbsp;%s</td>' % (SETTINGS_DEFAULTS[setting][DFLT], ))
        print('    </tr>')

    print('''    <tr>
      <td align="center" colspan="2">&nbsp;</td>
      <td align="center" colspan="1"><input type="submit" name="submit" value="submit" /></td>
      <td align="center" colspan="1"><input type="reset" value="revert"></td>
    </tr>
  </table>
  </form><br /><br/>
The hostname in the URL for the TVHeadend receiver will be automatically
turned into an IP address when chromecasting because chromecast devices
go direct to Google's DNS servers and thus private DNS is ignored.
''')

    config_file_handle = open(CONFIG_FILE_NAME, 'w')
    if config_file_handle:
        MY_SETTINGS.write(config_file_handle)
    else:
        print('<b>Error</b>, failed to open and write config file "%s"' %
              (CONFIG_FILE_NAME, ))


##########################################################################################
def page_status():
    '''prints the status information, useful to check the API call is working at all'''

    global MY_SETTINGS

    print('<h1>Server Status</h1>')

    print('<h2>Input Status</h2>')
    ts_url = MY_SETTINGS.get(SETTINGS_SECTION, TS_URL)
    ts_user = MY_SETTINGS.get(SETTINGS_SECTION, TS_USER)
    ts_pass = MY_SETTINGS.get(SETTINGS_SECTION, TS_PASS)
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_STI,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    print('<!-- status inputs URL %s -->' % (ts_query, ))
    if ts_response.status_code == 200:
        ts_json = ts_response.json()
        print('<pre>%s</pre>' % json.dumps(
            ts_json, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        print('<p>HTTP error response %d'
              '- does configured user have admin rights?</p>' %
              (ts_response.status_code, ))

    print('<h2>Connection Status</h2>')
    ts_query = '%s/%s' % (
        ts_url,
        TS_URL_STC,
    )
    ts_response = requests.get(ts_query, auth=(ts_user, ts_pass))
    #print('<!-- status connections URL %s -->' % (ts_query, ))
    if ts_response.status_code == 200:
        ts_json = ts_response.json()
        print('<pre>%s</pre>' % json.dumps(
            ts_json, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        print('<p>HTTP error response %d'
              '- does configured user have admin rights?</p>' %
              (ts_response.status_code, ))


##########################################################################################
def page_upgrade_check():
    '''the upgrade check page'''

    ################################################
    # see if this script is up to date
    githash_self = get_githash_self()
    githubhash_self = get_github_hash_self()

    print('<p>github hash of this file %s<br />\n' % (githubhash_self, ))
    print('git hash of this file %s<br />\n' % (githash_self, ))

    print('<p>')
    if githubhash_self == githash_self:
        print(
            'Great, this program is the same as the version on github.\n<br />\n'
        )
    else:
        print(
            'This program appears to be out of date, please update it.\n<br />\n'
        )

    print('</p>')


##########################################################################################
def m3u_page_header():
    '''page header for m3u playlists'''

    print('Content-Type: audio/x-mpegurl\n')


##########################################################################################
def html_page_header():
    '''standard html page header'''

    #print('Content-Type: text/plain\n')                # plain text for extreme debugging
    print('Content-Type: text/html; charset=utf-8\n')
    print('''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
  "http://www.w3.org/TR/html4/loose.dtd">''')
    print('<meta charset="utf-8"/>')

    print('''
<html>
  <head>
    <title>TVH EPG</title>
    <meta http-equiv="refresh" content="600;" />

    <style type="text/css">
    print('<meta charset="utf-8"/>')

    table {
        border-collapse: collapse;
        border-style: hidden;
    }

    table td, table th {
        border: 1px solid black;
    }

    .epg_row
    {
        vertical-align: top;    /* Makes sure all the divs are correctly aligned. */
        width: 100%;
        height: 100%;
        display: inline-flex;   /* prevents wrapping */
    }
    .epg_next
    {
        background-color: #e8e8ff;
        border: 1px #8080e0;
        border-style: solid;
        float: left;
    }
    .epg_now
    {
        background-color: #f0fff0;
        border: 1px #408040;
        border-style: solid;
        float: left;
    }
    .epg_none
    {
        background-color: #808080;
        border: 1px #404040;
        border-style: solid;
        float: left;
    }
    .chan_icon
    {
        background-color: #e0e0e0;
    }
    /* https://www.w3schools.com/css/css_tooltip.asp */
    /* Tooltip container */
    .tooltip {
        position: relative;
        display: inline-block;
    }

    /* Tooltip text */
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #888;
        color: #fff;
        text-align: center;
        padding: 5px 0;
        border-radius: 6px;

        /* Position the tooltip text */
        position: absolute;
        z-index: 1;
    }

    /* Show the tooltip text when you mouse over the tooltip container */
    .tooltip:hover .tooltiptext {
        visibility: visible;
    }


    pre {
      white-space: pre-wrap;       /* Since CSS 2.1 */
      white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
      white-space: -pre-wrap;      /* Opera 4-6 */
      white-space: -o-pre-wrap;    /* Opera 7 */
      word-wrap: break-word;       /* Internet Explorer 5.5+ */
    }
    </style>

  </head>
<body>
''')

    print('<a href="/python_errors/?C=M;O=A" target="_new">'
          '/python_errors (new window)</a><br /><br />')

    print('''
<b>Menu:</b>&nbsp;<a href="?page=epg">EPG</a>&nbsp;&nbsp;&nbsp;
<a href="?page=channels">Channels</a>&nbsp;&nbsp;&nbsp;
<a href="?page=recordings">Recordings</a>&nbsp;&nbsp;&nbsp;
<a href="?page=serverinfo">Server Info</a>&nbsp;&nbsp;&nbsp;
<a href="?page=settings">Settings</a>&nbsp;&nbsp;&nbsp;
<a href="?page=status">Status</a>&nbsp;&nbsp;&nbsp;
<a href="?page=upgrade_check">Upgrade Check</a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/speculatrix/tvh_epg/blob/master/README.md" target=_new>About</a> (new window)&nbsp;&nbsp;&nbsp;
''')


##########################################################################################
def secs_to_human(t_secs):
    '''turns a duration in seconds into Xd HH:MM:SS'''

    #t_secs = 86400 + 4000 + 120 + 5

    t_mins = int(t_secs / 60)
    t_hours = int(t_mins / 60)
    t_days = int(t_hours / 24)
    r_days = t_days

    r_hours = t_hours - r_days * 24
    r_mins = t_mins - r_days * 24 * 60 - r_hours * 60
    #r_secs = t_secs - r_days * 24 * 60 * 60 - r_hours * 60 * 60 - r_mins * 60

    h_days = ''
    if r_days > 0:
        h_days = '%dd, ' % r_days

    #h_time = '%s%02d:%02d:%02d' % (h_days, r_hours, r_mins, r_secs, )
    h_time = '%s%02d:%02d' % (
        h_days,
        r_hours,
        r_mins,
    )

    return h_time


##########################################################################################
def url_escape(text):
    """escape special characters for URL"""
    return "".join(URL_ESCAPE_TABLE.get(c, c) for c in text)


##########################################################################################
def web_interface():
    '''provides web interface'''

    global CONFIG_FILE_NAME
    global MY_SETTINGS

    # process the CGI params
    if 'event_id' in CGI_PARAMS:
        p_event_id = CGI_PARAMS.getvalue('event_id')
    else:
        p_event_id = ''

    if 'profile' in CGI_PARAMS:
        p_profile = CGI_PARAMS.getvalue('profile')
    else:
        p_profile = ''

    if 'uri' in CGI_PARAMS:
        p_uri = CGI_PARAMS.getvalue('uri')
    else:
        p_uri = ''

    if 'cast_device' in CGI_PARAMS:
        p_cast_device = CGI_PARAMS.getvalue('cast_device')
    else:
        p_cast_device = ''

    #illegal_param_count = 0
    error_text = 'Unknown error'
    (config_bad, error_text) = check_load_config_file()
    if config_bad < 0:
        p_page = 'error'
    #elif config_bad > 0:
    #    p_page = 'settings'
    elif 'page' in CGI_PARAMS:
        p_page = CGI_PARAMS.getvalue('page')
    else:   # set the default page if none provided
        #p_page = 'error'
        p_page = EPG


    if p_page == EPG:
        html_page_header()

        #for a in os.environ:
        #    print("<p>%s = %s</p>" % (a, os.getenv(a)) )
        #for headername, headervalue in os.environ.iteritems():
            #if headername.startswith("HTTP_"):
            #print("<p>%s = %s</p>" % (headername, headervalue, ) )

        page_epg()
        html_page_footer()
    elif p_page == 'error':
        html_page_header()
        page_error(error_text)
        html_page_footer()
    elif p_page == 'channels':
        html_page_header()
        page_channels()
        html_page_footer()
    elif CAST_SUPPORT and p_page == 'chromecast':
        html_page_header()
        page_chromecast(p_uri, p_cast_device)
        html_page_footer()
    elif p_page == 'm3u':
        if 'uuid' in CGI_PARAMS:
            p_uuid = CGI_PARAMS.getvalue('uuid')
            m3u_page_header()
            page_m3u(p_uuid)
        else:
            html_page_header()
            page_error('missing uuid for m3u generator')
            html_page_footer()
    elif p_page == 'record':
        html_page_header()
        page_record(p_event_id, p_profile)
        html_page_footer()
    elif p_page == 'recordings':
        html_page_header()
        page_recordings()
        html_page_footer()
    elif p_page == 'serverinfo':
        html_page_header()
        page_serverinfo()
        html_page_footer()
    elif p_page == 'status':
        html_page_header()
        page_status()
        html_page_footer()
    elif p_page == 'settings':
        html_page_header()
        page_settings()
        html_page_footer()
    elif p_page == 'upgrade_check':
        html_page_header()
        page_upgrade_check()
        html_page_footer()
    else:
        html_page_header()
        #page_error('no page selected')
        html_page_footer()
        #illegal_param_count += 1


##########################################################################################
# main

# a few globals
#PATH_OF_SCRIPT = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE_NAME = os.path.join(CONTROL_DIR, SETTINGS_FILE)
MY_SETTINGS = configparser.ConfigParser()

if len(sys.argv) <= 1:
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    DOCROOT = os.environ.get('DOCUMENT_ROOT', DOCROOT_DEFAULT)
    cgitb.enable(display=0, logdir=DOCROOT + '/python_errors', format='html')

    web_interface()

else:
    print('Failed')
    exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
