import logging
import urllib2
import json
import song

logger = logging.getLogger("playlist")

playlist_url_temp = "http://www.xiami.com/song/playlist/id/%s/type/%s/cat/json"
playlist_player_url_temp = "http://www.xiami.com/play?ids=/song/playlist/id/%s/type/%s"
player_path = "http://ima.xiami.com/static/swf/seiya/1.4/player.swf"


class Playlist(object):
    def __init__(self, parsed, id_, type_):
        self.type = parsed['type']
        self.last_song_id = parsed['lastSongId']
        self.tracks = []
        for track in parsed['trackList']:
            self.tracks.append(song.Song(track))
        self.playlist_id = id_
        self.playlist_type = type_

    def visit_player(self, state):
        player_url = playlist_player_url_temp % (self.playlist_id, self.playlist_type)
        player_page = urllib2.urlopen(player_url).read()
        logger.debug("player page: %s" % player_page)
        # player is inserted by scripts, hard to get location
        state['player_path'] = player_path


def get_playlist(state, playlist_id, playlist_type):
    playlist_url = playlist_url_temp % (playlist_id, playlist_type)
    playlist_data = urllib2.urlopen(playlist_url).read()
    playlist_parsed = json.loads(playlist_data)
    if 'status' not in playlist_parsed or not playlist_parsed['status']:
        if 'message' in playlist_parsed:
            raise Exception(u"fail to fetch playlist, msg: %s" %
                            playlist_parsed['message'])
        else:
            raise Exception("fail to fetch playlist")
    playlist_parsed = playlist_parsed['data']
    return Playlist(playlist_parsed, playlist_id, playlist_type)


def get_guess_list(state):
    return get_playlist(state, '1', '9')

if __name__ == '__main__':
    import init
    state = init.init()
    playlist = get_guess_list(state)
    playlist.visit_player(state)
    print "=== Today's guess ==="
    for track in playlist.tracks:
        print "%s by %s" % (track.title, track.artist)
