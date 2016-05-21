import song
import logging
import os
import codecs

class LocalPlaylist(object):
    def __init__(self):
        self.items = []

    def load(self, filename):
        with open(filename) as inf:
            line = inf.readline()

            while line:
                if '#' in line:
                    line = line.split('#', 1)[0]
                line = line.strip()
                try:
                    song_id = int(line)
                    track = song.Song.from_id(song_info)
                    self.items += [track]
                except:
                    pass

                line = inf.readline()

        if len(self.items) == 0:
            if os.path.exists(filename + os.extsep + "old"):
                self.load(filename + os.extsep + "old")

    def save(self, filename):
        if os.path.exists(filename):
            os.rename(filename, filename + os.extsep + "old")
        with codecs.open(filename, 'w', 'utf-8') as outf:
            for track in self.items:
                outf.write(u"{id} # {title} by {artist}\n".format(id=track.song_id, title=track.title, artist=track.artist))

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
