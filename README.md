# tvh_epg

## overview
This is the early days for this project, at the moment it's
just a basic now/next electronic program guide and recordings
list for TVHeaded.

It's a simple python3 cgi-bin program which grabs channel, EPG or
recordings data from a TVHeadEnd server and presents it in a grid
form, with a link to click to play the channel.

This cgi-bin program runs independently of the TV Headend server,
it can run on the same machine (but in, say, Apache) or a different
one.

I expect to add more features to make it more useful... I'd be
grateful for any help I can get! See the ROADMAP for plans and
changes.


## installation

* install a web server that can execute CGI-BIN programs, e.g. apache2 with "sudo apt-get install apache2"
* enable cgi-bin programs e.g. run "sudo a2enmod cgid" 
* put the tvh_epg.py into /usr/lib/cgi-bin
* access the CGI through your web browser and it will tell you what additional setup is needed
* if you want channel icons, put them into a directory called TVLogos under the document root
** You can get FreeSat icons from https://github.com/Elky666/TVLogos


## roadmap

See <a href="ROADMAP.md">ROADMAP.md</a>


### Screenshots

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/Screenshot_20181006_160730.png" />


## Acknowledgement and thanks

This program only exists because of the awesome developers working on
https://tvheadend.org

And also big thanks to Paulus Schoutsen (<a href="https://github.com/balloob">balloob</a>) for pychromecast


## Useful links

https://github.com/balloob/pychromecast - the library used for chromecast support

https://github.com/dave-p/TVH-API-docs - the API docs

https://tvheadend.org/boards/5/topics/34232 - the TVH forum discussion which sparked this off

https://tvheadend.org/boards/5/topics/21836?r=39707 - the discussion about pychromecast

