// Copyright (c) 2019 Aldo Hoeben / fieldOfView
// MKSPlugin is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import UM 1.2 as UM
import Cura 1.0 as Cura
import MKSPlugin 1.0 as MKSPlugin

import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Component
{
    id: monitorItem

    Item
    {
        // MKSPlugin.NetworkMJPGImage
        // {
        //     id: cameraImage
        //     visible: OutputDevice != null ? OutputDevice.showCamera : false

        //     property real maximumWidthMinusSidebar: maximumWidth - sidebar.width - 2 * UM.Theme.getSize("default_margin").width
        //     property real maximumZoom: 2
        //     property bool rotatedImage: (OutputDevice.cameraOrientation.rotation / 90) % 2
        //     property bool proportionalHeight:
        //     {
        //         if (imageHeight == 0 || maximumHeight == 0)
        //         {
        //             return true;
        //         }
        //         if (!rotatedImage)
        //         {
        //             return (imageWidth / imageHeight) > (maximumWidthMinusSidebar / maximumHeight);
        //         }
        //         else
        //         {
        //             return (imageWidth / imageHeight) > (maximumHeight / maximumWidthMinusSidebar);
        //         }
        //     }
        //     property real _width:
        //     {
        //         if (!rotatedImage)
        //         {
        //             return Math.min(maximumWidthMinusSidebar, imageWidth * screenScaleFactor * maximumZoom);
        //         }
        //         else
        //         {
        //             return Math.min(maximumHeight, imageWidth * screenScaleFactor * maximumZoom);
        //         }
        //     }
        //     property real _height:
        //     {
        //         if (!rotatedImage)
        //         {
        //             return Math.min(maximumHeight, imageHeight * screenScaleFactor * maximumZoom);
        //         }
        //         else
        //         {
        //             return Math.min(maximumWidth, imageHeight * screenScaleFactor * maximumZoom);
        //         }
        //     }
        //     width: proportionalHeight ? _width : imageWidth * _height / imageHeight
        //     height: !proportionalHeight ? _height : imageHeight * _width / imageWidth
        //     anchors.horizontalCenter: horizontalCenterItem.horizontalCenter
        //     anchors.verticalCenter: parent.verticalCenter

        //     Component.onCompleted:
        //     {
        //         if (visible)
        //         {
        //             start();
        //         }
        //     }
        //     onVisibleChanged:
        //     {
        //         if (visible)
        //         {
        //             start();
        //         } else
        //         {
        //             stop();
        //         }
        //     }
        //     source: OutputDevice.cameraUrl

        //     rotation: OutputDevice.cameraOrientation.rotation
        //     mirror: OutputDevice.cameraOrientation.mirror
        // }

        Item
        {
            id: horizontalCenterItem
            anchors.left: parent.left
            anchors.right: sidebar.left
        }
        Column
        {
            id: printaction
            width: UM.Theme.getSize("print_setup_widget").width
            SystemPalette { id: palette }
            UM.I18nCatalog { id: catalog; name:"cura" }
            UM.I18nCatalog { id: fdmprinter; name:"fdmprinter"}
            anchors
            {
                right: parent.right
                top: parent.top
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
                bottomMargin: UM.Theme.getSize("default_margin").height
            }
            Cura.PrintMonitor 
            {
                id:controlpanel
                width: parent.width
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    rightMargin: UM.Theme.getSize("default_margin").width
                }
            }
            Row
            {
                spacing: UM.Theme.getSize("default_lining").width
                anchors
                {
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("save_button_save_to_button").height
                }
                // Button
                // {
                //     id: addButton
                //     height: UM.Theme.getSize("save_button_save_to_button").height
                //     text: catalog.i18nc("@action:button", "Print");
                //     onClicked: Cura.MachineManager.printerOutputDevices[0].printtest()
                // }

                Button
                {
                    id: editButton
                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: 
                    {
                        if(Cura.MachineManager.printerOutputDevices[0].printer_state() == 'paused')
                        {
                            return catalog.i18nc("@label", "Resume");
                        }else{
                            return catalog.i18nc("@label", "Pause");
                        }
                    }
                    enabled: base.selectedPrinter != null && base.selectedPrinter.getProperty("manual") == "true"
                    onClicked:Cura.MachineManager.printerOutputDevices[0].pausePrint()
                }

                Button
                {
                    id: removeButton
                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: catalog.i18nc("@label", "Abort")
                    enabled: base.selectedPrinter != null && base.selectedPrinter.getProperty("manual") == "true"
                    onClicked: Cura.MachineManager.printerOutputDevices[0].cancelPrint()
                }

                Button
                {
                    id: rediscoverButton
                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: catalog.i18nc("@label", "SD")
                    onClicked: sdDialog.showDialog()
                }
            }
            Row
            {
                spacing: UM.Theme.getSize("default_lining").width
                anchors
                {
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    bottom: parent.bottom
                    // bottomMargin: UM.Theme.getSize("default_margin").height
                }
                Button
                {
                    id: homebutton
                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: "Cool Down";
                    onClicked: Cura.MachineManager.printerOutputDevices[0].printtest()
                }
                Button
                {
                    id: uploadbutton
                    height: UM.Theme.getSize("save_button_save_to_button").height
                    text: catalog.i18nc("@info:status", "Sending data to printer");
                    onClicked: Cura.MachineManager.printerOutputDevices[0].selectFileToUplload()
                }
            }

        }

        UM.Dialog{
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
                text: catalog.i18nc("@label","Delete")
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
            }
        ]
        }

        // Cura.RoundedRectangle
        // {
        //     id: sidebar

        //     width: UM.Theme.getSize("print_setup_widget").width
            // anchors
            // {
            //     right: parent.right
            //     top: parent.top
            //     topMargin: UM.Theme.getSize("default_margin").height
            //     bottom: actionsPanel.top
            //     bottomMargin: UM.Theme.getSize("default_margin").height
            // }

        //     border.width: UM.Theme.getSize("default_lining").width
        //     border.color: UM.Theme.getColor("lining")
        //     color: UM.Theme.getColor("main_background")

        //     cornerSide: Cura.RoundedRectangle.Direction.Left
        //     radius: UM.Theme.getSize("default_radius").width

            // Cura.PrintMonitor {
            //     width: parent.width
            //     anchors
            //     {
            //         left: parent.left
            //         leftMargin: UM.Theme.getSize("default_margin").width
            //         right: parent.right
            //         rightMargin: UM.Theme.getSize("default_margin").width
            //     }
            // }
        // }

        // Cura.RoundedRectangle
        // {
        //     id: actionsPanel
        //     border.width: UM.Theme.getSize("default_lining").width
        //     border.color: UM.Theme.getColor("lining")
        //     color: UM.Theme.getColor("main_background")

        //     cornerSide: Cura.RoundedRectangle.Direction.Left
        //     radius: UM.Theme.getSize("default_radius").width

        //     anchors.bottom: parent.bottom
        //     anchors.right: parent.right

        //     width: UM.Theme.getSize("print_setup_widget").width
        //     height: monitorButton.height + UM.Theme.getSize("default_margin").height
            
            // Cura.MonitorButton
            // {
            //     id: monitorButton
            //     width: parent.width
            //     anchors.top: parent.top
            //     anchors.topMargin: UM.Theme.getSize("default_margin").height
            // }
        // }
    }
}