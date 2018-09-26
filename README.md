# tvh_epg

This is the early days for this project, at the moment it's just
a basic now/next electronic program guide for TVHeaded.

It's a simple python3 cgi-bin program which grabs channel and EPG
data from a TVHeadEnd server and presents it in a grid form, with
a link to click to play the channel.

I expect to add more features to make it more useful... I'd be
grateful for any help I can get!


## installation

* install a web server that can execute CGI-BIN programs, e.g. apache2 with "sudo apt-get install apache2"
* enable cgi-bin programs e.g. run "sudo a2enmod cgid" 
* put the tvh_epg.py into /usr/lib/cgi-bin
* put the config file into /usr/lib/cgi-bin/tvh_epg_config/
* edit the config with your server details


## roadmap

### TBD

* create a proper now/next view timeline
* start to use /var/lib/tvh_epg for settings and caches etc
* implement user definable settings
* save a cache of channel information
* make display more attractive
* add feature to hover mouse for more information
* get the channel icons
* add a filter feature, to exclude or only include channels


### Done - in reverse order

20180926
* started the recording function
* colour coded now/next
* sets a time limit to limit width, not just number of EPG events

20180925
* got now/next boxes to be good proportions

20180924
* some progress using CSS to make now/next boxes be proportionate

20180923
* analyse the EPG data for a specific channel so can calculate duration

20180922
* make channel link generate an m3u with the auth token
* add status page (needs admin rights)

20180921
* make channel name be link to the live stream
* add a function to get the channel list
* experiment with a function to get the EPG data for a specific channel

20180920:
* create a github repo and push some stuff in there
* get a simple web page that extracts and displays any old EPG data
* create a config module as a temporary solution pending a proper settings function
* get a simple CGI-BIN up which talks to the API
* start a TVH Epg web interface in Python

### Screenshots

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/20180926_tvh_epg.png" />


## Acknowledgement and thanks

This program only exists because of the awesome developers working on
https://tvheadend.org


## Useful links

https://github.com/dave-p/TVH-API-docs - the API docs

https://tvheadend.org/boards/5/topics/34232 - the TVH forum discussion which sparked this off

