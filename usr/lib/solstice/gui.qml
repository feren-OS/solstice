import QtQuick 2.6
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3
import org.kde.kirigami 2.13 as Kirigami

ApplicationWindow {
    id: mainwnd
    objectName: "mainwnd"
    visible: true
    width: 56 * Kirigami.Units.gridUnit
    height: 32 * Kirigami.Units.gridUnit
    minimumWidth: 29 * Kirigami.Units.gridUnit
    minimumHeight: 21 * Kirigami.Units.gridUnit
    title: "APPTITLE" // Changed by solstice
    property var buttonRowMargin: 5
    property bool lastViewedEditor: false
    property string selectedBrowser: ""

    //SIGNALS
    signal openProfile(var profileid, var alwaysuse)
    signal gotoProfileEditor(var newprofile, var profileid)
    signal saveProfile()
    signal deleteProfile()
    signal gotoBrowserSelect()
    signal setBrowser(var newbrowser)

    Kirigami.Theme.inherit: true
    color: Kirigami.Theme.backgroundColor

    SwipeView {
        id: pages
        objectName: "pages"
        interactive: false
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
                    text: "PROFILESHEADER" // Changed by solstice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
                Label {
                    id: profilesSubheader
                    objectName: "profilesSubheader"
                    text: "PROFILESSUBHEADER"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
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
                text: "ALWAYSUSEPROFILE" // Changed by Solstice
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
                text: "ALWAYSUSEPROFILEHINT" // Changed by Solstice
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
                    text: "MANAGEHEADER"
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
                Label {
                    id: manageSubheader
                    objectName: "manageSubheader"
                    text: "MANAGESUBHEADER"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
            }

            ScrollView {
                width: parent.width > profilesToManage.width ? profilesToManage.width : parent.width // center the profiles list
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
                    text: "EDITPROFILEHEADER"
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
                Label {
                    id: editProfileSubheader
                    objectName: "editProfileSubheader"
                    text: "EDITPROFILESUBHEADER"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
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
                    objectName: "editProfileNameHint"
                    text: "EDITPROFILENAMEHINT" // Changed by solstice
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

                // Item { height: Kirigami.Units.smallSpacing }
                CheckBox {
                    id: noCache
                    objectName: "noCache"
                    text: "NOCACHE"
                }
                Label {
                    id: noCacheHint
                    objectName: "noCacheHint"
                    text: "NOCACHEHINT"
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
                    text: "BROWSERSELECTTEXT" // Changed by solstice
                    font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.6
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
                Label {
                    id: browsersSubheader
                    objectName: "browsersSubheader"
                    text: "BROWSERSELECTSUBTEXT"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    Layout.preferredWidth: mainwnd.width - 40
                }
            }

            Item {
                anchors.top: browserSelectCaption.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.topMargin: Kirigami.Units.smallSpacing

                ScrollView {
                    width: browsersToSelect.width + Kirigami.Units.gridUnit
                    height: parent.height > browsersToSelect.height ? browsersToSelect.height : parent.height // center the browsers list
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: Kirigami.Units.gridUnit * 0.5 // rebalance the centering
                    clip: true
                    contentHeight: browsersToSelect.height
                    ButtonGroup { id: browserSelectRadios }
                    ColumnLayout {
                        id: browsersToSelect
                        objectName: "browsersToSelect"
                        spacing: Kirigami.Units.largeSpacing
                        Rectangle {
                            color: "#00000000"
                            Layout.fillHeight: true
                        }

                        Repeater {
                            id: browserSelectRepeater
                            model: BrowsersModel
                            delegate: RowLayout {
                                spacing: 0
                                RadioButton {
                                    id: browserDelegRadio
                                    onCheckedChanged: mainwnd.selectedBrowser = browserid
                                    ButtonGroup.group: browserSelectRadios
                                    enabled: available
                                    checked: prechecked
                                }
                                Kirigami.Icon {
                                    source: bricon
                                    anchors.margins: Kirigami.Units.mediumSpacing
                                    implicitHeight: Kirigami.Units.iconSizes.large
                                    implicitWidth: Kirigami.Units.iconSizes.large
                                    MouseArea { //expands hitbox
                                        anchors.fill: parent
                                        onClicked: { browserDelegRadio.checked = available }
                                    }
                                }
                                Item { width: Kirigami.Units.largeSpacing }
                                ColumnLayout {
                                    spacing: 0
                                    Layout.preferredWidth: Kirigami.Units.gridUnit * 23
                                    Label {
                                        wrapMode: Text.WordWrap
                                        elide: Text.ElideRight
                                        text: brname
                                        Layout.preferredWidth: parent.width
                                    }
                                    Label {
                                        text: desc
                                        wrapMode: Text.WordWrap
                                        elide: Text.ElideRight
                                        font.pointSize: Kirigami.Theme.smallFont.pointSize
                                        visible: text
                                        Layout.preferredWidth: parent.width
                                        //NOTE: Layout.preferredWidth is the only way to seemingly make
                                        // this work in *Layout
                                    }
                                    MouseArea { //expands hitbox
                                        anchors.fill: parent
                                        onClicked: { browserDelegRadio.checked = available }
                                    }
                                }
                            }
                        }


                        Rectangle {
                            color: "#00000000"
                            Layout.fillHeight: true
                        }
                    }
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
            objectName: "manageBonusesBtn"
            text: "MANAGEBONUSESBTN" // Changed by solstice
            icon {
                name: "feren-store"
            }
            visible: pages.currentIndex == 1 ? fromStore && storeAvailable : false
            enabled: bonusesAvailable
            //TODO: OnClicked
        }
        Button {
            objectName: "changeBrowserBtn"
            text: "CHANGEBROWSERBTN"
            icon {
                name: "document-edit"
            }
            visible: pages.currentIndex == 1 ? true : false
            onClicked: mainwnd.gotoBrowserSelect()
        }
        // Profile Editor Buttons
        Button {
            objectName: "editorCancelBtn"
            text: "EDITORCANCELBTN"
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
            objectName: "deleteProfileBtn"
            text: "DELETEPROFILEBTN"
            icon {
                name: "delete"
                color: Kirigami.Theme.negativeTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
            onClicked: deleteProfile();
        }
        // Browser Select Buttons
        Button {
            objectName: "cancelBrowserSelect"
            text: "CANCELBROWSERSELECT"
            icon {
                name: "dialog-cancel"
            }
            visible: pages.currentIndex == 3 ? true : false
            onClicked: pages.currentIndex = 1
        }
        Button {
            objectName: "storeBrowsersBtn"
            text: "STOREBROWSERSBTN"
            icon {
                name: "feren-store"
            }
            visible: pages.currentIndex == 3 ? storeAvailable : false
            //TODO: OnClicked
        }

        // Separator
        Rectangle {
            id: rectangle
            color: "#00000000"
            Layout.fillWidth: true
        }
        // Browser Select Buttons
        Button {
            objectName: "browserSelectDone"
            text: "BROWSERSELECTDONE"
            icon {
                color: Kirigami.Theme.positiveTextColor
            }
            enabled: mainwnd.selectedBrowser != ""
            visible: pages.currentIndex == 3 ? true : false
            onClicked: setBrowser(mainwnd.selectedBrowser)
        }
        // Profile Select Buttons
        Button { //also Profile Management in this button's case
            objectName: "profileSelectAdd"
            text: "PROFILESELECTADD"
            icon {
                name: "list-add"
            }
            visible: pages.currentIndex == 0 || pages.currentIndex == 1 ? true : false
            onClicked: gotoProfileEditor(true, "");
        }
        Button {
            objectName: "gotoManagerBtn"
            text: "GOTOMANAGERBTN"
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
            text: "EXITMANAGERBTN"
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
            text: "EDITORDONEBTN"
            icon {
                name: "dialog-apply"
                color: Kirigami.Theme.positiveTextColor
            }
            visible: pages.currentIndex == 2 ? true : false
            onClicked: mainwnd.saveProfile();
        }
    }
}
