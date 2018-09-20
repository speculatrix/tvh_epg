#!/usr/bin/env python3
'''
a really really basic EPG for TVHeadend
'''

import  cgi
import  cgitb
import  json
import  os
import  requests
import  sys
import  time

from	tvh_epg_config	import TS_USER
from	tvh_epg_config	import TS_PASS
from	tvh_epg_config	import TS_URL
from	tvh_epg_config	import DOCROOT_DEFAULT

#####################################################################################################################


TS_URL_SI = TS_URL + 'serverinfo'
TS_URL_EPG = TS_URL + 'epg/events/grid'


CGI_PARAMS = cgi.FieldStorage()


#####################################################################################################################
def secs_to_human(t_secs):
    
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

    return(h_time)

#####################################################################################################################
def page_epg():

    print('<h1>epg</h1>')

    tvh_response = requests.get('%s?limit=400' % (TS_URL_EPG, ), auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()

    if 'totalCount' in tvh_json:
        print('<p>Entries: %d</p>' % tvh_json['totalCount'] )

    if 'entries' in tvh_json:
        channel_map = {}
        for entry in tvh_json['entries']:
            #print('<p>adding chr %s and chn %s</p>' % (entry['channelNumber'], entry['channelName'], ) )
            channel_number = int(entry['channelNumber'])
            if not channel_number in channel_map:
                channel_map[channel_number] = {}

            channel_map[channel_number]['channelName'] = entry['channelName']
            channel_map[channel_number]['title'] = entry['title']
            channel_map[channel_number]['start'] = entry['start']
            channel_map[channel_number]['stop'] = entry['stop']

        print('  <table>\n    <tr><th>Number</th><th>Name</th><th>Now</th><th>Start</th><th>Stop</th><th>Duration</th></tr>')
        for key in sorted(channel_map):
            time_start = int(channel_map[key]['start'])
            time_stop = int(channel_map[key]['stop'])
            duration = time_stop - time_start
            print('    <tr>')
            print('        <td>%d</td><td>%s</td>' % (key, channel_map[key]['channelName'], ))
            print('        <td>%s</td>' % (channel_map[key]['title'], ))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_start), )))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_stop), )))
            print('        <td>%s</td>' % (secs_to_human(duration), ))
            print('    </tr>')
        print('</table>')

    print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, indent=4, separators=(',', ': ')) )


#####################################################################################################################
def page_now():

    print('<h1>Whats On Now</h1>')

    tvh_response = requests.get('%s?limit=400' % (TS_URL_EPG, ), auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()

    if 'totalCount' in tvh_json:
        print('<p>Entries: %d</p>' % tvh_json['totalCount'] )

    if 'entries' in tvh_json:
        channel_map = {}
        for entry in tvh_json['entries']:
            channel_number = int(entry['channelNumber'])
            if not channel_number in channel_map:
                channel_map[channel_number] = {}

            channel_map[channel_number]['channelName'] = entry['channelName']
            channel_map[channel_number]['title'] = entry['title']
            channel_map[channel_number]['start'] = entry['start']
            channel_map[channel_number]['stop'] = entry['stop']

        print('  <table>\n    <tr><th>Number</th><th>Name</th><th>Now</th><th>Start</th><th>Stop</th><th>Duration</th></tr>')
        for key in sorted(channel_map):
            time_start = int(channel_map[key]['start'])
            time_stop = int(channel_map[key]['stop'])
            duration = time_stop - time_start
            print('    <tr>')
            print('        <td>%d</td><td>%s</td>' % (key, channel_map[key]['channelName'], ))
            print('        <td>%s</td>' % (channel_map[key]['title'], ))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_start), )))
            print('        <td>%s</td>' % (time.asctime(time.localtime(time_stop), )))
            print('        <td>%s</td>' % (secs_to_human(duration), ))
            print('    </tr>')
        print('</table>')


#####################################################################################################################
def page_serverinfo():

    print('<h1>server info</h1>')

    tvh_response = requests.get(TS_URL_SI, auth=(TS_USER, TS_PASS))
    tvh_json = tvh_response.json()

    print('<pre>%s</pre>' % json.dumps(tvh_json, sort_keys=True, indent=4, separators=(',', ': ')) )


#####################################################################################################################
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

    print('Python errors at <a href="/python_errors/?C=M;O=A" target="_new">/python_errors (new window)</a><br />')


    print('''
<a href="?page=epg">EPG</a>&nbsp;&nbsp;&nbsp;
<a href="?page=now">Now</a>&nbsp;&nbsp;&nbsp;
<a href="?page=serverinfo">Server Info</a>&nbsp;&nbsp;&nbsp;
''')


    if 'page' in CGI_PARAMS:
        p_page = CGI_PARAMS.getvalue('page')

        if (p_page == 'serverinfo'):
            page_serverinfo()
        elif (p_page == 'epg'):
            page_epg()
        elif (p_page == 'now'):
            page_now()


    print('''</body>
</html>''')


#####################################################################################################################
# main

if len(sys.argv) <= 1:
    DOCROOT = os.environ.get('DOCUMENT_ROOT', DOCROOT_DEFAULT)
    cgitb.enable(display=0, logdir=DOCROOT + '/python_errors', format='html')
    web_interface()

else:
    print('Failed')
    exit(1)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
