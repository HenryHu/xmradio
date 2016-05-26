import sys
import login
import radio
import init
import info
import re
import logging
import playlist
import localplaylist
import HTMLParser
import random
import song

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtQuick import QQuickView

from PyQt5 import QtCore, QtGui, QtWidgets

logger = logging.getLogger("gui")

ERROR_WAIT = 5
MAX_HISTORY_LEN = 1000  # seriously?
SONG_URL_TEMPLATE = "http://www.xiami.com/song/%s"


class XMTrayIcon(QtWidgets.QSystemTrayIcon):
    def event(self, evt):
        if isinstance(evt, QtGui.QWheelEvent):
            delta = evt.angleDelta()
            if delta.y() < 0:
                self.back.emit()
            elif delta.y() > 0:
                self.forward.emit()
            return True
        return QtWidgets.QSystemTrayIcon.event(self, evt)

    back = QtCore.pyqtSignal()
    forward = QtCore.pyqtSignal()


class StationWrapper(QtCore.QObject):
    def __init__(self, station):
        QtCore.QObject.__init__(self)
        self._station = station
        self._highlight = False

    def _title(self):
        unescaper = HTMLParser.HTMLParser()
        return self.tr("%s fav by %s") % (
            unescaper.unescape(self._station['radio_name']),
            self._station['fav_count'])

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
        self.is_highlight = False

    def _title(self):
        unescaper = HTMLParser.HTMLParser()
        return unescaper.unescape(
            self.tr("%s by %s") % (self._track.get_title(),
                                   self._track.artist))

    def _desc(self):
        unescaper = HTMLParser.HTMLParser()
        return unescaper.unescape(
            self.tr("from %s #%s") % (self._track.album_name,
                                      self._track.song_id))

    def _image_url(self):
        return self._track.pic

    def _highlight(self):
        return self.is_highlight

    changed = QtCore.pyqtSignal()
    title = QtCore.pyqtProperty(unicode, _title, notify=changed)
    desc = QtCore.pyqtProperty(unicode, _desc, notify=changed)
    image_url = QtCore.pyqtProperty(unicode, _image_url, notify=changed)
    highlight = QtCore.pyqtProperty(bool, _highlight, notify=changed)


class ThingsModel(QtCore.QAbstractListModel):
    def __init__(self, things):
        QtCore.QAbstractListModel.__init__(self)
        self._things = things
        self.last_highlight = -1

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._things)

    def data(self, index, role):
        if index.isValid():  # and role == .index('thing'):
            return self._things[index.row()]
        return None

    def append(self, data):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(), self.rowCount())
        self._things.append(data)
        self.endInsertRows()

    def delete(self, idx):
        self.beginRemoveRows(QtCore.QModelIndex(), idx, idx)
        self._things = self._things[:idx] + self._things[(idx + 1):]
        self.endRemoveRows()

    def get(self, index):
        return self._things[index]

    def clear(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.rowCount() - 1)
        self._things = []
        self.endRemoveRows()

    def set_highlight(self, idx):
        if self.last_highlight != -1 and self.last_highlight < len(self._things):
            self._things[self.last_highlight].is_highlight = False
            self._things[self.last_highlight].changed.emit()
            # does not work
            self.dataChanged.emit(self.index(self.last_highlight),
                                  self.index(self.last_highlight))
        if idx != -1 and idx < len(self._things):
            self._things[idx].is_highlight = True
            # does not work
            self.dataChanged.emit(self.index(0), self.index(self.rowCount()))
        # should not need this, but dataChanged has no effect
        self.modelReset.emit()
        self.last_highlight = idx


