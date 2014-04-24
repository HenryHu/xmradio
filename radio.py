import urllib2
from HTMLParser import HTMLParser
import xml.etree.ElementTree as ET
import song
import info
import logging

radio_url_temp = "http://www.xiami.com/radio/play/type/%s/oid/%s"
radio_list_url_temp = "http://www.xiami.com/radio/xml/type/%s/id/%s?v=%s"
player_path_prefix = '/res/fm/xiamiRadio'

logger = logging.getLogger('radio')

class RadioPageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.v_val = ''

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

def visit_radio(state, radio_type, radio_id):
    radio_url = radio_url_temp % (radio_type, radio_id)
    logger.debug("radio page: %s" % radio_url)
    radio_page = urllib2.urlopen(radio_url).read()
    parser = RadioPageParser()
    parser.feed(radio_page)
    if parser.v_val == '':
        logger.warning('can"t find v value')
        state['v_val'] = '0'
    else:
        state['v_val'] = parser.v_val

def get_radio_list(state, radio_type, radio_id):
    # visit the radio page to get v value
    # TODO not sure if this is required
    if not 'v_val' in state:
        visit_radio(state, radio_type, radio_id)

    # get list of songs
    radio_list_url = radio_list_url_temp % (radio_type, radio_id, state['v_val'])
    logger.debug("radio list: %s" % radio_list_url)
    radio_list = urllib2.urlopen(radio_list_url).read()

    # parse list
    root = ET.fromstring(radio_list)
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

if __name__ == '__main__':
    import init
    import config
    state = {}
    init.init()
    import login
    login.login(state, config.username, config.password)
    tracks = get_radio_list(state, config.radio_type, config.radio_id)
    for track in tracks:
        track.dump_info()
