# roadmap

## TBD

* create a proper now/next view timeline
* save a cache of channel information
* make display more attractive
* add a filter feature, to exclude or only include channels
* channel tag filters should be preserved when you submit

## Done - in reverse order

20181009
* channel tag filters now work

20181006
* record function pops up a separate window; no need to confirm the profile if there's only one

20181006
* started function to filter on tags
* added ability to turn channel icons off and on
* add a hover feature to show more information about a program
* uses TVH server's own channel images; not sure if this is better

20181003
* implemented a settings page
* now instructs the user to create a directory for /var/lib/tvh_epg for settings and caches etc

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