class MainWin(QtCore.QObject):
    def __init__(self, state, app):
        QtCore.QObject.__init__(self)
        self.state = state
        self.app = app

    # guess-related
    def guess_clicked(self):
        self.mode = "guess"
        self.guess_and_play()

    def guess_and_play(self):
        self.clear_playlist()
        self.fav_model.set_highlight(-1)
        guessed_list = playlist.get_guess_list(self.state)
        guessed_list.visit_player(self.state)
        for track in guessed_list.tracks:
            self.add_track(track)
        self.start_player()

    def random_guess_clicked(self):
        self.mode = "random_guess"
        self.guess_and_play()

    # player control
    def next_clicked(self):
        self.proper_next()

    def prev_clicked(self):
        self.proper_prev()

    def pause_clicked(self):
        self.root_obj.pause()

    def progress_seek(self, x, width):
        if self.duration != 0:
            self.root_obj.seek(x * self.duration / width)

    # local playlist handling
    def load_playlist_clicked(self):
        filename = "playlist.txt"
        my_playlist = localplaylist.LocalPlaylist()
        my_playlist.load(filename)
        self.state['player_path'] = playlist.player_path

        self.fav_model.set_highlight(-1)
        self.clear_playlist()
        for i in xrange(my_playlist.count()):
            track = my_playlist.get(i)
            self.add_track(track)
        self.set_status(self.tr("Playlist loaded from %s") % filename)

        self.mode = 'local_playlist'
        self.start_player()

    def save_playlist_clicked(self):
        filename = "playlist.txt"
        new_playlist = localplaylist.LocalPlaylist()
        for i in xrange(self.playlist_count()):
            track = self.playlist_model.get(i)
            new_playlist.insert(track._track)
        new_playlist.save(filename)
        self.set_status(self.tr("Playlist saved to %s") % filename)

    def clear_playlist(self):
        self.playlist_model.clear()
        self.move_to(0, False)

    # stations
    def load_fav_clicked(self):
        fav_radio_page = 1
        fav_radios = radio.get_fav_radio(self.state, fav_radio_page)

        for fav_radio in fav_radios:
            self.fav_model.append(StationWrapper(fav_radio))

    def station_clicked(self, station, idx):
        self.fav_model.set_highlight(idx)

        _station = station._station
        self.set_status(self.tr("Listening to radio %s (%s)") % (
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
            tracks = radio.get_radio_list(self.state, self.state['radio_type'],
                                          self.state['radio_id'])
        except:
            logger.exception("fail to get list of songs")
            return

        for track in tracks:
            self.add_track(track)

    # playlist
    def song_dblclicked(self, song, idx):
        self.move_to(idx, True)
        self.start_player()

    def song_clicked(self, buttons, song, idx):
        if buttons & QtCore.Qt.RightButton:
            self.playlist_model.delete(idx)
        if self.play_idx == idx:
            if idx == self.playlist_count():
                # deleted last song
                if self.playlist_count() == 0:
                    self.root_obj.stop()
                    self.root_obj.setProgress(0, 0, "")
                else:
                    self.move_to(0, False)
            else:
                self.move_to(idx, False)
            self.start_player()
        elif self.play_idx > idx:
            self.play_idx -= 1
        self.del_history(idx)

    song_id_re = re.compile("/song/([0-9]+)")
    album_id_re = re.compile("/album/([0-9]+)")

    def extract_song_id_from_text(self, text):
        if text.isdigit():
            return [text]
        found_ids = self.song_id_re.findall(text)
        if len(found_ids) > 0:
            return found_ids
        # TODO: handle albums
        return []

    def playlist_paste(self):
        content = self.app.app.clipboard().text()
        song_ids = self.extract_song_id_from_text(content)
        was_empty = self.playlist_count() == 0
        if len(song_ids) > 0:
            for song_id in song_ids:
                track = song.Song.from_id(song_id)
                track.load_info()
                self.playlist_model.append(SongWrapper(track))
        else:
            self.set_status(self.tr("No song found from clipboard"))
        if self.mode == 'stopped' or was_empty:
            self.mode = 'local_playlist'
            self.state['player_path'] = playlist.player_path
            self.start_player()

    def playlist_copy(self):
        song_id = self.playlist_model.get(self.play_idx)._track.song_id
        self.app.app.clipboard().setText(SONG_URL_TEMPLATE % song_id)

    def add_track(self, track):
        self.playlist_model.append(SongWrapper(track))

    def start_player(self):
        if self.play_idx >= self.playlist_count():
            if self.playlist_count() == 0:
                self.set_status(self.tr("Playlist empty"))
            else:
                self.set_status(
                        self.tr("No song to play, can't find song %d") % self.play_idx)
            return
        self.playlist_model.set_highlight(self.play_idx)
        self.main_win.rootObject().setCurrentSong(self.play_idx)
        track = self.playlist_model.get(self.play_idx)._track
        is_hq = info.is_vip(self.state)
        if is_hq:
            try:
                url = track.get_hq_location(self.state)
            except Exception as e:
                logger.warning(
                    "WARNING: error occoured when fetching high quality source: %r" % e)
                url = track.location
                is_hq = False
        else:
            url = track.location

        self.set_status(
                self.tr("Listening to: %s by %s from album %s%s #%s") %
                (track.get_title(), track.artist, track.album_name,
                    self.tr(" [HQ]") if is_hq else "", track.song_id))
        self.set_tray_tooltip(self.tr("Xiami Player - %s by %s from %s") %
                              (track.get_title(), track.artist,
                               track.album_name))
        if track.length:
            # missing? whatever...
            self.duration = int(track.length) * 1000
            self.position = 0
            self.update_position()
        self.main_win.rootObject().setSource(url)
        self.main_win.rootObject().play()

    def playlist_count(self):
        return self.playlist_model.rowCount()

    def move_to(self, idx, add_to_history):
        if add_to_history:
            self.push_history(self.play_idx)
        logger.debug("moving to %d history %r" % (idx, self.history))
        self.play_idx = idx

    def move_to_prev(self, add_to_history=True):
        if self.playlist_count() == 0:
            return
        self.move_to((self.play_idx - 1 + self.playlist_count()) %
                     self.playlist_count(), add_to_history)

    def move_to_next(self, add_to_history=True):
        if self.playlist_count() == 0:
            return
        self.move_to((self.play_idx + 1) %
                     self.playlist_count(), add_to_history)

    def move_to_random(self, add_to_history=True):
        self.move_to(random.randint(0, self.playlist_count() - 1),
                     add_to_history)

    def next_of_tail(self):
        # fetch more or jump back
        if self.mode == "station":
            self.fetch_from_station(self.current_station)
            self.move_to_next()
        else:
            if self.mode == "random_guess":
                self.move_to_random()
            else:
                self.move_to(0, True)

    def proper_next(self):
        if self.play_idx == self.playlist_count() - 1:
            self.next_of_tail()
        else:
            if self.mode == "random_guess":
                self.move_to_random()
            else:
                self.move_to_next()
        self.start_player()

    def proper_prev(self):
        idx = self.pop_history()
        if idx is not None:
            self.move_to(idx, False)
            self.start_player()
        elif self.mode == "random_guess":
            self.move_to_random(False)
        else:
            self.move_to_prev(False)
        self.start_player()

    # player event handling
    def player_duration(self, duration):
        self.duration = duration
        self.progress = 0
        self.update_position()

    def player_stopped(self):
        pass
#        if self.player_ended():
#           # stopped because end
#            self.proper_next()

    def player_status(self, status):
        logger.debug("status: %d" %
                     self.main_win.rootObject().getPlayerStatus())
        if self.player_ended():
            self.proper_next()

    def player_ended(self):
        # 7 = EndOfMedia
        return self.main_win.rootObject().getPlayerStatus() == 7

    def player_position(self, position):
        self.position = position
        self.update_position()

    def player_error(self, error, error_str):
        logger.error("Player error %r %s" % (error, error_str))

    def record_play(self, track, playtype="10"):
        # type 10 -> play from radio
        try:
            info.record_play(self.state, track.song_id, None,
                             info.is_vip(self.state), playtype)
        except:
            logger.exception("fail to record")

    # misc
    def key_pressed(self, key, modifiers):
        if key == ord('V') and modifiers == QtCore.Qt.ControlModifier:
            self.playlist_paste()
        elif key == ord('C') and modifiers == QtCore.Qt.ControlModifier:
            self.playlist_copy()
        elif key == ord('Q') and modifiers == QtCore.Qt.ControlModifier:
            self.exit_clicked()

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
        self.main_win.rootObject().setProgress(self.duration, self.position,
                                               msg)

    def set_status(self, status):
        self.main_win.rootObject().setStatus(status)

    def exit_clicked(self):
        sys.exit(0)

    # history
    def push_history(self, item):
        self.history.append(item)
        if len(self.history) > MAX_HISTORY_LEN:
            self.history = self.history[1:]

    def pop_history(self):
        if len(self.history) > 0:
            ret = self.history[-1]
            self.history = self.history[:-1]
            return ret
        else:
            return None

    def del_history(self, idx):
        # handle deletion
        new_history = []
        for entry in self.history:
            if entry < idx:
                new_history.append(entry)
            elif entry > idx:
                new_history.append(entry - 1)
        self.history = new_history

    # tray functions
    def tray_exit_clicked(self):
        sys.exit(0)

    def tray_activated(self, reason):
        if reason == 3:
            self.main_win.show()
        elif reason == 4:
            self.root_obj.pause()

    def tray_forward(self):
        self.prev_clicked()

    def tray_back(self):
        self.next_clicked()

    def set_tray_tooltip(self, tooltip):
        self.tray_icon.setToolTip(tooltip)

    def create(self):
        # Create the QML user interface.
        self.main_win = QQuickView()
        self.main_win.setTitle(self.tr("Xiami Player"))
        self.main_win.setIcon(QtGui.QIcon("icon.png"))
        self.main_win.setSource(QUrl('main.qml'))
        self.main_win.setResizeMode(QQuickView.SizeRootObjectToView)
        self.main_win.show()

        # Connect signals
        self.root_obj = self.main_win.rootObject()
        self.root_obj.guessClicked.connect(self.guess_clicked)
        self.root_obj.randomGuessClicked.connect(self.random_guess_clicked)
        self.root_obj.loadFavClicked.connect(self.load_fav_clicked)
        self.root_obj.loadPlaylistClicked.connect(self.load_playlist_clicked)
        self.root_obj.savePlaylistClicked.connect(self.save_playlist_clicked)
        self.root_obj.playerStopped.connect(self.player_stopped)
        self.root_obj.nextClicked.connect(self.next_clicked)
        self.root_obj.prevClicked.connect(self.prev_clicked)
        self.root_obj.pauseClicked.connect(self.pause_clicked)
        self.root_obj.playerPosition.connect(self.player_position)
        self.root_obj.playerStatus.connect(self.player_status)
        self.root_obj.progressSeek.connect(self.progress_seek)
        self.root_obj.songDblClicked.connect(self.song_dblclicked)
        self.root_obj.songClicked.connect(self.song_clicked)
        self.root_obj.stationClicked.connect(self.station_clicked)
        self.root_obj.playerError.connect(self.player_error)
        self.root_obj.exitClicked.connect(self.exit_clicked)
        self.root_obj.keyPressed.connect(self.key_pressed)

        self.fav_model = ThingsModel([])
        self.playlist_model = ThingsModel([])
        fav_list = self.root_obj.findChild(QObject, "favStations")
        fav_list.setProperty("model", self.fav_model)
        playlist_list = self.root_obj.findChild(QObject, "playlist")
        playlist_list.setProperty("model", self.playlist_model)

        self.set_status(self.tr("Ready"))
#        rc = self.main_win.rootContext()
#        rc.setContextProperty("controller", self)

        self.tray_menu = QtWidgets.QMenu()
        exit_action = self.tray_menu.addAction(self.tr("Exit"))
        self.tray_icon = XMTrayIcon(QtGui.QIcon("icon.png"))
        self.tray_icon.setToolTip(self.tr("Xiami Player"))
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        exit_action.triggered.connect(self.tray_exit_clicked)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.forward.connect(self.tray_forward)
        self.tray_icon.back.connect(self.tray_back)

        self.play_idx = 0
        self.duration = 0
        self.position = 0
        self.current_station = None
        self.mode = 'stopped'
        self.history = []


class LoginWin(QtCore.QObject):
    def __init__(self, state, app):
        QtCore.QObject.__init__(self)
        self.state = state
        self.app = app

        # Create the QML user interface.
        self.login_win = QQuickView()
        self.login_win.setTitle(self.tr("Xiami Login"))
        self.login_win.setSource(QUrl('login.qml'))
        self.login_win.setResizeMode(QQuickView.SizeRootObjectToView)
        self.login_win.show()

        # Connect signals
        self.root_obj = self.login_win.rootObject()
        self.root_obj.loginClicked.connect(self.login_clicked)
        self.root_obj.exitClicked.connect(self.exit_clicked)

    def set_state(self, msg):
        self.root_obj.setStatus(msg)

    def exit_clicked(self):
        sys.exit(0)

    def login_clicked(self, username, password):
        code = self.root_obj.getVerificationCode()
        if code != "":
            try:
                login.login_with_code(self.state, self.key, code)
            except Exception as e:
                self.set_state(e.message)
                self.root_obj.hideCode()
                return
            self.ok()
        else:
            try:
                ret = login.login(self.state, username, password)
            except Exception as e:
                self.set_state(e.message)
                return
            if not ret[0]:
                with open(login.img_path, 'wb') as imgf:
                    imgf.write(ret[2])
                self.set_state(self.tr("Please enter verification code"))
                self.root_obj.setVerificationImage("file://%s"
                                                   % login.img_path)
                self.key = ret[1]
            else:
                self.ok()

    def ok(self):
        self.login_win.close()
        self.app.auth_ok()


class XiamiPlayer(QtCore.QObject):
    def main(self):
        self.running = False
        self.state = init.init()

        self.app = QtWidgets.QApplication(sys.argv)

        qt_translator = QtCore.QTranslator()
        qt_translator.load("xmradio_%s" % QtCore.QLocale().name(), "lang")
        self.app.installTranslator(qt_translator)

        self.authenticate()

    def auth_ok(self):
        self.main_win = MainWin(self.state, self)
        self.main_win.create()
        self.run()

    def run(self):
        if not self.running:
            self.running = True
            self.app.exec_()

    def authenticate(self):
        if not info.authenticated(self.state):
            self.login_win = LoginWin(self.state, self)
            self.run()
        self.auth_ok()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    main_app = XiamiPlayer()
    main_app.main()
