import sys
import login
import radio
import init
import info
import sys
import time
import os
import logging
import playlist
import HTMLParser
import random
from functools import partial

from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtProperty
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQuick import QQuickView

from PyQt5 import QtCore, QtGui, QtWidgets

logger = logging.getLogger("gui")

ERROR_WAIT = 5

class StationWrapper(QtCore.QObject):
    def __init__(self, station):
        QtCore.QObject.__init__(self)
        self._station = station
        self._highlight = False

    def _title(self):
        unescaper = HTMLParser.HTMLParser()
        return "%s fav by %s" % (unescaper.unescape(self._station['radio_name']), self._station['fav_count'])

    def _desc(self):
        unescaper = HTMLParser.HTMLParser()
        return unescaper.unescape(self._station['description'])

    def _highlight(self):
        return self._highlight

    changed = QtCore.pyqtSignal()
    title = QtCore.pyqtProperty(unicode, _title, notify=changed)
    desc = QtCore.pyqtProperty(unicode, _desc, notify=changed)
    highlight = QtCore.pyqtProperty(bool, _highlight, notify=changed)

class SongWrapper(QtCore.QObject):
    def __init__(self, track):
        QtCore.QObject.__init__(self)
        self._track = track
        self._highlight = False

    def _title(self):
        unescaper = HTMLParser.HTMLParser()
        return unescaper.unescape("%s by %s" % (self._track.title, self._track.artist))

    def _desc(self):
        unescaper = HTMLParser.HTMLParser()
        return unescaper.unescape("from %s #%s" % (self._track.album_name, self._track.song_id))

    def _highlight(self):
        return self._highlight

    changed = QtCore.pyqtSignal()
    title = QtCore.pyqtProperty(unicode, _title, notify=changed)
    desc = QtCore.pyqtProperty(unicode, _desc, notify=changed)
    highlight = QtCore.pyqtProperty(bool, _highlight, notify=changed)

class ThingsModel(QtCore.QAbstractListModel):
    def __init__(self, things):
        QtCore.QAbstractListModel.__init__(self)
        self._things = things
        self.last_highlight = -1

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._things)

    def data(self, index, role):
        if index.isValid(): # and role == ThingListModel.COLUMNS.index('thing'):
            return self._things[index.row()]
        return None

    def append(self, data):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self._things.append(data)
        self.endInsertRows()

    def get(self, index):
        return self._things[index]

    def clear(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.rowCount() - 1)
        self._things = []
        self.endRemoveRows()

    def set_highlight(self, idx):
        if self.last_highlight != -1 and self.last_highlight < len(self._things):
            self._things[self.last_highlight]._highlight = False
            self.dataChanged.emit(
                    self.index(self.last_highlight), self.index(self.last_highlight))
        self._things[idx]._highlight = True
        self.dataChanged.emit(self.index(idx), self.index(idx))
        self.last_highlight = idx

def authenticate(state):
    if not info.authenticated(state):
        username = raw_input("username: ")
        import getpass
        password = getpass.getpass("password: ")
        login.login_console(state, username, password)

