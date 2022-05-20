# tvh_epg

## overview
This is an electronic program guide for TV Headend, whose user interface
is rendered entirely in simple HTML so as to be lightweight.

It was written because TVH doesn't really have an EPG, just a list of 
what's on and how much of currently playing programs has elapsed.

Users can choose just to see a channel list, a full EPG in the classic
style of horizontal bars for each channel, and a list of recordings.

This tool doesn't have the ability to play channels or recordings at all,
rather, it outputs an m3u playlist file which can be opened in a player
like VLC or MXPlayer.

There is now basic Chromecast support (which requires that the web server
running this program is on the same network (broadcast domain) as a Chromecast.


It's a simple python3 cgi-bin program which grabs channel, EPG or
recordings data from a TVHeadEnd server and presents it in a grid
form, with a link to click to play the channel.

This cgi-bin program runs independently of the TV Headend server,
it can run on the same machine (but in, say, Apache) or a different
one.

I expect to add more features to make it more useful... I'd be
grateful for any help I can get! See the ROADMAP for plans and
changes.

Although the instructions seem a little daunting at first, each
stage should be fairly easy.


## Setting Up TV Headend

### Create a user with persistent authentication token

Create a user for playing media, enabling persistent authentication, and copy off that token and put into the settings along with the username and password.

![Audio-Only Profile](https://raw.githubusercontent.com/speculatrix/ya_pi_radio/master/webby_user.png)



## installation

* install a web server that can execute CGI-BIN programs, e.g. apache2 with "sudo apt-get install apache2"
* enable cgi-bin programs e.g. run "sudo a2enmod cgid" 
* put the tvh_epg.py into /usr/lib/cgi-bin
* make the config directory
** this directory is /var/lib/tvh_epg ("sudo mkdir -p /var/lib/tvh_epg)
** make it group owned by www-data (for example "sudo chown www-data /var/lib/tvh_epg")
** add group write ("sudo chmod g+ws /var/lib/tvh_epg")
* access the CGI through your web browser and it will tell you what additional setup is needed
* if you want channel icons, put them into a directory called TVLogos under the document root
** You can get FreeSat icons from https://github.com/Elky666/TVLogos

## chromecast

There is basic support for chromecast, see <a href="CHROMECAST.md">CHROMECAST.md</a>
for installation details. The web server running the CGI needs to be on the
same network.
It's quite slow as the pychromecast library has to listen on the network for
the chromecast to announce itself.

Note that you need 9.4.0 because any later changes break tvh_epg
https://github.com/home-assistant-libs/pychromecast/archive/refs/tags/9.4.0.zip

Thanks to https://github.com/dgilbert2 for finding that and letting me know


## roadmap

See <a href="ROADMAP.md">ROADMAP.md</a>


## Screenshots

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/epg_sample.png" />


## Acknowledgement and thanks

This program only exists because of the awesome developers working on
https://tvheadend.org

And also big thanks to Paulus Schoutsen (<a href="https://github.com/balloob">balloob</a>) for pychromecast

A big thanks to (a href="https://github.com/dgilbert2">dgilbert2</a> for being a patient alpha tested

## Useful links

https://github.com/balloob/pychromecast - the library used for chromecast support

https://github.com/dave-p/TVH-API-docs - the API docs

https://tvheadend.org/boards/5/topics/34232 - the TVH forum discussion which sparked this off

https://tvheadend.org/boards/5/topics/21836?r=39707 - the discussion about pychromecast

