// Copyright (c) 2019
// MKSPlugin is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import UM 1.2 as UM
import Cura 1.0 as Cura
import MKSPlugin 1.0 as MKSPlugin

import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import "."

Component
{
    id: monitorItem

    Item
    {
        property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
        property var printerModel: connectedDevice != null ? connectedDevice.activePrinter : null
        property var activePrintJob: printerModel != null ? printerModel.activePrintJob: null
        property var currentLanguage: UM.Preferences.getValue("general/language")

        SystemPalette { id: palette }
        UM.I18nCatalog { id: catalog; name:"mksplugin" }

        Item
        {
            id: horizontalCenterItem
            anchors.left: parent.left
            anchors.right: base.left
        }

        Cura.RoundedRectangle
        {
            id: background

            width: UM.Theme.getSize("print_setup_widget").width - UM.Theme.getSize("default_margin").width // "- UM.Theme.getSize("default_margin").width" needed for correct alignment of extruder block when 2 extruders

            color: UM.Theme.getColor("main_background")

            anchors
            {
                right: base.right
                top: base.top
                bottom: base.bottom
            }
        }

        Cura.PrintMonitor
        {
            id:base

            width: UM.Theme.getSize("print_setup_widget").width - UM.Theme.getSize("default_margin").width // "- UM.Theme.getSize("default_margin").width" needed for correct alignment of extruder block when 2 extruders
            anchors
            {
                right: parent.right
                top: parent.top
                bottom: parent.bottom
            }

            Rectangle
            {
                anchors
                {
                    top: parent.top
                    left: parent.left
                    //had not found how to insert this into Cura's qml, so took the summ of sizes from Cura's sources
                    leftMargin: Math.floor(parent.width * 0.4) + UM.Theme.getSize("default_margin").width * 2 + UM.Theme.getSize("default_lining").width * 5 + UM.Theme.getSize("setting_control").height * 4
                }

                Label //outputDevice.activePrinter.name spacer got from Cura/resources/qml/PrinterOutput/OutputDeviceHeader.qml
                {
                    id: outputDeviceNameLabelSpacer
                    font: UM.Theme.getFont("large_bold")
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    text: " "
                }
                Label //outputDevice.address spacer got from Cura/resources/qml/PrinterOutput/OutputDeviceHeader.qml
                {
                    id: outputDeviceAddressLabelSpacer
                    font: UM.Theme.getFont("default_bold")
                    anchors.top: outputDeviceNameLabelSpacer.bottom
                    anchors.left: parent.left
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    text: " "
                }
                Rectangle //extruder spacer a size of implicitHeight from Cura/resources/qml/PrinterOutput/ExtruderBox.qml
                {
                    id: extruderSpacer
                    anchors.top: outputDeviceAddressLabelSpacer.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").width
                    height: UM.Theme.getSize("print_setup_extruder_box").height
                }
                Rectangle //heat bed spacer a size of height from Cura/resources/qml/PrinterOutput/HeatedBedBox.qml
                {
                    id: heatBedSpacer
                    anchors.top: extruderSpacer.bottom
                    anchors.topMargin: UM.Theme.getSize("thick_lining").width //gor from Cura/resources/qml/PrintMonitor.qml
                    height: UM.Theme.getSize("print_setup_extruder_box").height
                }
                Rectangle //printer control spacer got from Cura/resources/qml/PrinterOutput/ManualPrinterControl.qml
                {
                    id: printerControlBoxSpacer
                    anchors.top: heatBedSpacer.bottom
                    height: UM.Theme.getSize("setting_control").height
                }

                Row
                {
                    spacing: UM.Theme.getSize("default_margin").width

                    anchors
                    {
                        top: printerControlBoxSpacer.bottom
                    }

                    Column
                    {
                        enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                        spacing: UM.Theme.getSize("default_lining").height
                        Label
                        {
                            text: catalog.i18nc("@label", "E0")
                            color: UM.Theme.getColor("setting_control_text")
                            font: UM.Theme.getFont("default")
                            width: UM.Theme.getSize("section").height
                            height: UM.Theme.getSize("setting_control").height
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Button
                        {
                            iconSource: UM.Theme.getIcon("arrow_top");
                            style: UM.Theme.styles.monitor_button_style
                            width: height
                            height: UM.Theme.getSize("setting_control").height

                            onClicked: Cura.MachineManager.printerOutputDevices[0].e0up()
                        }
                        Button
                        {
                            iconSource: UM.Theme.getIcon("arrow_bottom");
                            style: UM.Theme.styles.monitor_button_style
                            width: height
                            height: UM.Theme.getSize("setting_control").height

                            onClicked: Cura.MachineManager.printerOutputDevices[0].e0down()
                        }
                    }

                    Column
                    {
                        enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                        visible: Cura.MachineManager.printerOutputDevices[0].printer_E_num() > 1

                        spacing: UM.Theme.getSize("default_lining").height
                        Label
                        {
                            text: catalog.i18nc("@label", "E1")
                            color: UM.Theme.getColor("setting_control_text")
                            font: UM.Theme.getFont("default")
                            width: UM.Theme.getSize("section").height
                            height: UM.Theme.getSize("setting_control").height
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Button
                        {
                            iconSource: UM.Theme.getIcon("arrow_top");
                            style: UM.Theme.styles.monitor_button_style
                            width: height
                            height: UM.Theme.getSize("setting_control").height

                            onClicked: Cura.MachineManager.printerOutputDevices[0].e1up()
                        }
                        Button
                        {
                            iconSource: UM.Theme.getIcon("arrow_bottom");
                            style: UM.Theme.styles.monitor_button_style
                            width: height
                            height: UM.Theme.getSize("setting_control").height

                            onClicked: Cura.MachineManager.printerOutputDevices[0].e1down()
                        }
                    }
                }
            }

            Column
            {
                id: buttonBox

                spacing: UM.Theme.getSize("default_margin").width

                height: childrenRect.height

                anchors
                {
                    right: base.right
                    bottom: base.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").width
                }

                Rectangle
                {
                    color: UM.Theme.getColor("wide_lining")
                    width: base.width
                    height: UM.Theme.getSize("thick_lining").width * 2
                }

                Row
                {
                    id: controlButtonBox

                    height: childrenRect.height
                    spacing: UM.Theme.getSize("default_lining").width

                    anchors
                    {
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                    }

                    Button
                    {
                        id: sdFileButton

                        enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "paused" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                        height: UM.Theme.getSize("setting_control").height
                        style: UM.Theme.styles.print_setup_action_button
                        text: catalog.i18nc("@action:button", "SD Files")
                        onClicked: sdDialog.showDialog()

                        onHoveredChanged:
                        {
                            if (hovered)
                            {
                                base.showTooltip(
                                    base,
                                    {x: 0, y: printButtonBox.mapToItem(base, 0, 0).y},
                                    catalog.i18nc("@tooltip", "Browse SD card in 3D printer.")
                                );
                            }
                            else
                            {
                                base.hideTooltip();
                            }
                        }
                    }

                    Button
                    {
                        id: uploadButton

                        enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "paused" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                        height: UM.Theme.getSize("setting_control").height
                        style: UM.Theme.styles.print_setup_action_button
                        text: catalog.i18nc("@action:button", "Send Print Job")
                        onClicked: Cura.MachineManager.printerOutputDevices[0].selectFileToUplload()

                        onHoveredChanged:
                        {
                            if (hovered)
                            {
                                base.showTooltip(
                                    base,
                                    {x: 0, y: printButtonBox.mapToItem(base, 0, 0).y},
                                    catalog.i18nc("@tooltip", "Select and send G-Code file to 3D printer.")
                                );
                            }
                            else
                            {
                                base.hideTooltip();
                            }
                        }
                    }

                    Button
                    {
                        id: moreButton

                        height: UM.Theme.getSize("setting_control").height
                        style: UM.Theme.styles.print_setup_action_button
                        text: catalog.i18nc("@action:button", "More")
                        onClicked: moreDialog.show()

                        onHoveredChanged:
                        {
                            if (hovered)
                            {
                                base.showTooltip(
                                    base,
                                    {x: 0, y: printButtonBox.mapToItem(base, 0, 0).y},
                                    catalog.i18nc("@tooltip", "More printer commands.")
                                );
                            }
                            else
                            {
                                base.hideTooltip();
                            }
                        }
                    }
                }

                Row
                {
                    id: printButtonBox

                    height: childrenRect.height
                    spacing: UM.Theme.getSize("default_lining").width

                    anchors
                    {
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                    }

                    Button
                    {
                        id: pauseResumeButton

                        enabled: connectedDevice != null && connectedDevice.getProperty("manual") == "true" && (activePrintJob.state == "printing" || activePrintJob.state == "paused")

                        height: UM.Theme.getSize("setting_control").height
                        style: UM.Theme.styles.print_setup_action_button
                        text:
                        {
                            if (activePrintJob.state == "printing") {
                                return catalog.i18nc("@action:button", "Pause")
                            } else {
                                return catalog.i18nc("@action:button", "Resume")
                            }
                        }
                        onClicked:Cura.MachineManager.printerOutputDevices[0].pausePrint()

                        onHoveredChanged:
                        {
                            if (hovered)
                            {
                                base.showTooltip(
                                    base,
                                    {x: 0, y: printButtonBox.mapToItem(base, 0, 0).y},
                                    activePrintJob.state == "printing" ? catalog.i18nc("@tooltip", "Pause print.") : catalog.i18nc("@tooltip", "Resume print.")
                                );
                            }
                            else
                            {
                                base.hideTooltip();
                            }
                        }
                    }

                    Button
                    {
                        id: abortButton

                        enabled: connectedDevice != null && connectedDevice.getProperty("manual") == "true" && (activePrintJob.state == "printing" || activePrintJob.state == "paused")

                        height: UM.Theme.getSize("setting_control").height
                        style: UM.Theme.styles.print_setup_action_button
                        text: catalog.i18nc("@action:button", "Abort Print")
                        onClicked: Cura.MachineManager.printerOutputDevices[0].cancelPrint()

                        onHoveredChanged:
                        {
                            if (hovered)
                            {
                                base.showTooltip(
                                    base,
                                    {x: 0, y: printButtonBox.mapToItem(base, 0, 0).y},
                                    catalog.i18nc("@tooltip", "Abort current print.")
                                );
                            }
                            else
                            {
                                base.hideTooltip();
                            }
                        }
                    }
                }
            }
        }

        UM.Dialog
        {
            id: sdDialog
            signal showDialog()
            onShowDialog:
            {
                listview.model = Cura.MachineManager.printerOutputDevices[0].getSDFiles
                sdDialog.show();
            }
            title: catalog.i18nc("@title:window", "Open file(s)")
            Column{
                spacing: UM.Theme.getSize("default_margin").height
                ScrollView{
                    id: objectListContainer
                    width: sdDialog.width-UM.Theme.getSize("default_margin").height*1.5
                    height: sdDialog.height-btnOk.height*2
                    Rectangle
                    {
                        parent: viewport
                        anchors.fill: parent
                        color: palette.light
                    }
                    ListView{
                        id: listview
                        model: Cura.MachineManager.printerOutputDevices[0].getSDFiles
                        currentIndex: -1
                        onModelChanged:
                        {
                            currentIndex = -1;
                        }
                        onCurrentIndexChanged:
                        {
                        }
                        delegate: Rectangle{
                            height: childrenRect.height
                            color: ListView.isCurrentItem ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                            width: objectListContainer.width
                            Label
                            {
                                anchors.left: parent.left
                                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                anchors.right: parent.right
                                text: listview.model[index]
                                color: parent.ListView.isCurrentItem ? palette.highlightedText : palette.text
                                elide: Text.ElideRight
                            }

                            MouseArea
                            {
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
            }
            rightButtons: [
            Button {
                text: catalog.i18nc("@action:button","Delete")
                onClicked:
                {
                    // sdDialog.reject()
                    if(listview.currentIndex != -1)
                    {
                        sdDialog.hide()
                        Cura.MachineManager.printerOutputDevices[0].deleteSDFiles(listview.model[listview.currentIndex])
                        listview.model = Cura.MachineManager.printerOutputDevices[0].getSDFiles
                    }
                }
            },
            Button {
                id: btnOk
                text: catalog.i18nc("@action:button", "Print")
                onClicked:
                {
                    // sdDialog.accept()
                    if(listview.currentIndex != -1)
                    {
                        sdDialog.hide()
                        Cura.MachineManager.printerOutputDevices[0].printSDFiles(listview.model[listview.currentIndex])
                    }
                }
            },
            Button {
                id: btnRefresh
                text: catalog.i18nc("@action:button", "Refresh")
                onClicked:
                {
                    Cura.MachineManager.printerOutputDevices[0].getSDFiles
                    
                }
            }
        ]
        }

        UM.Dialog
        {
            id: moreDialog
            signal showDialog()
            title: catalog.i18nc("@title:window", "More")

            minimumWidth: 200 * screenScaleFactor
            minimumHeight: 120 * screenScaleFactor
            width: minimumWidth
            height: minimumHeight

            Column
            {
                id: buttonColumn
                spacing: UM.Theme.getSize("default_lining").height

                anchors.fill: parent

                Button
                {
                    id: fanOnButton

                    width: parent.width

                    text: catalog.i18nc("@action:button", "Fan On")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].openfan()

                    tooltip: catalog.i18nc("@tooltip", "Turn fan on.")
                }

                Button
                {
                    id: fanOffButton

                    width: parent.width

                    text: catalog.i18nc("@action:button", "Fan Off")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].closefan()

                    tooltip: catalog.i18nc("@tooltip", "Turn fan off.")
                }

                Button
                {
                    id: coolDownButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.getProperty("manual") == "true" && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "Cool Down")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].printtest()

                    tooltip: catalog.i18nc("@tooltip", "Cool down heated bed and exptuder.")
                }

                Button
                {
                    id: unlockMotorButton

                    width: parent.width

                    enabled: connectedDevice != null && connectedDevice.acceptsCommands && (activePrintJob == null || !(activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline"))

                    text: catalog.i18nc("@action:button", "Unlock Motors")
                    onClicked: Cura.MachineManager.printerOutputDevices[0].unlockmotor()

                    tooltip: catalog.i18nc("@tooltip", "Unlock 3D printer motors.")
                }
            }
        }
    }
}
