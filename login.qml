import QtQuick 2.0
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.3

Rectangle {
    id: rectangle1
    //    title: qsTr("Login")
    width: 480; height: 200

    signal loginClicked(string username, string password)
    signal exitClicked()

    function getVerificationCode() {
        var ret = eCode.text
        eCode.text = ""
        return ret
    }

    function setVerificationImage(path) {
        imgCode.source = ""
        imgCode.source = path
        imgCode.visible = true
        eCode.visible = true
        lblCode.visible = true
    }

    function hideCode() {
        imgCode.visible = false
        eCode.visible = false
        lblCode.visible = false
    }

    function setStatus(msg) {
        tState.text = msg
    }

    Text {
        id: text1
        x: 78
        y: 8
        text: qsTr("Please login")
        anchors.horizontalCenterOffset: 0
        font.pointSize: 11
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Text {
        id: tState
        x: 61
        y: 102
        text: qsTr("Ready")
        font.pixelSize: 12
    }

    Grid {
        id: grid1
        x: 23
        y: 34
        width: 402
        height: 62
        anchors.horizontalCenterOffset: 0
        anchors.horizontalCenter: parent.horizontalCenter
        rows: 2
        columns: 2

        Text {
            id: lblUsername
            width: 100
            text: qsTr("Username:")
            font.pointSize: 11

        }

        TextField {
            id: eUsername
            width: 300
            text: ""
            clip: true
            font.pointSize: 10
        }

        Text {
            id: lblPassword
            width: 100
            text: qsTr("Password:")
            font.pointSize: 11
        }

        TextField {
            id: ePassword
            width: 300
            text: ""
            clip: true
            font.pointSize: 10
            inputMethodHints: Qt.ImhHiddenText
            echoMode: TextInput.Password
        }
    }

    Rectangle {
        id: rectangle2
        x: 94
        y: 155
        width: 270
        height: 45
        color: "#ffffff"
        anchors.horizontalCenterOffset: 0
        anchors.horizontalCenter: parent.horizontalCenter

        Button {
            id: bLogin
            x: 8
            y: 0
            text: qsTr("Login")
            onClicked: loginClicked(eUsername.text, ePassword.text)
        }

        Button {
            id: bExit
            x: 186
            y: 0
            text: qsTr("Exit")
            onClicked: exitClicked()
        }
    }

    Text {
        id: lblCode
        x: 221
        y: 121
        text: qsTr("Code:")
        visible: false
    }

    TextField {
        id: eCode
        x: 284
        y: 115
        placeholderText: qsTr("Code")
        visible: false
    }

    Image {
        id: imgCode
        x: 105
        y: 117
        cache: false
        width: 103
        height: 32
        source: ""
        visible: false
    }
}
