import song
import logging
import os
import codecs

logger = logging.getLogger("localplaylist")


class LocalPlaylist(object):
    def __init__(self):
        self.items = []

    def load(self, filename):
        with open(filename) as inf:
            line = inf.readline()

            while line:
                desc = ""
                if '#' in line:
                    (line, desc) = line.split('#', 1)
                line = line.strip()
                try:
                    track = song.Song.from_encoded(desc.split(' ')[-1])
                    if track is None:
                        track = song.Song.from_id(int(line))
                    self.items += [track]
                except:
                    logger.exception("line %s error(%s)" % (line, filename))

                line = inf.readline()

        if len(self.items) == 0:
            if os.path.exists(filename + os.extsep + "old"):
                self.load(filename + os.extsep + "old")

    def save(self, filename):
        if os.path.exists(filename):
            os.rename(filename, filename + os.extsep + "old")
        with codecs.open(filename, 'w', 'utf-8') as outf:
            for track in self.items:
                outf.write(u"{id} # {title} by {artist} {info}\n"
                           .format(id=track.song_id, title=track.title,
                                   artist=track.artist, info=track.encode()))

    def count(self):
        return len(self.items)

    def get(self, idx):
        track = self.items[idx]
        try:
            track.load_info()
        except:
            logger.exception("error loading info")
        return track

    def insert(self, track, idx=0):
        self.items.insert(idx, track)

    def append(self, track):
        self.items += [track]
