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

See <a href="ROADMAP.md">ROADMAP.md</a>


### Screenshots

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/Screenshot_20181006_160730.png" />


## Acknowledgement and thanks

This program only exists because of the awesome developers working on
https://tvheadend.org


## Useful links

https://github.com/dave-p/TVH-API-docs - the API docs

https://tvheadend.org/boards/5/topics/34232 - the TVH forum discussion which sparked this off