class MainWin(QtCore.QObject):
    def guess_clicked(self):
        self.mode = "guess"
        self.guess_and_play()

    def guess_and_play(self):
        self.clear_playlist()
        guessed_list = playlist.get_guess_list(self.state)
        guessed_list.visit_player(self.state)
        for track in guessed_list.tracks:
            self.add_track(track)
        self.start_player()

    def random_guess_clicked(self):
        self.mode = "random_guess"
        self.guess_and_play()

    def next_clicked(self):
        self.proper_next()
        self.start_player()

    def prev_clicked(self):
        self.move_to_prev()
        self.start_player()

    def pause_clicked(self):
        self.root_obj.pause()

    def player_duration(self, duration):
        self.duration = duration
        self.progress = 0
        self.update_position()

    def load_fav_clicked(self):
        fav_radio_page = 1
        fav_radios = radio.get_fav_radio(self.state, fav_radio_page)

        for fav_radio in fav_radios:
            self.fav_model.append(StationWrapper(fav_radio))

    def clear_playlist(self):
        self.playlist_model.clear()
        self.play_idx = 0

    @QtCore.pyqtSlot(QtCore.QObject)
    def station_clicked(self, station):
        idx = self.root_obj.currentStation()
        self.fav_model.set_highlight(idx)

        _station = station._station
        self.set_status("Listening to radio %s (%s)" % (
            _station['radio_id'], _station['object_id']))
        self.current_station = _station
        self.mode = "station"

        radio_id = _station['radio_id']
        radio.visit_radio(self.state, radio_id)
        self.clear_playlist()
        self.fetch_from_station(_station)
        self.start_player()

    def fetch_from_station(self, station):
        try:
            tracks = radio.get_radio_list(self.state,
                    self.state['radio_type'], self.state['radio_id'])
        except:
            logger.exception("fail to get list of songs")
            return

        for track in tracks:
            self.add_track(track)

    @QtCore.pyqtSlot(QtCore.QObject)
    def song_clicked(self, song):
        idx = self.main_win.rootObject().currentSong()
        self.play_idx = idx
        self.start_player()

    def add_track(self, track):
        self.playlist_model.append(SongWrapper(track))

    def start_player(self):
        self.playlist_model.set_highlight(self.play_idx)
        self.main_win.rootObject().setCurrentSong(self.play_idx)
        track = self.playlist_model.get(self.play_idx)._track
        is_hq = info.is_vip(self.state)
        if is_hq:
            try:
                url = track.get_hq_location(self.state)
            except Exception as e:
                logger.warning("WARNING: error occoured when fetching high quality source: %r" % e)
                url = track.location
                is_hq = False
        else:
            url = track.location

        self.set_status("Listening to: %s by %s from album %s%s #%s" % (track.title, track.artist, track.album_name, " [HQ]" if is_hq else "", track.song_id))
        if track.length:
            # missing? whatever...
            self.duration = int(track.length) * 1000
            self.position = 0
            self.update_position()
        self.main_win.rootObject().setSource(url)
        self.main_win.rootObject().play()

    def playlist_count(self):
        return self.playlist_model.rowCount()

    def move_to_prev(self):
        self.play_idx = (self.play_idx - 1 + self.playlist_count()) % self.playlist_count()

    def move_to_next(self):
        self.play_idx = (self.play_idx + 1) % self.playlist_count()

    def time_ms_to_str(self, time_ms):
        time_s = int(time_ms / 1000)
        time_h = time_s / 3600
        time_s = time_s % 3600
        time_m = time_s / 60
        time_s = time_s % 60
        if time_h > 0:
            return "%02d:%02d:%02d" % (time_h, time_m, time_s)
        else:
            return "%02d:%02d" % (time_m, time_s)

    def update_position(self):
        cur_pos = self.time_ms_to_str(self.position)
        max_pos = self.time_ms_to_str(self.duration)
        msg = "%s (%s)" % (cur_pos, max_pos)
        self.main_win.rootObject().setProgress(self.duration, self.position, msg)

    def move_to_random(self):
        self.play_idx = random.randint(0, self.playlist_count() - 1)

    def next_of_tail(self):
        # fetch more or jump back
        if self.mode == "station":
            self.fetch_from_station(self.current_station)
            self.move_to_next()
            self.start_player()
        else:
            if self.mode == "random_guess":
                self.move_to_random()
            else:
                self.play_idx = 0
            self.start_player()

    def proper_next(self):
        if self.play_idx == self.playlist_count() - 1:
            self.next_of_tail()
        else:
            if self.mode == "random_guess":
                self.move_to_random()
            else:
                self.move_to_next()
            self.start_player()

    def player_stopped(self):
        pass
#        if self.player_ended():
            # stopped because end
#            self.proper_next()

    def player_status(self, status):
        logger.debug("status: %d" % self.main_win.rootObject().getPlayerStatus())
        if self.player_ended():
            self.proper_next()

    def player_ended(self):
        return self.main_win.rootObject().getPlayerStatus() == 7

    def player_position(self, position):
        self.position = position
        self.update_position()

    def record_play(self, track, playtype="10"):
        # type 10 -> play from radio
        try:
            info.record_play(self.state, track.song_id, None, info.is_vip(self.state), playtype)
        except:
            logger.exception("fail to record")

    def set_status(self, status):
        self.main_win.rootObject().setStatus(status)

    def main(self):
        self.state = init.init()
        authenticate(self.state)

        app = QGuiApplication(sys.argv)

        # Create the QML user interface.
        self.main_win = QQuickView()
        self.main_win.setTitle("Xiami Player")
        self.main_win.setSource(QUrl('main.qml'))
        self.main_win.setResizeMode(QQuickView.SizeRootObjectToView)
        self.main_win.show()

        # Connect signals
        self.root_obj = self.main_win.rootObject()
        self.root_obj.guessClicked.connect(self.guess_clicked)
        self.root_obj.randomGuessClicked.connect(self.random_guess_clicked)
        self.root_obj.loadFavClicked.connect(self.load_fav_clicked)
        self.root_obj.playerStopped.connect(self.player_stopped)
        self.root_obj.nextClicked.connect(self.next_clicked)
        self.root_obj.prevClicked.connect(self.prev_clicked)
        self.root_obj.pauseClicked.connect(self.pause_clicked)
        self.root_obj.playerPosition.connect(self.player_position)
        self.root_obj.playerStatus.connect(self.player_status)

        self.fav_model = ThingsModel([])
        self.playlist_model = ThingsModel([])
        fav_list = self.root_obj.findChild(QObject, "favStations")
        fav_list.setProperty("model", self.fav_model)
        playlist_list = self.root_obj.findChild(QObject, "playlist")
        playlist_list.setProperty("model", self.playlist_model)
        self.play_idx = 0

        self.set_status("Ready")
        rc = self.main_win.rootContext()
        rc.setContextProperty("controller", self)

        self.duration = 0
        self.position = 0
        self.current_station = None

        app.exec_()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    main_win = MainWin()
    main_win.main()
