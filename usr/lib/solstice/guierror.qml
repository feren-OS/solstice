import QtQuick 2.6
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3
import org.kde.kirigami 2.13 as Kirigami

ApplicationWindow {
    id: errorwnd
    objectName: "errorwnd"
    visible: true
    width: 25 * Kirigami.Units.gridUnit
    height: 17 * Kirigami.Units.gridUnit
    title: "ERRORTITLE" // Changed by solstice
    property var buttonRowMargin: 5
    property var creationCancel: QtObject { property bool returnHome: true }

    //SIGNALS
    signal dismiss()
    signal openStoreBrowsers()
    signal openStoreID(var storeid)

    Kirigami.Theme.inherit: true
    color: Kirigami.Theme.backgroundColor

    Rectangle {
        id: background
        color: Kirigami.Theme.backgroundColor
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: buttonRow.top
        anchors.bottomMargin: buttonRowMargin
        Kirigami.Theme.colorSet: Kirigami.Theme.View

        ColumnLayout {
            id: genericError
            objectName: "genericError"
            visible: false
            anchors.top: parent.top
            anchors.topMargin: 20
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.right: parent.right
            anchors.rightMargin: 20

            Label {
                id: genericErrorHeader
                objectName: "genericErrorHeader"
                text: "Error" // Changed by feren-storium-ice
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
            Label {
                id: genericErrorSubheader
                objectName: "genericErrorSubheader"
                text: "Error text goes here"
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
        }

        ColumnLayout {
            id: noBrowsersError
            objectName: "noBrowsersError"
            visible: false
            anchors.top: parent.top
            anchors.topMargin: 20
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.right: parent.right
            anchors.rightMargin: 20

            Label {
                id: noBrowsersHeader
                objectName: "noBrowsersHeader"
                text: "No browsers are available for APPTITLE" // Changed by feren-storium-ice
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
            Label {
                id: noBrowsersSubheader
                objectName: "noBrowsersSubheader"
                text: "Unfortunately, APPTITLE cannot currently start as there are no installed browsers that can run it."
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
        }

        ColumnLayout {
            id: unavailableError
            objectName: "unavailableError"
            visible: false
            anchors.top: parent.top
            anchors.topMargin: 20
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.right: parent.right
            anchors.rightMargin: 20

            Label {
                id: unavailableHeader
                objectName: "unavailableHeader"
                text: "APPTITLE is no longer available" // Changed by feren-storium-ice
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
            Label {
                id: unavailableSubheader
                objectName: "unavailableSubheader"
                text: "Unfortunately, APPTITLE has ceased all operations, meaning it is no longer available.\n\nSince APPTITLE is no longer available, would you like to remove APPTITLE from Feren OS?\nNOTE: Once done, you cannot install APPTITLE again."
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                anchors {
                    left: parent.left
                    right: parent.right
                }
            }
            Button {
                text: "More information"
                objectName: "moreInformationBtn"
                icon {
                    name: "internet-web-browser"
                }
                onClicked: dismiss(); //TODO
            }
        }
    }

    RowLayout {
        id: buttonRow
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: buttonRowMargin

        // Browser Unavailable
        Button {
            text: "Get a new browser from Store..."
            objectName: "getStoreBrowserBtn"
            icon {
                name: "feren-store"
                color: Kirigami.Theme.positiveTextColor
            }
            visible: noBrowsersError.visible
            onClicked: openStoreBrowsers();
        }

        // Separator
        Rectangle {
            id: rectangle
            color: "#00000000"
            Layout.fillWidth: true
        }

        // Generic Error
        Button {
            text: "OK"
            visible: genericError.visible
            onClicked: {
                dismiss();
            }
        }
        // Browser Unavailable
        Button {
            text: "OK"
            visible: noBrowsersError.visible
            onClicked: {
                dismiss();
            }
        }
        // Website Unavailable
        Button {
            text: "Dismiss"
            visible: unavailableError.visible
            onClicked: dismiss();
        }
        Button {
            text: "Remove"
            objectName: "deleteProfileBtn"
            icon {
                name: "delete"
                color: Kirigami.Theme.negativeTextColor
            }
            visible: unavailableError.visible
            onClicked: deleteProfile();
        }
    }
}
