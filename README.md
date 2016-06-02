# xmradio

Xiami Radio API & Demo Application

## Modules

* login Login into Xiami service. Ask for verification code if required.
* song Song information retrieval. Supports high quality URL retrieval.
* radio Get information of radio stations & list of favourite radio stations.
* info Process user information.
* init Initialization / Finalization

## Demo

Run `console.py`

## GUI
Dependencies:
* qtquick, pyQt  The GUI uses PyQt5 and QtQuick to draw the interface and handle user input
* QtMultimedia It uses the MediaPlayer widget in QtQuick for playback
* gstreamer1 For audio playback, used by QtMultimedia
* gstreamer-neon  For streaming HTTP audio

### install the following packages
* Ubuntu / Debian:
`gstreamer1.0-plugins-good gstreamer-plugins-base gstreamer1.0-pluseaudio libgstreamer-plugins-bad1.0-0 libqt5gstreamer-1.0-0 python-pyqt5 python-pyqt5.qtmultimedia python-pyqt5.qtquick python-dbus.mainloop.pyqt5`
* FreeBSD:
Notice: py-qt5-qtquick is still missing from the ports.
`py27-qt5-core py27-qt5-gui py27-qt5-multimedia py27-qt5-qml py27-qt5-dbus py27-qt5-dbussupport gstreamer1-plugins-neon`

Run `gui.py`

## TODO

* Modify the list of favourite radio stations
* Other functions
