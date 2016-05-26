import console
import localplaylist
import init
import logging
import playlist


def play(filename):
    state = init.init()
    console.authenticate(state)
    my_playlist = localplaylist.LocalPlaylist()
    my_playlist.load(filename)
    state['player_path'] = playlist.player_path

    while True:
        for i in xrange(my_playlist.count()):
            song = my_playlist.get(i)
            console.play_track(state, song)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    play('playlist.txt')
