# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import MKSOutputDevice

from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Logger import Logger

from PyQt5.QtCore import QObject

from UM.Message import Message
from UM.i18n import i18nCatalog

from . import Constants, MKSPreview

catalog = i18nCatalog("mksplugin")

@signalemitter
class MKSOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self.init_translations()
        self._current_printer = None
        self._error_message = None

        Application.getInstance().globalContainerStackChanged.connect(self.mks_current_ip_recheck)

        Application.getInstance().getOutputDeviceManager().writeStarted.connect(MKSPreview.add_preview)

    _translations = {}

    def init_translations(self):
        self._translations = {
            "connected": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "<message>{0}</message> printer connected successfully!"),
            "disconnected": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "<message>{0}</message> printer disconnected!")
        }

    printerListChanged = Signal()

    def mks_current_ip_check(self):
        Logger.log("d", "mks_current_ip_check called")
        active_machine = Application.getInstance().getGlobalContainerStack()
        if active_machine:
            meta_data = active_machine.getMetaData()
            if Constants.CURRENT_IP in meta_data:
                address = active_machine.getMetaDataEntry(Constants.CURRENT_IP)
                self.addPrinter(address)

    def mks_current_ip_recheck(self):
        Logger.log("d", "mks_current_ip_recheck called")
        # closing previous printer
        if self._current_printer:
            self.mks_remove_output_device(self._current_printer.getKey())
        # checking new printer got mks_current_ip
        self.mks_current_ip_check()

    def start(self):
        Logger.log("d", "start called")
        # self.startDiscovery()
        self.mks_current_ip_check()
        
    def startDiscovery(self):
        Logger.log("d", "startDiscovery called")

    def addPrinter(self, address):
        Logger.log("d", "addPrinter %s" % (address))
        instance_name = "mks:%s" % address

        active_printer_name = Application.getInstance().getGlobalContainerStack().getName()

        properties = {
            b"name": active_printer_name.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"manual": b"true",
            b"incomplete": b"false"
        }

        self._current_printer = MKSOutputDevice.MKSOutputDevice(instance_name, address, properties)

        Logger.log("d", "addPrinter, connecting [%s]..." % self._current_printer.getKey())
        self._current_printer.connect()
        self._current_printer.connectionStateChanged.connect(
            self._onPrinterConnectionStateChanged)

    def mks_remove_output_device(self, key):
        Logger.log("d", "mks_remove_output_device %s" % key)
        if self._current_printer:
            self._current_printer.disconnect()
            self._current_printer.connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
            self._current_printer = None
            if self.getOutputDeviceManager().getOutputDevice(key):
                self.getOutputDeviceManager().removeOutputDevice(key)

    def mks_add_printer_to_list(self, address):
        Logger.log("d", "mks_add_printer_to_list %s" % (address))

        active_machine = Application.getInstance().getGlobalContainerStack()
        
        ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)

        if ip_list_entry:
            ip_list = ip_list_entry.split(",")
            ip_list.append(address)
            active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
        else:
            active_machine.setMetaDataEntry(Constants.IP_LIST, address)
        self.printerListChanged.emit()

    def mks_remove_printer_from_list(self, address):
        Logger.log("d", "mks_remove_printer_from_list %s" % (address))
        active_machine = Application.getInstance().getGlobalContainerStack()

        if active_machine.getMetaDataEntry(Constants.CURRENT_IP) == self._current_printer:
            active_machine.setMetaDataEntry(Constants.CURRENT_IP, None)
            active_machine.removeMetaDataEntry(Constants.CURRENT_IP)

        if address:
            ip_list = active_machine.getMetaDataEntry(Constants.IP_LIST).split(",")

            ip_list.remove(address)

            if ip_list:
                active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
            else:
                active_machine.setMetaDataEntry(Constants.IP_LIST, None)
                active_machine.removeMetaDataEntry(Constants.IP_LIST)

        if self._current_printer and self._current_printer.address == address:
            self.mks_remove_output_device(self._current_printer.getKey())
            
        self.printerListChanged.emit()

    def mks_edit_printer_in_list(self, prev_address, address):
        active_machine = Application.getInstance().getGlobalContainerStack()

        ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)

        if ip_list_entry:
            ip_list = ip_list_entry.split(",")
            if prev_address != "":
                ip_list.remove(prev_address)
            if address != "":
                ip_list.append(address)
            active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
            
        self.printerListChanged.emit()

    def getPrinters(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)
        if ip_list_entry:
            return ip_list_entry.split(",")
        return []

    def _onPrinterConnectionStateChanged(self, key):
        if self._current_printer.getKey() != key:
            Logger.log("w", "_current_printer.getKey != %s" % key)

        if self._current_printer.isConnected:
            if self._error_message:
                self._error_message.hide()
            self._error_message = Message(self._translations.get("connected").format(
                self._current_printer._properties.get(b"name", b"").decode("utf-8")))
            self._error_message.show()
            self.getOutputDeviceManager().addOutputDevice(self._current_printer)
        else:
            if self.getOutputDeviceManager().getOutputDevice(key):
                self._error_message = Message(self._translations.get("disconnected").format(
                    self._current_printer._properties.get(b"name", b"").decode("utf-8")))
                self._error_message.show()
                self.getOutputDeviceManager().removeOutputDevice(self._current_printer.getKey())
