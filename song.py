import urllib
import urllib2
import json
import logging

lyric_url_temp = "http://www.xiami.com/radio/lyric?sid=%s"
get_hq_url_temp = "http://www.xiami.com/song/gethqsong/sid/%s"

logger = logging.getLogger('song')

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
    def dump_info(self):
        print self.title, self.location

    def get_lyric(self):
        if not hasattr(self, 'song_id'):
            raise Exception("missing song id")
        lyric_url = lyric_url_temp % self.song_id
        lyric = urllib2.urlopen(lyric_url).read()
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

        get_hq_parsed = json.loads(get_hq_rep)

        if not 'status' in get_hq_parsed or get_hq_parsed['status'] != 1:
            raise Exception("fail to get hq url. status = %d" % get_hq_parsed['status'])

        self.hq_location = decrypt_location(get_hq_parsed['location'])
        return self.hq_location

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

