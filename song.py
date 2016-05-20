import urllib
import urllib2
import json
import logging
import info
import re
from HTMLParser import HTMLParser

lyric_url = "http://www.xiami.com/radio/lyric"
related_info_url = "http://www.xiami.com/radio/relate-info"
get_hq_url_temp = "http://www.xiami.com/song/gethqsong/sid/%s"
similar_artists_url_temp = "http://www.xiami.com/ajax/similar-artists?id=%s&c=%d"
song_url_temp = "http://www.xiami.com/song/%s"
artist_id_rex = re.compile("/artist/([0-9]+)")
song_info_url_temp = "http://www.xiami.com/song/playlist/id/%s/object_name/default/object_id/0/cat/json"

logger = logging.getLogger('song')

class SongPageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.title = None
        self.artist = None
        self.album = None
        self.image = None
        self.album_id = None
        self.artist_id = None

        self.in_nav = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            try:
                prop = attrs['property']
                content = attrs['content']
                if prop == 'og:title':
                    self.title = content
                elif prop == 'og:music:artist':
                    self.artist = content
                elif prop == 'og:music:album':
                    self.album = content
                elif prop == 'og:image':
                    self.image = content
            except:
                pass
        elif tag == 'a':
            try:
                if attrs['id'] == 'albumCover':
                    href = attrs['href']
                    self.album_id = href.split('/')[-1]
            except:
                pass
            if self.in_nav:
                if 'href' in attrs:
                    ret = artist_id_rex.match(attrs['href'])
                    if ret:
                        self.artist_id = ret.group(1)
        elif tag == 'div':
            if 'id' in attrs and attrs['id'] == 'nav':
                self.in_nav = True

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.in_nav:
                self.in_nav = False

class Song(object):
    # expected attributes:
    # * title
    # * song_id
    # * album_id
    # * album_name
    # * grade
    # * artist
    # * location
    # * pic
    # * length
    # * artist_id
    # * rec_note
    # * hq_location
    def __init__(self, parsed = {}):
        for key in parsed:
            setattr(self, key, parsed[key])

        if hasattr(self, 'location'):
            self.info_loaded = True
        else:
            self.info_loaded = False

    def dump_info(self):
        print self.title, self.location

    def get_lyric(self):
        if not hasattr(self, 'song_id'):
            raise Exception("missing song id")
        # use POST as the official one
        args = urllib.urlencode({'sid' : self.song_id})
        lyric = urllib2.urlopen(lyric_url, args).read()
        return lyric

    def get_hq_location(self, state):
        if not hasattr(self, 'song_id'):
            raise Exception("missing song id")

        if hasattr(self, 'hq_location'):
            return self.hq_location

        get_hq_url = get_hq_url_temp % self.song_id
        logger.debug("get hq req: %s" % get_hq_url)
        get_hq_req = urllib2.Request(get_hq_url)
        if 'player_path' in state:
            get_hq_req.add_header('Referer', state['player_path'])
        get_hq_rep = urllib2.urlopen(get_hq_req).read()

        try:
            get_hq_parsed = json.loads(get_hq_rep)
        except Exception as e:
            logger.exception("fail to parse get hq reply: %s", get_hq_rep)
            raise e

        if not 'status' in get_hq_parsed or get_hq_parsed['status'] != 1:
            raise Exception("fail to get hq url. status = %d" % get_hq_parsed['status'])

        self.hq_location = decrypt_location(get_hq_parsed['location'])
        return self.hq_location

    def get_related_info(self, state):
        if not hasattr(self, 'artist_id'):
            raise Exception("missing artist id")

        xiamitoken = info.get_xiamitoken(state)
        # use POST as the official one
        args = urllib.urlencode({'arid': self.artist_id, '_xiamitoken': xiamitoken})
        request = urllib2.Request(related_info_url)
        request.add_header('Referer', state['radio_page_path'])
        related_info = urllib2.urlopen(request, args).read()
        return related_info

    def get_similar_artists(self, count):
        if not hasattr(self, 'artist_id'):
            raise Exception("missing artist id")

        similar_artists_url = similar_artists_url_temp % (self.artist_id, count)
        similar_artists = urllib2.urlopen(similar_artists_url).read()
        return json.loads(similar_artists)

    def get_song_url(self):
        if not hasattr(self, 'song_id'):
            raise Exception("missing song id")

        return song_url_temp % self.song_id

    def load_info(self):
        if not hasattr(self, 'song_id'):
            raise Exception("missing song id")

        if self.info_loaded:
            return

        logging.debug("loading info of %s" % self.song_id)
        song_info_url = song_info_url_temp % self.song_id
        song_info_ret = urllib2.urlopen(song_info_url).read()
        song_info = json.loads(song_info_ret)

        if not 'status' in song_info or not song_info['status']:
            raise Exception("fail to load song info.%s" %
                (song_info['message'] if 'message' in song_info else ""))

        my_info = song_info['data']['trackList'][0]
        self.__init__(my_info)
        if hasattr(self, 'songName'):
            # for some reason, title = album_name
            self.title = self.songName

    def load_info_from_page(self):
        ''' Load info of this song, index by song_id (deprecated)'''
        # missing:
        # * grade
        # * location
        # * length
        # * rec_note
        url = self.get_song_url()
        song_page = urllib2.urlopen(url).read().decode('utf-8')
        parser = SongPageParser()
        parser.feed(song_page)
        self.title = parser.title
        self.album_name = parser.album
        self.artist = parser.artist
        self.pic = parser.image
        self.album_id = parser.album_id
        self.artist_id = parser.artist_id

def decrypt_location(encrypted):
    output = ''

    # decryption method obtained from internet
    # characters of the URL is listed in a table vertically
    # and the encoding result is read out horzontally

    # first part is the number of rows
    i = 0
    while encrypted[i].isdigit():
        i += 1
    rows = int(encrypted[:i])
    encrypted = encrypted[i:]
    total_len = len(encrypted)

    # looks like this:

    # h******************** ^
    # t******************** | final_col_len
    # t******************** v
    # p*******************
    # %*******************
    # <-   min_row_len  ->

    r = 0
    c = 0
    pos = 0
    min_row_len = total_len / rows
    final_col_len = total_len % rows
    for x in xrange(total_len):
        output += encrypted[pos]
        if r == rows - 1:
            # last row reached, reset to first row
            r = 0
            c += 1
            pos = c
        else:
            # move to next row
            pos += min_row_len
            if r < final_col_len:
                pos += 1
            r += 1

    # why 0 is replaced by ^.....
    return urllib.unquote(output).replace('^', '0')

