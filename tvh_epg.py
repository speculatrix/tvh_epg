#!/usr/bin/env python3
'''
a really really basic EPG for TVHeadend
'''

import  cgi
import  cgitb
import  datetime
import  json
import  os
import  sys
import  time

import  collections
import  requests

from	tvh_epg_config	import TS_USER
from	tvh_epg_config	import TS_PASS
from	tvh_epg_config	import TS_URL
from	tvh_epg_config	import DOCROOT_DEFAULT

# pylint:disable=bad-whitespace
# pylint:disable=too-many-branches
# pylint:disable=too-many-locals
# pylint:disable=too-many-nested-blocks
# pylint:disable=too-many-statements

################################################################################


TS_URL_CHN = TS_URL + 'api/channel/grid'
TS_URL_CBE = TS_URL + 'api/dvr/entry/create_by_event'
TS_URL_DCG = TS_URL + 'api/dvr/config/grid'
TS_URL_EPG = TS_URL + 'api/epg/events/grid'

TS_URL_STC = TS_URL + 'api/status/connections'
TS_URL_STI = TS_URL + 'api/status/inputs'
TS_URL_SVI = TS_URL + 'api/serverinfo'

TS_URL_STR = TS_URL + 'stream/channel'

CGI_PARAMS = cgi.FieldStorage()


EPG = 'epg'

SECS_P_PIXEL = 10           # how many seconds per pixel

MAX_FUTURE = 9000   # 2.5 hours - how far into the future to show a prog


################################################################################
def secs_to_human(t_secs):
    '''turns a duration in seconds into Xd HH:MM:SS'''

    #t_secs = 86400 + 4000 + 120 + 5

    t_mins = int(t_secs / 60)
    t_hours = int(t_mins / 60)
    t_days = int(t_hours / 24)
    r_days = t_days

    r_hours = t_hours - r_days * 24
    r_mins = t_mins - r_days * 24 * 60      - r_hours * 60
    #r_secs = t_secs - r_days * 24 * 60 * 60 - r_hours * 60 * 60 - r_mins * 60

    h_days = ''
    if r_days > 0:
        h_days = '%dd, ' % r_days

    #h_time = '%s%02d:%02d:%02d' % (h_days, r_hours, r_mins, r_secs, )
    h_time = '%s%02d:%02d' % (h_days, r_hours, r_mins, )

    return h_time


################################################################################
def epoch_to_human(epoch_time):
    '''takes numeric sec since unix epoch and returns humanly readable time'''

    #return time.asctime(time.localtime(epoch_time))

    human_dt = datetime.datetime.fromtimestamp(epoch_time)
    return human_dt.strftime("%H:%M")


################################################################################
def load_channel_dict_from_cache():
    '''load channel dict from cache file - FIXME'''


################################################################################
def save_channel_dict_to_cache():
    '''saves channel dict to cache file - FIXME'''


################################################################################
def get_dvr_config_grid():
    '''gets the dvr/config/grid dict'''

    tvh_url = '%s' % (TS_URL_DCG, )
    tvh_response = requests.get(tvh_url, auth=(TS_USER, TS_PASS))
    print('<!-- get_dvr_config_grid URL %s -->' % (tvh_url, ))
    tvh_json = tvh_response.json()

    #print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, \
    #                                   indent=4, separators=(',', ': ')) )

    return tvh_json

################################################################################
def get_channel_dict():
    '''gets the channel listing and generats an ordered dict by name'''

    tvh_url = '%s?limit=400' % (TS_URL_CHN, )
    tvh_response = requests.get(tvh_url, auth=(TS_USER, TS_PASS))
    #print('<!-- get_channel_dict URL %s -->' % (tvh_url, ))
    tvh_json = tvh_response.json()
    #print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, \
    #                                   indent=4, separators=(',', ': ')) )

    channel_map = {}    # full channel info
    channel_list = []   # build a list of channel names
    ordered_channel_map = collections.OrderedDict()
    if 'entries' in tvh_json:

        # grab all channel info
        name_unknown = 0
        number_unknown = -1
        for entry in tvh_json['entries']:
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

            if 'number' in entry:
                ch_map['number'] = entry['number']
            else:
                ch_map['number'] = number_unknown
                name_unknown -= 1

            ch_map['uuid'] = entry['uuid']

        channel_list_sorted = sorted(channel_list, key=lambda s: s.casefold())

        # case insensitive sort of channel list
        for chan in channel_list_sorted:
            # ... produces an ordered dict
            #print('adding %s<br />' % (chan, ))
            ordered_channel_map[chan] = channel_map[chan]

    return ordered_channel_map


################################################################################
def page_channels():
    '''prints the channel list to stdout'''

    print('<h1>Channels</h1>')

    channel_dict = get_channel_dict()
    #print('<pre>%s</pre>' % json.dumps(channel_dict, sort_keys=True,
    #                                   indent=4, separators=(',', ': ')) )
    cdl = len(channel_dict)
    print('''<p><b>Channel count: %d</b></p>
<p>Note, the links are the streams, open in VLC
- you can drag and drop the link into a VLC window</p>''' % (cdl, ))

    if cdl:
        print('''  <table>
    <tr>
      <th>Channel Name</th>
      <th>Channel Number</th>
    </tr>
''')
        for ch_name in channel_dict:
            chan = channel_dict[ch_name]
            play_url = '?page=m3u&uuid=%s' % (chan['uuid'], )
            print('''    <tr>
      <td><a href="%s" download="tvheadend.m3u">%s</a></td>
      <td>%s</td>
    </tr>''' % (play_url, ch_name, chan['number'], ))

        print('</table>')

