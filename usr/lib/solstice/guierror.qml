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
    property var buttonRowMargin: 5
    maximumHeight: height
    maximumWidth: width
    minimumHeight: height
    minimumWidth: width

    //SIGNALS
    signal dismiss()
    signal openStoreBrowsers()
    signal openStoreID()
    signal unavailMoreInformation()

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
                text: "GENERICERRORHEADER" // Changed by solstice
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
            }
            Label {
                id: genericErrorSubheader
                objectName: "genericErrorSubheader"
                text: "GENERICERRORSUBHEADER"
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
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
                text: "NOBROWSERSHEADER"
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
            }
            Label {
                id: noBrowsersSubheader
                objectName: "noBrowsersSubheader"
                text: "NOBROWSERSSUBHEADER"
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
            }

            Rectangle {
                color: "#00000000"
                height: Kirigami.Units.largeSpacing
            }
            ColumnLayout {
                objectName: "browserSubstitute"
                Label {
                    objectName: "browserSubstituteTitle"
                    text: "BROWSERSUBSTITUTETITLE"
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.2
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: errorwnd.width - 40
                }
                Label {
                    objectName: "browserSubstituteDesc"
                    text: "BROWSERSUBSTITUTEDESCRIPTION"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: errorwnd.width - 40
                }
                Button {
                    text: "VIEWBROWSERBUTTON"
                    objectName: "getStoreBrowserBtn"
                    icon {
                        name: "feren-store"
                        color: Kirigami.Theme.positiveTextColor
                    }
                    //TODO: onClicked
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
                text: "NOTAVAILABLEHEADER"
                font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
            }
            Label {
                id: unavailableSubheader
                objectName: "unavailableSubheader"
                text: "NOTAVAILABLESUBHEADER"
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                Layout.preferredWidth: errorwnd.width - 40
            }
            Button {
                text: "MOREINFORMATIONBTN"
                objectName: "moreInformationBtn"
                icon {
                    name: "internet-web-browser"
                }
                onClicked: unavailMoreInformation();
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
            text: "GETSTOREBROWSERSBTN"
            objectName: "getStoreBrowsersBtn"
            icon {
                name: "feren-store"
            }
            visible: noBrowsersError.visible && storeAvailable && canEdit
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
            text: "GENERICOK"
            objectName: "genericOk"
            visible: genericError.visible
            onClicked: {
                dismiss();
            }
        }
        // Browser Unavailable
        Button {
            text: "UNAVAILABLEOK"
            objectName: "unavailableOk"
            visible: noBrowsersError.visible
            onClicked: {
                dismiss();
            }
        }
        // Website Unavailable
        Button {
            text: "UNAVAILABLEDISMISS"
            objectName: "unavailableDismiss"
            visible: unavailableError.visible
            onClicked: dismiss();
        }
        Button {
            text: "UNINSTALLSTOREBTN"
            objectName: "uninstallStoreBtn"
            icon {
                name: "delete"
                color: Kirigami.Theme.negativeTextColor
            }
            visible: unavailableError.visible && storeAvailable && canEdit
            onClicked: openStoreID();
        }
    }
}
