// Copyright (c) 2021
// MKS Plugin is released under the terms of the AGPLv3 or higher.

import UM 1.3 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.3
import QtQuick.Window 2.1

Cura.MachineAction {
    id: base
    anchors.fill: parent;

    UM.I18nCatalog { id: catalog; name:"mksplugin" }

    property var selectedPrinter: null

    property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

    property var printerSupportScreenshots: manager.supportScreenshot()
    property var printerScreenshotSizesList: manager.getScreenshotOptions()
    property var printerScreenshotIndex: {
        var sIndex = manager.getScreenshotIndex()

        screenshotComboBox.currentIndex = sIndex
        return sIndex
    }

    function connectPrinter() {
        if(base.selectedPrinter) {
            if(manager.getCurrentAddress() != base.selectedPrinter)
            {
                manager.mks_connect_printer(base.selectedPrinter);
                completed();
            }
        }
    }

    function disconnectPrinter() {
        if(base.selectedPrinter) {
            if(manager.getCurrentAddress() == base.selectedPrinter)
            {
                manager.mks_disconnect_printer(base.selectedPrinter);
                completed();
            }
        }
    }

    ListModel {
        id: tabNameModel

        Component.onCompleted: update()

        function update() {
            clear()
            append({ name: catalog.i18nc("@title:tab", "Network settings") })
            append({ name: catalog.i18nc("@title:tab", "Preview settings") })
        }
    }

    Cura.RoundedRectangle {
        anchors
        {
            top: tabBar.bottom
            topMargin: -UM.Theme.getSize("default_lining").height
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        cornerSide: Cura.RoundedRectangle.Direction.Down
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width
        color: UM.Theme.getColor("main_background")
        StackLayout {
            id: tabStack
            anchors.fill: parent

            currentIndex: tabBar.currentIndex

            Item {
                id: networkTab

                property int columnWidth: ((parent.width - 2 * UM.Theme.getSize("default_margin").width) / 2) | 0
                property int columnSpacing: 3 * screenScaleFactor

                property int labelWidth: (columnWidth * 2 / 3 - UM.Theme.getSize("default_margin").width * 2) | 0
                property int controlWidth: (columnWidth / 3) | 0
                property var labelFont: UM.Theme.getFont("default")

                Column {
                    id: networkUpperBlock
                    anchors
                    {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        bottom: parent.bottom
                        margins: UM.Theme.getSize("default_margin").width
                    }
                    spacing: UM.Theme.getSize("default_margin").width
                    width: parent.width

                    Row {
                        id: wifiSupportRow
                        anchors
                        {
                            left: parent.left
                            right: parent.right
                        }

                        Label {
                            width: Math.round(parent.width * 0.5)
                            height: mksWifiSupport.height
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.WordWrap
                            text: catalog.i18nc("@label", "WiFi support")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")

                            enabled: mksSupport.checked
                        }
                        Cura.CheckBox {
                            id: mksWifiSupport
                            checked: manager.WiFiSupportEnabled()

                            onCheckedChanged: {
                                if (!mksWifiSupport.checked) {
                                    manager.setMaxFilenameLen("")
                                    disconnectPrinter();
                                }
                            }

                            enabled: mksSupport.checked
                        }
                    }

                    Row {
                        id: maxFilenameLenRow
                        anchors
                        {
                            left: parent.left
                            right: parent.right
                        }

                        Label {
                            width: Math.round(parent.width * 0.5)
                            height: maxFilenameLenInput.height
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.WordWrap
                            text: catalog.i18nc("@label", "Maximum file name length (0..255, 30 by default)")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")

                            enabled: mksSupport.checked
                        }
                        Cura.TextField {
                            id: maxFilenameLenInput
                            width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width
                            maximumLength: 3
                            validator: RegExpValidator
                            {
                                regExp: /^\s*$|^(?:[0-1]?[0-9]?[0-9]|2?[0-4]?[0-9]|25[0-5])$/
                            }

                            text: manager.getMaxFilenameLen()

                            onEditingFinished: {
                                manager.setMaxFilenameLen(maxFilenameLenInput.text)
                            }

                            enabled: mksSupport.checked
                        }
                    }

                    Row {
                        id: printerControlRaw
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").width

                        Button {
                            id: addButton
                            height: UM.Theme.getSize("setting_control").height
                            style: UM.Theme.styles.print_setup_action_button
                            text: catalog.i18nc("@action:button", "Add");
                            enabled: mksWifiSupport.checked;
                            onClicked:
                            {
                                manualPrinterDialog.showDialog("");
                            }
                        }

                        Button {
                            id: editButton
                            height: UM.Theme.getSize("setting_control").height
                            style: UM.Theme.styles.print_setup_action_button
                            text: catalog.i18nc("@action:button", "Edit")
                            enabled: mksWifiSupport.checked && base.selectedPrinter != null
                            onClicked:
                            {
                                manualPrinterDialog.showDialog(base.selectedPrinter);
                            }
                        }

                        Button {
                            id: removeButton
                            height: UM.Theme.getSize("setting_control").height
                            style: UM.Theme.styles.print_setup_action_button
                            text: catalog.i18nc("@action:button", "Remove")
                            enabled: mksWifiSupport.checked && base.selectedPrinter != null
                            onClicked: {
                                if (connectedDevice.address  == base.selectedPrinter) {
                                    disconnectPrinter();
                                }
                                manager.removePrinter(base.selectedPrinter);
                            }
                        }
                    }

                    Cura.ScrollView {
                        id: objectListContainer
                        width: parent.width
                        height: networkUpperBlock.height - wifiSupportRow.height - maxFilenameLenRow.height - printerControlRaw.height - printerConnectRaw.height - UM.Theme.getSize("default_margin").width * 4

                        enabled: mksWifiSupport.checked;

                        ListView
                        {
                            id: listview
                            model: manager.foundDevices
                            onModelChanged: {
                                var printerAddress = manager.getCurrentAddress();
                                for(var i = 0; i < model.length; i++) {
                                    if(model[i] == printerAddress)
                                    {
                                        currentIndex = i;
                                        return
                                    }
                                }
                                currentIndex = -1;
                            }
                            width: parent.width
                            currentIndex: -1
                            onCurrentIndexChanged: {
                                base.selectedPrinter = listview.model[currentIndex];
                            }
                            Component.onCompleted: manager.startDiscovery()
                            delegate: Rectangle
                            {
                                height: childrenRect.height
                                color: ListView.isCurrentItem ? UM.Theme.getColor("button_active") : UM.Theme.getColor("button")
                                width: parent.width
                                Label
                                {
                                    anchors.left: parent.left
                                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                    anchors.right: parent.right
                                    text: listview.model[index]
                                    color: objectListContainer.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("text_inactive")
                                    elide: Text.ElideRight
                                }

                                MouseArea {
                                    anchors.fill: parent;
                                    onClicked:
                                    {
                                        if(!parent.ListView.isCurrentItem)
                                        {
                                            parent.ListView.view.currentIndex = index;
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Row {
                        id: printerConnectRaw
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").width

                        Button {
                            id: connectbtn
                            height: UM.Theme.getSize("setting_control").height
                            style: UM.Theme.styles.print_setup_action_button
                            text: catalog.i18nc("@action:button", "Connect")
                            enabled: {
                                if (!mksWifiSupport.checked) {
                                    return false
                                }
                                if (base.selectedPrinter) {
                                    if (connectedDevice != null) {
                                        if (connectedDevice.address  != base.selectedPrinter) {
                                            return true
                                        }else{
                                            return false
                                        }
                                    } else {
                                        return true
                                    }
                                }
                                return false
                            }
                            onClicked: {
                                connectPrinter()
                            }
                        }

                        Button {
                            id: disconnectbtn
                            height: UM.Theme.getSize("setting_control").height
                            style: UM.Theme.styles.print_setup_action_button
                            text: catalog.i18nc("@action:button", "Disconnect")
                            enabled: {
                                if (!mksWifiSupport.checked) {
                                    return false
                                }
                                if (base.selectedPrinter) {
                                    if (connectedDevice != null) {
                                        if (connectedDevice.address == base.selectedPrinter) {
                                            return true
                                        }
                                    }
                                }
                                return false
                            }
                            onClicked: disconnectPrinter()
                        }
                    }
                }
            }

            Item {
                id: screenshotTab

                Grid {
                    id: screenshotUpperBlock
                    anchors
                    {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        margins: UM.Theme.getSize("default_margin").width
                    }
                    spacing: UM.Theme.getSize("default_margin").width
                    width: parent.width
                    columns: 2

                    Label {
                        width: Math.round(parent.width * 0.5)
                        height: mksScreenshotSupport.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Screenshot support")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")

                        enabled: mksSupport.checked
                    }
                    Cura.CheckBox {
                        id: mksScreenshotSupport
                        checked: printerSupportScreenshots

                        onCheckedChanged: {
                            if (!mksScreenshotSupport.checked) {
                                manager.setSimage("")
                                manager.setGimage("")
                                manager.setScreenshotIndex("")
                                screenshotComboBox.currentIndex = 0
                            }
                            simageTextInput.text = manager.getSimage()
                            gimageTextInput.text = manager.getGimage()
                            screenshotComboBox.currentIndex = printerScreenshotIndex
                        }

                        enabled: mksSupport.checked
                    }

                    Label {
                        width: Math.round(parent.width * 0.5)
                        height: screenshotComboBox.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Printer model")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")

                        enabled: mksScreenshotSupport.checked
                    }
                    Cura.ComboBox {
                        id: screenshotComboBox
                        width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width
                        height: mksSupport.height

                        textRole: "key"

                        model: printerScreenshotSizesList

                        onCurrentIndexChanged:
                        {
                            if (mksScreenshotSupport.checked) {
                                var currentValue = model[screenshotComboBox.currentIndex].key
                                if (currentValue != catalog.i18nc("@label", "Custom")){
                                    var settings = manager.getScreenshotSettings(currentValue)
                                    manager.setSimage(settings.simage)
                                    manager.setGimage(settings.gimage)
                                }
                                simageTextInput.text = manager.getSimage()
                                gimageTextInput.text = manager.getGimage()
                                manager.setScreenshotIndex(currentIndex)
                            }
                        }
                        enabled: mksScreenshotSupport.checked
                    }

                    Label {
                        width: Math.round(parent.width * 0.5)
                        height: simageTextInput.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Simage")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")

                        enabled: mksScreenshotSupport.checked
                    }
                    Cura.TextField {
                        id: simageTextInput
                        width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width
                        maximumLength: 5
                        validator: RegExpValidator {
                            regExp: /[0-9]*/
                        }

                        text: manager.getSimage()

                        onEditingFinished: {
                            if (mksScreenshotSupport.checked) {
                                manager.setSimage(simageTextInput.text)
                            }
                        }

                        enabled: {
                            if (mksScreenshotSupport.checked) {
                                if (screenshotComboBox.currentText == catalog.i18nc("@label", "Custom")) {
                                    return true
                                }
                            }
                            return false
                        }
                    }

                    Label {
                        width: Math.round(parent.width * 0.5)
                        height: gimageTextInput.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Gimage")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")

                        enabled: mksScreenshotSupport.checked
                    }
                    Cura.TextField {
                        id: gimageTextInput
                        width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width
                        maximumLength: 5
                        validator: RegExpValidator {
                            regExp: /[0-9]*/
                        }

                        text: manager.getGimage()

                        onEditingFinished: {
                            if (mksScreenshotSupport.checked) {
                                manager.setGimage(gimageTextInput.text)
                            }
                        }

                        enabled: {
                            if (mksScreenshotSupport.checked) {
                                if (screenshotComboBox.currentText == catalog.i18nc("@label", "Custom")) {
                                    return true
                                }
                            }
                            return false
                        }
                    }
                }
            }
        }
    }

    Row {
        id: headerRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        width: parent.width
        spacing: UM.Theme.getSize("default_margin").height

        Label {
            width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width * 2
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "MKS WiFi Plugin is active for this printer")
        }
        Cura.CheckBox {
            id: mksSupport
            checked: manager.pluginEnabled()

            onCheckedChanged: {
                if (mksSupport.checked) {
                    manager.pluginEnable()
                } else {
                    mksWifiSupport.checked = false
                    mksScreenshotSupport.checked = false
                    manager.pluginDisable()
                }
            }
        }
    }

    UM.TabRow {
        id: tabBar
        anchors.top: headerRow.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        Repeater {
            model: tabNameModel
            delegate: UM.TabRowButton
            {
                text: model.name
            }
        }
    }

    UM.Dialog {
        id: manualPrinterDialog
        property var prevAddress: ""
        property alias addressText: addressField.text

        title: catalog.i18nc("@title:window", "Adding a new printer")

        minimumWidth: 400 * screenScaleFactor
        minimumHeight: 130 * screenScaleFactor
        width: minimumWidth
        height: minimumHeight

        signal showDialog(string address)
        onShowDialog: {

            prevAddress = address;
            addressText = address;
            addressField.selectAll();
            addressField.focus = true;

            manualPrinterDialog.show();
        }

        onAccepted: {
            manager.setPrinter(prevAddress, addressText)
        }

        Column {
            anchors.fill: parent
            spacing: UM.Theme.getSize("default_margin").height

            Label {
                text: catalog.i18nc("@alabel","Enter the IP address or hostname of your printer on the network.")
                width: parent.width
                wrapMode: Text.WordWrap
            }

            TextField {
                id: addressField
                width: parent.width
                maximumLength: 40
                validator: RegExpValidator
                {
                    regExp: /[a-zA-Z0-9\.\-\_]*/
                }
            }
        }

        rightButtons: [
            Button {
                text: catalog.i18nc("@action:button","Cancel")
                onClicked: {
                    manualPrinterDialog.reject()
                    manualPrinterDialog.hide()
                }
            },
            Button {
                text: catalog.i18nc("@action:button", "OK")
                onClicked: {
                    manualPrinterDialog.accept()
                    manualPrinterDialog.hide()
                }
                enabled: manualPrinterDialog.addressText.trim() != ""
                isDefault: true
            }
        ]
    }
}
