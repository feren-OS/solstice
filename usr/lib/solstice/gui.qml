import QtQuick 2.6
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3
import org.kde.kirigami 2.13 as Kirigami

ApplicationWindow {
    id: mainwnd
    objectName: "mainwnd"
    visible: true
    width: 1020
    height: 600
    title: "APPTITLE" // Changed by solstice
    property var buttonRowMargin: 5
    property bool lastViewedEditor: false

    //SIGNALS
    signal openProfile(var profileid, var alwaysuse)
    signal gotoProfileEditor(var newprofile, var profileid)
    signal saveProfile()
    signal deleteProfile()

    Kirigami.Theme.inherit: true
    color: Kirigami.Theme.backgroundColor

    SwipeView {
        id: pages
        objectName: "pages"
        interactive: true //FIXME
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: buttonRow.top
        anchors.bottomMargin: buttonRowMargin
        Kirigami.Theme.colorSet: Kirigami.Theme.View

        background: Rectangle {
            color: Kirigami.Theme.backgroundColor
        }

        Item {
            id: profileSelect
            objectName: "profileSelect"

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: profilesHeader
                    objectName: "profilesHeader"
                    text: "Who's using APPTITLE?" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: profilesSubheader
                    objectName: "profilesSubheader"
                    text: "Select your profile from the options below to begin.\nIf you are a new user, hit "+'"'+"Add a profile"+'"'+" instead to begin."
                }
            }

            ScrollView {
                width: parent.width > profiles.width ? profiles.width : parent.width // center the profiles list
                height: profiles.height + Kirigami.Units.gridUnit
                anchors.centerIn: parent
                anchors.verticalCenterOffset: Kirigami.Units.gridUnit * 0.5 // rebalance the centering
                clip: true
                contentWidth: profiles.width
                RowLayout {
                    id: profiles
                    objectName: "profiles"
                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }


                    Repeater {
                        objectName: "profilesRepeater"
                        id: profilesRepeater
                        model: ProfilesModel
                        delegate: Button {
                            id: buttondeleg1
                            Layout.preferredWidth: 7.5 * Kirigami.Units.gridUnit
                            Layout.preferredHeight: 7 * Kirigami.Units.gridUnit
                            onClicked: mainwnd.openProfile(profileid, alwaysUseProfile.checked)

                            ToolTip.visible: pname ? hovered : false
                            ToolTip.text: pname
                            ToolTip.delay: Kirigami.Units.toolTipDelay

                            contentItem: ColumnLayout {
                                Kirigami.Avatar {
                                    name: pname
                                    iconSource: "user-identity"
                                    cache: false
                                    readonly property int size: 3 * Kirigami.Units.gridUnit
                                    implicitWidth: size
                                    implicitHeight: size
                                    anchors.centerIn: parent //FIXME: it misaligns without this
                                }
                                Text {
                                    id: profilelbl
                                    text: pname
                                    font: buttondeleg1.font
                                    width: buttondeleg1.width - Kirigami.Units.gridUnit
                                    horizontalAlignment: Text.AlignHCenter
                                    anchors.horizontalCenter: parent.horizontalCenter //FIXME: again, misaligns without this and the above line
                                    color: Kirigami.Theme.textColor
                                    Kirigami.Theme.inherit: false
                                    Kirigami.Theme.colorSet: Kirigami.Theme.Button
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }


                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }
                }
            }

            CheckBox {
                id: alwaysUseProfile
                objectName: "alwaysUseProfile"
                text: "Always use this profile"
                checked: false
                anchors {
                    bottom: alwaysUseProfileHint.top
                    left: alwaysUseProfileHint.left
                }
                visible: profilesRepeater.count == 1
            }
            Label {
                id: alwaysUseProfileHint
                objectName: "alwaysUseProfileHint"
                text: 'You can manage profiles and select other profiles by right-clicking this application in the Applications Menu and choosing "Manage Profiles...".'
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                font.pointSize: Kirigami.Theme.smallFont.pointSize
                visible: alwaysUseProfile.visible

                anchors {
                    left: parent.left
                    bottom: parent.bottom
                    right: parent.right
                    leftMargin: Kirigami.Units.largeSpacing * 2
                    bottomMargin: Kirigami.Units.largeSpacing * 2
                }
            }
        }

        Item {
            id: profileManager
            objectName: "profileManager"

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: manageHeader
                    objectName: "manageHeader"
                    text: "Manage APPTITLE Profiles" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: manageSubheader
                    objectName: "manageSubheader"
                    text: "Select a profile from the options below to manage it.\nOnce you are done managing profiles, hit Done below."
                }
            }

            ScrollView {
                width: parent.width > profilesToManage.width ? profilesToManage.width : profilesToManage.width // center the profiles list
                height: profilesToManage.height + Kirigami.Units.gridUnit
                anchors.centerIn: parent
                anchors.verticalCenterOffset: Kirigami.Units.gridUnit * 0.5 // rebalance the centering
                clip: true
                contentWidth: profilesToManage.width
                RowLayout {
                    id: profilesToManage
                    objectName: "profilesToManage"
                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }

                    Repeater {
                        id: profileManagerRepeater
                        model: ProfilesModel
                        delegate: Button {
                            id: buttondeleg1
                            Layout.preferredWidth: 7.5 * Kirigami.Units.gridUnit
                            Layout.preferredHeight: 7 * Kirigami.Units.gridUnit
                            onClicked: mainwnd.gotoProfileEditor(false, profileid);

                            ToolTip.visible: pname ? hovered : false
                            ToolTip.text: pname
                            ToolTip.delay: Kirigami.Units.toolTipDelay

                            contentItem: ColumnLayout {
                                Kirigami.Avatar {
                                    name: pname
                                    iconSource: "user-identity"
                                    cache: false
                                    readonly property int size: 3 * Kirigami.Units.gridUnit
                                    implicitWidth: size
                                    implicitHeight: size
                                    anchors.centerIn: parent //FIXME: it misaligns without this
                                }
                                Text {
                                    id: profilelbl
                                    text: pname
                                    font: buttondeleg1.font
                                    width: buttondeleg1.width - Kirigami.Units.gridUnit
                                    horizontalAlignment: Text.AlignHCenter
                                    anchors.horizontalCenter: parent.horizontalCenter //FIXME: again, misaligns without this and the above line
                                    color: Kirigami.Theme.textColor
                                    Kirigami.Theme.inherit: false
                                    Kirigami.Theme.colorSet: Kirigami.Theme.Button
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }


                    Rectangle {
                        color: "#00000000"
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Item {
            id: profileEditor

            ColumnLayout {
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: editProfileHeader
                    objectName: "editProfileHeader"
                    text: "Create a profile" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: editProfileSubheader
                    objectName: "editProfileSubheader"
                    text: "Choose your name, and options for your profile.\nOnce you are done. hit Finish below."
                }
            }

            TextField {
                id: editProfileName
                objectName: "editProfileName"
                horizontalAlignment: Text.AlignRight
                anchors {
                    right: editingAvatar.left
                    verticalCenter: parent.verticalCenter
                    rightMargin: Kirigami.Units.largeSpacing * 2
                }

                Text {
                    text: "Profile name"
                    opacity: 0.5
                    visible: !editProfileName.text
                    anchors {
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        rightMargin: Kirigami.Units.smallSpacing
                    }
                    color: Kirigami.Theme.textColor
                }
            }
            Label {
                id: editProfileNameError
                objectName: "editProfileNameError"
                text: ""
                color: Kirigami.Theme.negativeTextColor
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignRight

                anchors {
                    top: editProfileName.bottom
                    topMargin: Kirigami.Units.smallSpacing
                    left: parent.left
                    right: editProfileName.right
                }
            }

            Kirigami.Avatar {
                Kirigami.Theme.inherit: false //use normal colour set
                id: editingAvatar
                name: editProfileName.text
                color: Kirigami.Theme.backgroundColor
                iconSource: "user-identity"
                cache: false
                readonly property int size: 8 * Kirigami.Units.gridUnit
                width: size
                height: size
                anchors.centerIn: parent
            }

            ColumnLayout {
                anchors {
                    left: editingAvatar.right
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: Kirigami.Units.largeSpacing * 2
                }
                spacing: 0

                CheckBox {
                    id: forceDarkMode
                    objectName: "forceDarkMode"
                    text: "Always use dark mode"
                }
                Label {
                    id: forceDarkModeHint
                    objectName: "forceDarkModeHint"
                    text: "Only works on compatible applications"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                }
                Item { height: Kirigami.Units.smallSpacing }
                CheckBox {
                    id: noCache
                    objectName: "noCache"
                    text: "Disable browser cache"
                }
                Label {
                    id: noCacheHint
                    objectName: "noCacheHint"
                    text: "Worsens load times of websites"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                }
            }
        }

        Item {
            id: browserSelect

            ColumnLayout {
                id: browserSelectCaption
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.left: parent.left
                anchors.leftMargin: 20

                Label {
                    id: browsersHeader
                    objectName: "browsersHeader"
                    text: "Choose a browser to launch APPTITLE" // Changed by feren-storium-ice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                }
                Label {
                    id: browsersSubheader
                    objectName: "browsersSubheader"
                    text: "The browser used to launch this application is missing or has been removed.\nTo continue, please choose a replacement browser below."
                }
            }

            ScrollView {
                width: browsers.width
                anchors.top: browserSelectCaption.bottom //need to do this differently so it doesn't overlap or underlap the caption
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                clip: true
                contentHeight: browsers.height
                ColumnLayout {
                    id: browsers

                }
            }
        }
    }

    RowLayout {
        id: buttonRow
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: buttonRowMargin

        // Profile Manager Buttons
        Button {
            text: "Manage bonuses in Store... (dummy)"
            icon {
                name: "feren-store"
            }
            visible: pages.currentIndex == 1 ? true : false
        }
        // Profile Editor Buttons
        Button {
            text: "Cancel"
            icon {
                name: "dialog-cancel"
            }
            visible: pages.currentIndex == 2 ? true : false
            enabled: profilesRepeater.count > 0 ? true : false
            onClicked: {
                if (lastViewedEditor == true) {
                    pages.currentIndex = 1;
                    profileManager.forceActiveFocus(true);
                } else {
                    pages.currentIndex = 0;
                    profileSelect.forceActiveFocus(true);
                }
            }
        }
        Button {
            text: "Delete profile"
            objectName: "deleteProfileBtn"
            icon {
                name: "delete"
                color: Kirigami.Theme.negativeTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
            onClicked: deleteProfile();
        }

        // Separator
        Rectangle {
            id: rectangle
            color: "#00000000"
            Layout.fillWidth: true
        }
        // Browser Select Buttons
        Button {
            text: "Confirm (dummy)"
            icon {
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 3 ? true : false
        }
        // Profile Select Buttons
        Button { //also Profile Management in this button's case
            text: "Add a profile..."
            icon {
                name: "list-add"
            }
            visible: pages.currentIndex == 0 || pages.currentIndex == 1 ? true : false
            onClicked: gotoProfileEditor(true, "");
        }
        Button {
            text: "Manage profiles..."
            icon {
                color: Kirigami.Theme.neutralTextColor
            }
            visible: pages.currentIndex == 0 ? true : false
            onClicked: {
                pages.currentIndex = 1;
                lastViewedEditor = true;
                profileManager.forceActiveFocus(true);
            }
        }
        // Profile Management Buttons
        Button {
            text: "Done"
            objectName: "exitManagerBtn"
            id: exitManagerBtn
            icon {
                name: "dialog-apply"
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 1 ? true : false
            onClicked: {
                pages.currentIndex = 0;
                lastViewedEditor = false;
                profileSelect.forceActiveFocus(true);
            }
        }
        // Profile Editor Buttons
        Button {
            objectName: "editorDoneBtn"
            text: "Finish"
            icon {
                name: "dialog-apply"
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
            onClicked: mainwnd.saveProfile();
        }
    }
}
