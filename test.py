import init
import login
import config
import info
import traceback
import time
import urllib2

test_pass = 0
test_total = 0


def test_func(func):
    def test_wrapper(*args, **kwargs):
        print "running test %s" % func.__name__
        global test_total
        test_total += 1
        try:
            func(*args, **kwargs)
            global test_pass
            test_pass += 1
        except Exception as e:
            print "Exception: %r" % e
            if hasattr(e, 'msg'):
                print "msg: %s" % e.msg
            traceback.print_exc()
            raw_input('press enter to continue')

    return test_wrapper


@test_func
def test_song_lyric():
    import song
    track = song.Song()
    track.song_id = config.song_id
    print "lyric:", track.get_lyric()


@test_func
def test_song_hqlocation():
    import radio
    radio.visit_radio(state, config.radio_id)
    tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
    track = tracks[0]
    track.dump_info()
    print "hq location:", track.get_hq_location(state)


@test_func
def test_related_info(state):
    import radio
    radio.visit_radio(state, config.radio_id)
    tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
    track = tracks[0]
    print track.get_related_info(state)


@test_func
def test_similar_artists():
    import radio
    radio.visit_radio(state, config.radio_id)
    tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
    track = tracks[0]
    similar_artists = track.get_similar_artists(4)
    print similar_artists
    assert(len(similar_artists) == 4)
    for artist in similar_artists:
        assert('category' in artist)
        assert('name' in artist)


@test_func
def test_song_url():
    import song
    track = song.Song()
    track.song_id = config.song_id
    print track.get_song_url()
    urllib2.urlopen(track.get_song_url()).read()


@test_func
def test_fav_radio(state):
    import radio
    fav_radios = radio.get_fav_radio(state, 1)
    for fav_radio in fav_radios:
        print "radio name:", fav_radio['radio_name']
        radio.visit_radio(state, fav_radio['radio_id'])
        tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
        tracks[0].dump_info()


@test_func
def test_radio_list(state):
    import radio
    radio.visit_radio(state, config.radio_id)
    for x in xrange(2):
        tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
        for track in tracks:
            track.dump_info()
        time.sleep(5)

state = init.init()
if not info.authenticated(state):
    login.login_console(state, config.username, config.password)
test_radio_list(state)
test_song_lyric()
test_song_hqlocation()
test_related_info(state)
test_similar_artists()
test_song_url()
test_fav_radio(state)

print "============ total test ran: \t%d" % test_total
print "============ test passed:    \t%d" % test_pass
