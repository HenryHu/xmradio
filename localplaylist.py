import song
import logging
import os

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

    def save(self, filename):
        if os.path.exists(filename):
            os.rename(filename, filename + os.extsep + "old")
        with open(filename, 'w') as outf:
            for track in self.items:
                outf.write("%s\n" % (track.song_id))

    def count(self):
        return len(self.items)

    def get(self, idx):
        track = self.items[idx]
        try:
            track.load_info()
        except:
            logging.exception("error loading info")
        return track

    def insert(self, track, idx = 0):
        self.items.insert(idx, track)

    def append(self, track):
        self.items += [track]
