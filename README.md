# tvh_epg

This is just the very start of this project, at the moment it's just a
proof of concept, a simple python3 program which grabs channel and EPG
data from a TVHeadEnd server
 There's no point in you playing with it unless you just
want to see some python being hacked out.

That said, I'd be grateful for any help I can get!


## installation

* put the tvh_epg.py into /usr/lib/cgi-bin
* put the config file into /usr/lib/cgi-bin/tvh_epg_config/
* edit the config with your server details


## roadmap

### TBD

* analyse the EPG data for a specific channel
* create a proper now/next view timeline
* start to use /var/lib/tvh_epg for settings and caches etc
* implement user definable settings
* save a cache of channel information


### Done - in reverse order

20180921
* add a function to get the channel list
* experiment with a function to get the EPG data for a specific channel

20180920:
* create a github repo and push some stuff in there
* get a simple web page that extracts and displays any old EPG data 
* create a config module as a temporary solution pending a proper settings function
* get a simple CGI-BIN up which talks to the API
* start a TVH Epg web interface in Python


## Acknowledgement and thanks

This program only exists because of the awesome developers working on 
https://tvheadend.org