################################################################################
def page_epg():
    '''prints the EPG to stdout'''

    print('<h1>EPG</h1>')

    epoch_time = time.time()

    channel_dict = get_channel_dict()
    cdl = len(channel_dict)
    if cdl:
        print('''<p><b>Channel count: %d</b></p>
<p>Note, the links are the streams, open in VLC
- you can drag and drop the link into a VLC window</p>''' % (cdl, ))

        # get the EPG data for each channel
        print('''  <table width="1700px">
    <tr>
      <th width="80px">Channel Name</th>
      <th width="1600px" align="left"><b>It's now %s</b></th>
    </tr>
''' % (epoch_to_human(epoch_time), ) )
        # iterate through the channel list by name
        for ch_name in channel_dict:
            chan = channel_dict[ch_name]
            play_url = '?page=m3u&uuid=%s' % (chan['uuid'], )
            print('''    <tr>
      <td width="80px" align="right"><a href="%s" download="tvheadend.m3u">%s</a>
<br />%d</td>''' % (play_url, ch_name, chan['number']))

            # grab the EPG data for the channel
            req_url = '%s?limit=6&channel=%s' % (TS_URL_EPG, chan['uuid'], )
            #print('<!-- channel EPG URL %s -->' % (req_url, ))
            tvh_response = requests.get(req_url, auth=(TS_USER, TS_PASS))
            tvh_json = tvh_response.json()

            if len(tvh_json['entries']):
                #chan[EPG] = tvh_json['entries']
                print('       <td valign="top" nowrap width="1600px"><div class="epg_row">')

                entry_num = 0
                for entry in tvh_json['entries']:
                    time_start = int(entry['start'])
                    time_stop = int(entry['stop'])

                    # don't show far future, stop screen being too wide
                    if time_start - epoch_time < MAX_FUTURE:
                        duration = time_stop - time_start
                        time_left = duration
                        box_width = duration / SECS_P_PIXEL

                        time_offset = time_start - epoch_time
                        if time_offset < 0:
                            time_left = time_stop - epoch_time
                            box_width = time_left / SECS_P_PIXEL
                            print('<div class="epg_now" style="width: '
                                  '%dpx; max-width: %dpx">' % (box_width, box_width,) )
                        elif entry_num == 0:
                            width_offset = time_offset / SECS_P_PIXEL
                            print('<div class="epg_none" style="width: %dpx; '
                                  'max-width: %dpx">%d</div>'
                                  % (width_offset, width_offset, width_offset,) )
                        else:
                            print('<div class="epg_next" style="width: '
                                  '%dpx; max-width: %dpx">' % (box_width, box_width,) )
                        if 'title' in entry:
                            try:
                                # FIXME! this stops the unicode error seen on channel BBC R n Gael
                                # 'ascii' codec can't encode character '\xe8'
                                # in position 4: ordinal not in range(128)
                                print('<b>%s</b><br /><a href="?page=record&event_id=%s">'
                                      '&reg;</a>&nbsp;&nbsp;'
                                      #% (entry['title'],
                                      % (bytes.decode(entry['title'].encode("ascii", "ignore")),
                                         entry['eventId'], ))
                            except UnicodeEncodeError as uc_ex:
                                print('%s - %s' % (type(uc_ex).__name__, str(uc_ex), ))
                        else:
                            print('<i>untitled</i><br />') # empty table cell
                        if time_offset > 0:
                            print('start %s<br />duration %s'            \
                                  % (epoch_to_human(time_start), secs_to_human(duration), ))
                        else:
                            print('%s left of %s'
                                  % (secs_to_human(time_left), secs_to_human(duration), ))
                        print('      </div>')
                        entry_num += 1
                print('<div style="clear:both; font-size:1px;"></div></div></td>')
            else:
                print('      &nbsp</td>')
            print('    </tr>')
        print('</table>')


################################################################################
def page_error():
    '''prints an error'''

    print('<h1>Error</h1>')
    print('<p>Something went wrong</p>')


################################################################################
def page_m3u(p_uuid):
    '''generates an m3u file to be played in e.g. vlc'''

    print('#EXTM3U')
    print('%s/%s' % (TS_URL_STR, p_uuid, ))


