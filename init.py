import cookielib
import urllib2
import logging

def init():
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = (('User-agent', 'Mozilla/5.0 ( X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0'),)
    urllib2.install_opener(opener)

    logging.basicConfig(level=logging.DEBUG)

