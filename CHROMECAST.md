# Adding Chromecast Support To TVH_EPG

This is the barest details of how to proceed. These instructions will be improved over time.


## Persistent Auth Token

You need to create a user with a persistent authentication token, and put that into the settings.


## Install pychromecast library

you need to git clone the <a href="https://github.com/balloob/pychromecast">pychromecast repo</a> and copy the subdirectory pychromecast to the place where you put the tvh_epg.py CGI script. If the tvh_epg.py script can't import pychromecast then you won't see the link against the channel list to cast it.

Suppose the tvh_epg.py script is in /usr/lib/cgi-bin, then do this:
```
cd /tmp
git clone https://github.com/balloob/pychromecast.git
cd pychromecast
rsync -au pychromecast /usr/lib/cgi-bin
```



## Streaming Profile

Chromecast devices support a narrow range of codecs, so we need to add a streaming profile which makes the TVH server transcode the stream into something that the chromecast device will handle.

<img src="https://raw.githubusercontent.com/speculatrix/tvh_epg/master/chromecast_profile1.jpg" />


This has been tested with the following devices:
* Chromecast 3rd Generation ( https://en.wikipedia.org/wiki/Chromecast#Third_generation )
