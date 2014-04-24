import cookielib
import urllib2
import logging

def init():
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    logging.basicConfig(level=logging.DEBUG)

