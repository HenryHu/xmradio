import login
import radio
import init
import info
import sys
import time
import os
import logging

logging.basicConfig(level=logging.WARN)

state = init.init()
if not info.authenticated(state):
    username = raw_input("username: ")
    import getpass
    password = getpass.getpass("password: ")
    login.login_console(state, username, password)

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
    sel = raw_input("Select radio station [1-%d], [n] for next page, [p] for prev page:" % (len(fav_radios)))
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
        else:
            print("invalid selection")

radio_id = sel_radio['radio_id']
print("Listening to radio %s (%s)" % (sel_radio['radio_id'], sel_radio['object_id']))
radio.visit_radio(state, radio_id)
while True:
    tracks = radio.get_radio_list(state, state['radio_type'], state['radio_id'])
    for track in tracks:
        print("Listening to: %s by %s from album %s" % (track.title, track.artist, track.album_name))
        url = track.get_hq_location(state)
        os.system("mplayer -really-quiet -cache 1024 -cache-min 50 %s" % url)
        time.sleep(1)


