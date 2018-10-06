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

* if you want channel icons, put them into a directory called TVLogos under the document root
** You can get FreeSat icons from https://github.com/Elky666/TVLogos


## roadmap

### TBD

* create a proper now/next view timeline
* save a cache of channel information
* make display more attractive
* add a filter feature, to exclude or only include channels


### Done - in reverse order

20181006
* started function to filter on tags
* added ability to turn channel icons off and on
* add a hover feature to show more information about a program
* uses TVH server's own channel images; not sure if this is better

20181003
* implemented a settings page
* now instructst the user to create a directory for /var/lib/tvh_epg for settings and caches etc

20181001
* channel icons

20180927
* recording function works, but it's ugly

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

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/Screenshot_20181006_160730.png" />


## Acknowledgement and thanks

This program only exists because of the awesome developers working on
https://tvheadend.org


## Useful links

https://github.com/dave-p/TVH-API-docs - the API docs

https://tvheadend.org/boards/5/topics/34232 - the TVH forum discussion which sparked this off

