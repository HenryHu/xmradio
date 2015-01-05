import login
import radio
import init
import info
import sys
import time
import os
import logging
import playlist


logger = logging.getLogger("console")

ERROR_WAIT = 5

def play_track(state, track):
    print("Listening to: %s by %s from album %s" % (track.title, track.artist, track.album_name))
    is_hq = info.is_vip(state)
    if is_hq:
        try:
            url = track.get_hq_location(state)
        except Exception as e:
            print("WARNING: error occoured when fetching high quality source: %r" % e)
            url = track.location
    else:
        url = track.location
    try:
        info.add_stat(state, info.STAT_BEGIN, track.song_id)
    except Exception as e:
        print("WARNING: error occoured when reporting stat: %r" % e)
    os.system("mplayer -prefer-ipv4 -really-quiet -cache 10240 -cache-min 10 %s" % url)
    try:
        info.add_stat(state, info.STAT_END, track.song_id)
    except Exception as e:
        print("WARNING: error occoured when reporting stat: %r" % e)

def play_guessed_list(state):
    guessed_list = playlist.get_guess_list(state)
    guessed_list.visit_player(state)
    while True:
        for track in guessed_list.tracks:
            play_track(state, track)
            info.record_play(state, track.song_id, "guess", info.is_vip(state), None)
            time.sleep(1)

def play_radio(state, radio_id):
    radio.visit_radio(state, radio_id)
    while True:
        try:
            tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
        except:
            logger.exception("fail to get list of songs")
            time.sleep(ERROR_WAIT)
            continue
        for track in tracks:
            play_track(state, track)
            # type 10 -> play from radio
            info.record_play(state, track.song_id, None, info.is_vip(state), "10")
            time.sleep(1)

def select_radio_station(state):
    fav_radio_page = 1
    sel_radio = None

    while True:
        try:
            print("Favourite radio stations, page %d:" % fav_radio_page)
            fav_radios = radio.get_fav_radio(state, fav_radio_page)
            if len(fav_radios) == 0:
                raise Exception("no station available")
        except Exception as e:
            if fav_radio_page == 1:
                print("can't retrieve list of favourite radio stations: %r" % e)
                sys.exit(1)
            else:
                fav_radio_page -= 1
                continue
        idx = 1
        for fav_radio in fav_radios:
            print("Radio %d: %s fav by %s people" % (idx, fav_radio['radio_name'], fav_radio['fav_count']))
            print("    %s" % (fav_radio['description']))
            idx += 1
        sel = raw_input("Select radio station [1-%d], [n] for next page, [p] for prev page, [g] for guessed playlist:" % (len(fav_radios)))
        if sel.isdigit():
            sel = int(sel)
            if sel < 1 or sel > len(fav_radios):
                print("invalid selection: out of range")
                continue
            sel_radio = fav_radios[sel - 1]
            break
        else:
            if sel[0].lower() == 'n':
                fav_radio_page += 1
            elif sel[0].lower() == 'p':
                if fav_radio_page == 1:
                    print("invalid operation: at first page")
                    continue
                fav_radio_page -= 1
            elif sel[0].lower() == 'g':
                return 'g'
            else:
                print("invalid selection")

    print("Listening to radio %s (%s)" % (sel_radio['radio_id'], sel_radio['object_id']))

    return sel_radio['radio_id']

def authenticate(state):
    if not info.authenticated(state):
        username = raw_input("username: ")
        import getpass
        password = getpass.getpass("password: ")
        login.login_console(state, username, password)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    state = init.init()
    authenticate(state)
    radio_id = select_radio_station(state)
    if radio_id == 'g':
        play_guessed_list(state)
    else:
        play_radio(state, radio_id)
