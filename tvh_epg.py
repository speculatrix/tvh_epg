#!/usr/bin/env python3
'''
a really really basic EPG for TVHeadend
'''

import  cgi
import  cgitb
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

################################################################################


TS_URL_SI = TS_URL + 'serverinfo'
TS_URL_EPG = TS_URL + 'epg/events/grid'
TS_URL_CHN = TS_URL + 'channel/grid'


CGI_PARAMS = cgi.FieldStorage()


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
    r_secs = t_secs - r_days * 24 * 60 * 60 - r_hours * 60 * 60 - r_mins * 60

    h_days = ''
    if r_days > 0:
        h_days = '%dd, ' % r_days

    h_time = '%s%02d:%02d:%02d' % (h_days, r_hours, r_mins, r_secs, )

    return h_time

################################################################################
def epoch_to_localtime(epoch_time):

    return time.asctime(time.localtime(epoch_time))

################################################################################
def save_channel_dict_to_cache():
    '''saves channel dict to cache file - FIXME'''

################################################################################
def load_channel_dict_from_cache():
    '''load channel dict from cache file - FIXME'''


################################################################################
def get_channel_dict():
    '''gets the channel listing and generats an ordered dict by name'''

    tvh_response = requests.get('%s?limit=400' % (TS_URL_CHN, ), auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()
    #print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, indent=4, separators=(',', ': ')) )

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
    #print('<pre>%s</pre>' % json.dumps(channel_dict, sort_keys=True, indent=4, separators=(',', ': ')) )
    cdl = len(channel_dict)
    print('<p><b>Channel count: %d</b></p>' % (cdl, ))

    if cdl:
        print('''  <table>
    <tr>
      <th>Channel Name</th>
      <th>Channel Number</th>
      <th>Channel UUID</th>
    </tr>
''')
        for chan in channel_dict:
            print('    <tr>')
            print('      <td>%s</td>' % (chan, ))
            print('      <td>%s</td>' % (channel_dict[chan]['number'], ))
            print('      <td>%s</td>' % (channel_dict[chan]['uuid'], ))
            print('    </tr>')

        print('</table>')

################################################################################
def page_epg():
    '''prints the EPG to stdout'''

    print('<h1>EPG</h1>')

    channel_dict = get_channel_dict()
    if len(channel_dict):

        # get the EPG data for each channel
        print('''  <table>
    <tr>
      <th>Channel Name</th>
      <th>Now</th>
      <th>Next</th>
      <th>Next</th>
      <th>Next</th>
      <th>Next</th>
    </tr>
''')
        for ch_name in channel_dict:
            print('<tr><td>%s</td>' % (ch_name, ))
            chan = channel_dict[ch_name]
            chan['epg'] = []
            req_url = '%s?limit=5&channel=%s' % (TS_URL_EPG, chan['uuid'], )
            #print('channel %s => %s<br />' % (ch_name, req_url, )) #str(chan, )) )
            tvh_response = requests.get(req_url, auth=(TS_USER, TS_PASS))
            tvh_json = tvh_response.json()
            if len(tvh_json['entries']):
                try:
                    for entry in tvh_json['entries']:
                        if 'title' in entry:
                            print('<td>%s - start %s stop %s</td>' % (entry['title'], epoch_to_localtime(entry['start']), epoch_to_localtime(entry['stop']), ) )
                        else:
                            print('<td>&nbsp;</td>')
                    #chan['epg'].append(tvh_json['entries'])
                    #print(', '.join(tvh_json['entries'] ))
                    #print(tvh_json['entries'][0]['title'])
                except Exception as e:
                    print('<td>' + str(e) + '</td>')
            else:
                print('<td colspan="5">&nbsp</td>')
            print('</tr>')
        print('</table>')

    return

    ###########################################################################
    #### below is stuff am thinking about
    if 'totalCount' in tvh_json:
        print('<p>Entries: %d</p>' % tvh_json['totalCount'] )

    if 'entries' in tvh_json:
        channel_map = {}
        for entry in tvh_json['entries']:
            channel_uuid = entry['channelUuid']
            if channel_uuid not in channel_map:
                channel_map[channel_uuid] = {}

            if 'channelNumber' in entry:
                channel_map[channel_uuid]['channelNumber'] = int(entry['channelNumber'])
            else:
                channel_map[channel_uuid]['channelNumber'] = -1

            if 'channelName' in entry:
                channel_map[channel_uuid]['channelName'] = entry['channelName']
            else:
                channel_map[channel_uuid]['channelName'] = ''

            if 'title' in entry:
                channel_map[channel_uuid]['title'] = entry['title']
            else:
                channel_map[channel_uuid]['title'] = ''

            if 'start' in entry:
                channel_map[channel_uuid]['start'] = entry['start']
            else:
                channel_map[channel_uuid]['start'] = 0

            if 'stop' in entry:
                channel_map[channel_uuid]['stop'] = entry['stop']
            else:
                channel_map[channel_uuid]['stop'] = 0

        print('''  <table>
    <tr>
      <th>Number</th>
      <th>Name</th>
      <th>Now</th>
      <th>Start</th>
      <th>Stop</th>
      <th>Duration</th>
    </tr>''')
        for key in sorted(channel_map):
            time_start = int(channel_map[key]['start'])
            time_stop = int(channel_map[key]['stop'])
            duration = time_stop - time_start
            print('    <tr>')
            print('        <td>%d</td>' % (channel_map[key]['channelNumber'], ))
            print('        <td>%s</td>' % (channel_map[key]['channelName'], ))
            #print('        <td>%s</td>' % (channel_map[key]['title'], ))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_start)), ))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_stop)), ))
            print('        <td>%s</td>' % (secs_to_human(duration)), )
            print('    </tr>')
        print('</table>')


################################################################################
def page_serverinfo():
    '''prints the server information, useful to check the API call is working at all'''

    print('<h1>server info</h1>')

    tvh_response = requests.get(TS_URL_SI, auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()

    print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, indent=4, separators=(',', ': ')) )


################################################################################
def web_interface():
    '''this is the function which produces the web interface, as opposed
    to the cron function'''

    illegal_param_count = 0

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

    print('<a href="/python_errors/?C=M;O=A" target="_new">/python_errors (new window)</a><br />')


    print('''
<a href="?page=epg">EPG</a>&nbsp;&nbsp;&nbsp;
<a href="?page=channels">Channels</a>&nbsp;&nbsp;&nbsp;
<a href="?page=serverinfo">Server Info</a>&nbsp;&nbsp;&nbsp;
''')


    if 'page' in CGI_PARAMS:
        p_page = CGI_PARAMS.getvalue('page')

        if p_page == 'serverinfo':
            page_serverinfo()
        elif p_page == 'epg':
            page_epg()
        elif p_page == 'channels':
            page_channels()
        else:
            illegal_param_count += 1


    print('''</body>
</html>''')


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
