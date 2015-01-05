import song
import logging

class LocalPlaylist(object):
    def __init__(self):
        self.items = []

    def load(self, filename):
        with open(filename) as inf:
            line = inf.readline()

            while line:
                try:
                    song_id = int(line)
                    song_info = {'song_id': str(song_id)}
                    track = song.Song(song_info)
                    self.items += [track]
                except:
                    pass

                line = inf.readline()

    def count(self):
        return len(self.items)

    def get(self, idx):
        track = self.items[idx]
        try:
            track.load_info()
        except:
            logging.exception("error loading info")
        return track
