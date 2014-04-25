import urllib2
from HTMLParser import HTMLParser
import xml.etree.ElementTree as ET
import song
import info
import logging
import json
import re

radio_url_temp = "http://www.xiami.com/radio/play/id/%s"
radio_list_url_temp = "http://www.xiami.com/radio/xml/type/%s/id/%s?v=%s"
player_path_prefix = '/res/fm/xiamiRadio'
player_host = "http://www.xiami.com"
fav_radio_url_temp = "http://www.xiami.com/radio/favlist?page=%d"
radio_data_rex = re.compile("/radio/xml/type/([0-9]+)/id/([0-9]+)")

logger = logging.getLogger('radio')

class RadioPageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.v_val = ''
        self.player_path = ''
        self.in_player = False
        self.radio_data_url = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'object' and attrs['type'] == 'application/x-shockwave-flash':
            path = attrs['data']
            if path.startswith(player_path_prefix):
                values = path.split('?')[1]
                for pair in values.split('&'):
                    split_pair = pair.split('=')
                    if len(split_pair) == 2 and split_pair[0] == 'v':
                        self.v_val = split_pair[1]
                self.player_path = path
                self.in_player = True
        elif tag == 'param':
            if 'name' in attrs and attrs['name'] == 'FlashVars':
                flashvars = attrs['value']
                for flashvar in flashvars.split('&'):
                    (name, val) = flashvar.split('=')
                    if name == 'dataUrl':
                        self.radio_data_url = val

    def handle_endtag(self, tag):
        if tag == 'object' and self.in_player:
            self.in_player = False

def visit_radio(state, radio_pid):
    radio_url = radio_url_temp % radio_pid
    logger.debug("radio page: %s" % radio_url)
    radio_page = urllib2.urlopen(radio_url).read()
    parser = RadioPageParser()
    parser.feed(radio_page)
    if parser.v_val == '':
        logger.warning('can"t find v value')
        state['v_val'] = '0'
    else:
        state['v_val'] = parser.v_val
    if parser.player_path:
        state['player_path'] = player_host + parser.player_path
    state['radio_page_path'] = radio_url
    result = radio_data_rex.match(parser.radio_data_url)
    state['radio_type'] = result.group(1)
    state['radio_id'] = result.group(2)

def get_radio_list(state, radio_type, radio_id):
    # visit the radio page to get v value
    # TODO not sure if this is required
    if not 'v_val' in state:
        raise Exception("visit radio page first")

    # get list of songs
    radio_list_url = radio_list_url_temp % (radio_type, radio_id, state['v_val'])
    logger.debug("radio list: %s" % radio_list_url)
    radio_list = urllib2.urlopen(radio_list_url).read()

    # parse list
    try:
        root = ET.fromstring(radio_list)
    except Exception as e:
        logger.error("fail to parse song list!")
        logger.error(radio_list)
        raise e
    tracks = []
    for child in root:
        if child.tag == 'config':
            # update personal info from new data
            info.update_state(state, child)
        elif child.tag == 'trackList':
            for track_node in child:
                track = song.Song()
                for prop_node in track_node:
                    tag = prop_node.tag
                    text = prop_node.text
                    if tag == 'location':
                        text = song.decrypt_location(text)
                    setattr(track, tag, text)
                tracks += [track]

    return tracks

def get_fav_radio(state, page):
    assert(page >= 1)
    fav_radio_url = fav_radio_url_temp % page
    fav_radio_ret = urllib2.urlopen(fav_radio_url).read()
    fav_radio_parsed = json.loads(fav_radio_ret)

    if not fav_radio_parsed['status']:
        raise Exception('fail to get favourite radios. %s' % fav_radio_parsed['message'])
    fav_radios = fav_radio_parsed['data']
    # unknown
    prev_fav = fav_radios['prev']
    next_fav = fav_radios['next']

    fav_radios = fav_radios['data']
    return fav_radios

if __name__ == '__main__':
    import init
    import config
    state = init.init()
    if not info.authenticated(state):
        import login
        login.login(state, config.username, config.password)
    visit_radio(state, config.radio_id)
    import time
    for x in xrange(10):
        tracks = get_radio_list(state, state['radio_type'], state['radio_id'])
        for track in tracks:
            track.dump_info()
        time.sleep(5)