################################################################################
def page_record(p_event_id, p_profile):
    '''checks the recording param and generated DVR record'''

    print('<h1>Record Item</h1>')

    if p_profile == '':
        dcg_json = get_dvr_config_grid()

        if 'entries' in dcg_json:
            print('<form method="get">')
            print('<input type="hidden" name="page" value="record" />')
            print('<select name="profile">')
            for entry in dcg_json['entries']:
                print('<option value=%s>profile: %s</p>' % (entry['uuid'], entry['profile'], ))
            print('</select>')
            print('<input type="hidden" name="event_id" value="%s" />' % (p_event_id, ))
            print('<input type="submit" name="Go" value="Go" />')
            print('</form method="get">')
        else:
            print('<p><b>Error<b>, there were no DCG profiles</p>')

    else:
        print('Generating DVR record...')
        print('<p>Work In Progress</p>')

        tvh_url = '%s?config_uuid=%s&event_id=%s' % (TS_URL_CBE, p_profile, p_event_id,)
        tvh_response = requests.get(tvh_url, auth=(TS_USER, TS_PASS))
        print('<!-- page_record CBE URL %s -->' % (tvh_url, ))
        tvh_json = tvh_response.json()

        #print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, \
        #                                   indent=4, separators=(',', ': ')) )

        if 'uuid' in tvh_json:
            print('<p><b>Success</b></p>')
        else:
            print('<p><b>Failed</b></p>')


################################################################################
def page_serverinfo():
    '''prints the server information, useful to check the API call is working at all'''

    print('<h1>Server Info</h1>')

    tvh_response = requests.get(TS_URL_SVI, auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()
    #print('<!-- serverinfo URL %s -->' % (TS_URL_SVI, ))

    print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, indent=4, separators=(',', ': ')) )


################################################################################
def page_status():
    '''prints the status information, useful to check the API call is working at all'''

    print('<h1>Server Status</h1>')

    print('<h2>Input Status</h2>')
    tvh_response = requests.get(TS_URL_STI, auth=(TS_USER, TS_PASS))
    #print('<!-- status inputs URL %s -->' % (TS_URL_STI, ))
    if tvh_response.status_code == 200:
        tvh_json = tvh_response.json()
        print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True,
                                           indent=4, separators=(',', ': ')) )
    else:
        print('<p>HTTP error response %d'
              '- does configured user have admin rights?</p>' % (tvh_response.status_code, ) )

    print('<h2>Connection Status</h2>')
    tvh_response = requests.get(TS_URL_STC, auth=(TS_USER, TS_PASS))
    #print('<!-- status connections URL %s -->' % (TS_URL_STC, ))
    if tvh_response.status_code == 200:
        tvh_json = tvh_response.json()
        print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True,
                                           indent=4, separators=(',', ': ')) )
    else:
        print('<p>HTTP error response %d'
              '- does configured user have admin rights?</p>' % (tvh_response.status_code, ) )


################################################################################
def m3u_page_header():
    '''page header for m3u playlists'''

    print('Content-Type: audio/x-mpegurl\n')


################################################################################
def html_page_header():
    '''standard html page header'''


    #print('Content-Type: text/plain\n')    # plain text for extreme debugging
    print('Content-Type: text/html\n')     # HTML is following

    print('''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
  "http://www.w3.org/TR/html4/loose.dtd">''')

    print('''
<html>
  <head>
    <title>TVH EPG</title>
    <style type="text/css">

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
<a href="?page=serverinfo">Server Info</a>&nbsp;&nbsp;&nbsp;
<a href="?page=status">Status</a>&nbsp;&nbsp;&nbsp;
''')

################################################################################
def html_page_footer():
    '''no surprises'''

    print('''</body>
</html>''')


################################################################################
def web_interface():
    '''provides web interface'''

    if 'event_id' in CGI_PARAMS:
        p_event_id = CGI_PARAMS.getvalue('event_id')
    else:
        p_event_id = ''

    if 'profile' in CGI_PARAMS:
        p_profile = CGI_PARAMS.getvalue('profile')
    else:
        p_profile = ''


    #illegal_param_count = 0
    if 'page' in CGI_PARAMS:
        p_page = CGI_PARAMS.getvalue('page')
    else:
        p_page = ''
        #p_page = 'error'

    if p_page == EPG:
        html_page_header()
        page_epg()
        html_page_footer()
    elif p_page == 'error':
        html_page_header()
        page_error()
        html_page_footer()
    elif p_page == 'channels':
        html_page_header()
        page_channels()
        html_page_footer()
    elif p_page == 'm3u':
        if 'uuid' in CGI_PARAMS:
            p_uuid = CGI_PARAMS.getvalue('uuid')
            m3u_page_header()
            page_m3u(p_uuid)
        else:
            html_page_header()
            page_error()
            html_page_footer()
    elif p_page == 'record':
        html_page_header()
        page_record(p_event_id, p_profile)
        html_page_footer()
    elif p_page == 'serverinfo':
        html_page_header()
        page_serverinfo()
        html_page_footer()
    elif p_page == 'status':
        html_page_header()
        page_status()
        html_page_footer()
    else:
        html_page_header()
        page_record(p_event_id, p_profile)
        #page_error()
        html_page_footer()
        #illegal_param_count += 1



################################################################################
# main

if len(sys.argv) <= 1:
    DOCROOT = os.environ.get('DOCUMENT_ROOT', DOCROOT_DEFAULT)
    cgitb.enable(display=0, logdir=DOCROOT + '/python_errors', format='html')
    web_interface()

else:
    print('Failed')
    exit(1)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
