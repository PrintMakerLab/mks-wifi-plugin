// Copyright (c) 2019
// MKSPlugin is released under the terms of the AGPLv3 or higher.

import QtQuick 6.0
import UM 1.6 as UM
import Cura 1.7 as Cura

import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0
import QtQuick.Window 6.0

import "."

Component
{
    id: monitorItem

    Item
    {
        property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
        property var printerModel: connectedDevice != null ? connectedDevice.activePrinter : null
        property var activePrintJob: printerModel != null ? printerModel.activePrintJob: null
        property var _buttonSize: UM.Theme.getSize("setting_control").height + UM.Theme.getSize("thin_margin").height

        UM.I18nCatalog { id: catalog; name:"mksplugin" }
        UM.I18nCatalog { id: cura_catalog; name: "cura"}

        // Item
        // {
        //     id: horizontalCenterItem
        //     anchors.left: parent.left
        //     anchors.right: base.left
        // }

        Rectangle {
            color: UM.Theme.getColor("main_background")

            anchors.right: parent.right
            width: Math.floor(parent.width * 0.35) - ((Math.floor(parent.width * 0.35) % 2) ? 0 : 1) // section after minus needed for correct alignment of extruder block when 2 extruders
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            Cura.PrintMonitor {
                id:base

                anchors
                {
                    right: parent.right
                    top: parent.top
                    bottom: parent.bottom
                }

                anchors.fill: parent

                Rectangle {
                    anchors
                    {
                        top: parent.top
                        left: parent.left
                        //had not found how to insert this into Cura's qml, so took the summ of sizes from Cura's sources
                        leftMargin: Math.floor(parent.width * 0.4) + UM.Theme.getSize("default_margin").width * 2 + UM.Theme.getSize("default_lining").width * 5 + _buttonSize * 4
                    }

                    Label {//outputDevice.activePrinter.name spacer got from Cura/resources/qml/PrinterOutput/OutputDeviceHeader.qml
                        id: outputDeviceNameLabelSpacer
                        font: UM.Theme.getFont("large_bold")
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: UM.Theme.getSize("default_margin").width
                        text: " "
                    }
                    Label {//outputDevice.address spacer got from Cura/resources/qml/PrinterOutput/OutputDeviceHeader.qml
                        id: outputDeviceAddressLabelSpacer
                        font: UM.Theme.getFont("default_bold")
                        anchors.top: outputDeviceNameLabelSpacer.bottom
                        anchors.left: parent.left
                        anchors.margins: UM.Theme.getSize("default_margin").width
                        text: " "
                    }
                    Rectangle {//extruder spacer a size of implicitHeight from Cura/resources/qml/PrinterOutput/ExtruderBox.qml
                        id: extruderSpacer
                        anchors.top: outputDeviceAddressLabelSpacer.bottom
                        anchors.topMargin: UM.Theme.getSize("default_margin").width
                        height: UM.Theme.getSize("print_setup_extruder_box").height
                    }
                    Rectangle {//heat bed spacer a size of height from Cura/resources/qml/PrinterOutput/HeatedBedBox.qml
                        id: heatBedSpacer
                        anchors.top: extruderSpacer.bottom
                        anchors.topMargin: UM.Theme.getSize("thick_lining").width //gor from Cura/resources/qml/PrintMonitor.qml
                        height: UM.Theme.getSize("print_setup_extruder_box").height
                    }
                    Rectangle { //printer control spacer got from Cura/resources/qml/PrinterOutput/ManualPrinterControl.qml
                        id: printerControlBoxSpacer
                        anchors.top: heatBedSpacer.bottom
                        height: UM.Theme.getSize("setting_control").height
                    }

                    Row {
                        spacing: UM.Theme.getSize("default_margin").width

                        anchors
                        {
                            top: printerControlBoxSpacer.bottom
                        }

                        Column {
                            enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                            spacing: UM.Theme.getSize("default_lining").height
                            UM.Label {
                                text: catalog.i18nc("@label", "E0")
                                color: UM.Theme.getColor("setting_control_text")
                                width: height
                                height: UM.Theme.getSize("setting_control").height
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Cura.SecondaryButton {
                                iconSource: UM.Theme.getIcon("ChevronSingleUp");
                                leftPadding: (width - iconSize) / 2
                                width: _buttonSize
                                height: _buttonSize

                                onClicked: Cura.MachineManager.printerOutputDevices[0].e0up()
                            }
                            Cura.SecondaryButton {
                                iconSource: UM.Theme.getIcon("ChevronSingleDown");
                                leftPadding: (width - iconSize) / 2
                                width: _buttonSize
                                height: _buttonSize

                                onClicked: Cura.MachineManager.printerOutputDevices[0].e0down()
                            }
                        }

                        Column {
                            enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                            visible: Cura.MachineManager.printerOutputDevices[0].printer_E_num() > 1

                            spacing: UM.Theme.getSize("default_lining").height
                            Label {
                                text: catalog.i18nc("@label", "E1")
                                color: UM.Theme.getColor("setting_control_text")
                                font: UM.Theme.getFont("default")
                                width: UM.Theme.getSize("section").height
                                height: UM.Theme.getSize("setting_control").height
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Button {
                                icon.source: UM.Theme.getIcon("ChevronSingleUp");
                                // style: UM.Theme.styles.monitor_button_style
                                width: height
                                height: UM.Theme.getSize("setting_control").height

                                onClicked: Cura.MachineManager.printerOutputDevices[0].e1up()
                            }

                            Button {
                                icon.source: UM.Theme.getIcon("ChevronSingleDown");
                                // style: UM.Theme.styles.monitor_button_style
                                width: height
                                height: UM.Theme.getSize("setting_control").height

                                onClicked: Cura.MachineManager.printerOutputDevices[0].e1down()
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: footerSeparator
                width: parent.width
                height: UM.Theme.getSize("wide_lining").height
                color: UM.Theme.getColor("wide_lining")
                anchors.bottom: monitorButton.top
                anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
            }

            // MonitorButton is actually the bottom footer panel.
            Cura.MonitorButton {
                id: monitorButton
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right

                Label {
                    id: statusLabelSpacer
                    width: parent.width - 2 * UM.Theme.getSize("thick_margin").width
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("thick_margin").width

                    font: UM.Theme.getFont("large_bold")
                    text: " "
                }

                Label {
                    id: percentageLabelSpacer
                    anchors.top: parent.top
                    anchors.right: parent.right

                    font: UM.Theme.getFont("large_bold")
                    text: " "
                }

                Cura.SecondaryButton {
                    id: pauseResumeButtonSpacer

                    height: UM.Theme.getSize("save_button_save_to_button").height

                    visible: false

                    text: {
                        if (activePrintJob.state == "paused") {
                            return cura_catalog.i18nc("@label", "Resume");
                        } else {
                            return cura_catalog.i18nc("@label", "Pause");
                        }
                    }
                }

                Cura.SecondaryButton {
                    id: abortButtonSpacer

                    visible: false

                    height: UM.Theme.getSize("save_button_save_to_button").height

                    text: cura_catalog.i18nc("@label", "Abort Print")
                }

                Cura.SecondaryButton {
                    id: moreButton

                    anchors.top: percentageLabelSpacer.bottom
                    anchors.topMargin: UM.Theme.getSize("progressbar").height +  Math.round(UM.Theme.getSize("thick_margin").height / 4) + UM.Theme.getSize("thick_margin").height
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width + pauseResumeButtonSpacer.width + UM.Theme.getSize("default_margin").width + abortButtonSpacer.width + UM.Theme.getSize("thick_margin").width

                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: catalog.i18nc("@action:button", "More")
                    onClicked: moreDialog.show()
                }
            }
        }

        Timer {
            interval: 5000
            running: sdDialog.visible
            repeat: true
            onTriggered: Cura.MachineManager.printerOutputDevices[0].refreshSDFiles()
        }

        UM.Dialog {
            id: sdDialog
            title: catalog.i18nc("@title:window", "Open file(s)")

            Column {
                spacing: UM.Theme.getSize("default_margin").height

                anchors.fill: parent

                Row {
                    spacing: UM.Theme.getSize("default_margin").height

                    UM.Label {
                        height: drivePrefixTextInput.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "Drive prefix:")
                    }

                    Cura.ComboBox {
                        id: drivePrefixComboBox
                        width: 100
                        height: drivePrefixTextInput.height

                        textRole: "text"

                        model: [
                            { text: catalog.i18nc("@label", "None"), value: "" },
                            { text: "1:/", value: "1:/" },
                            { text: catalog.i18nc("@label", "Custom"), value: ""}
                        ]

                        onCurrentIndexChanged: {
                            var currnetDrivePrefix = model[drivePrefixComboBox.currentIndex].value
                            drivePrefixTextInput.text = currnetDrivePrefix
                        }
                    }

                    Cura.TextField {
                        id: drivePrefixTextInput
                        width: Math.round(parent.width * 0.5) - UM.Theme.getSize("default_margin").width

                        onEditingFinished: {
                        }

                        enabled: {
                            if (drivePrefixComboBox.currentText == catalog.i18nc("@label", "Custom")) {
                                return true
                            }
                            return false
                        }
                    }
                }

                Row {
                    spacing: UM.Theme.getSize("default_margin").height

                    UM.Label {
                        height: drivePrefixTextInput.height
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        text: catalog.i18nc("@label", "If the Print/Delete buttons aren't working, adjust the Drive prefix above. \nChoose 'None' or '1:/' based on your printer's firmware (e.g., 'None' for Marlin, '1:/' for FlyingBear Ghost).")
                    }
                }

                Cura.ScrollView {
                    id: objectListContainer
                    width: sdDialog.width-UM.Theme.getSize("default_margin").height*1.5
                    height: sdDialog.height - btnPrint.height*2 - drivePrefixTextInput.height*2 -drivePrefixTextInput.height*2

                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                    ListView {
                        id: listview
                        model: Cura.MachineManager.printerOutputDevices[0].getSDFiles
                        currentIndex: -1

                        onModelChanged:
                        {
                            currentIndex = -1;
                        }

                        delegate: Rectangle {
                            height: childrenRect.height
                            color: ListView.isCurrentItem ? UM.Theme.getColor("background_3") : "transparent"
                            width: objectListContainer.width
                            Label
                            {
                                anchors.left: parent.left
                                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                anchors.right: parent.right
                                text: listview.model[index]
                                color: UM.Theme.getColor("text")
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
                    anchors.right: parent.right
                    spacing: UM.Theme.getSize("default_margin").height

                    Cura.SecondaryButton {
                        text: catalog.i18nc("@action:button","Delete")
                        enabled: listview.currentIndex != -1
                        onClicked:
                        {
                            if(listview.currentIndex != -1)
                            {
                                Cura.MachineManager.printerOutputDevices[0].deleteSDFiles(drivePrefixTextInput.text, "", listview.model[listview.currentIndex])
                            }
                        }
                    }
                    Cura.SecondaryButton {
                        id: btnPrint
                        text: catalog.i18nc("@action:button", "Print")
                        enabled: listview.currentIndex != -1
                        onClicked:
                        {
                            if(listview.currentIndex != -1)
                            {
                                sdDialog.hide()
                                Cura.MachineManager.printerOutputDevices[0].printSDFiles(drivePrefixTextInput.text, "", listview.model[listview.currentIndex])
                            }
                        }
                    }
                }
            }
        }

        UM.Dialog {
            id: moreDialog
            title: catalog.i18nc("@title:window", "More")

            minimumWidth: 200 * screenScaleFactor
            width: minimumWidth
            height: sdFileButton.height + uploadButton.height + fanOnButton.height + fanOffButton.height + coolDownButton.height + unlockMotorButton.height + UM.Theme.getSize("default_margin").height * 2

            Column {
                id: buttonColumn
                spacing: UM.Theme.getSize("default_lining").height

                anchors.fill: parent

                Cura.SecondaryButton {
                    id: sdFileButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "paused" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "SD Files")
                    onClicked: sdDialog.show()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Browse SD card in 3D printer.")
                }

                Cura.SecondaryButton {
                    id: uploadButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "paused" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "Send Print Job")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].selectFileToUplload()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Select and send G-Code file to 3D printer.")
                }


                Cura.SecondaryButton {
                    id: fanOnButton

                    width: parent.width

                    text: catalog.i18nc("@action:button", "Fan On")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].openfan()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Turn fan on.")
                }

                Cura.SecondaryButton {
                    id: fanOffButton

                    width: parent.width

                    text: catalog.i18nc("@action:button", "Fan Off")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].closefan()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Turn fan off.")
                }

                Cura.SecondaryButton {
                    id: coolDownButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.getProperty("manual") == "true" && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "Cool Down")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].printtest()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Cool down heated bed and exptuder.")
                }

                Cura.SecondaryButton {
                    id: unlockMotorButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "Unlock Motors")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].unlockmotor()

                    ToolTip.visible: hovered
                    ToolTip.text: catalog.i18nc("@tooltip", "Unlock 3D printer motors.")
                }
            }
        }
    }
}
