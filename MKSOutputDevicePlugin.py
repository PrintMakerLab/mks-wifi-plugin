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

from cura.CuraApplication import CuraApplication
from . import Constants
from . import MKSPreview

catalog = i18nCatalog("mksplugin")


@signalemitter
class MKSOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self.init_translations()
        self._printers = {}
        self._discovered_devices = {}

        self._error_message = None

        self.addPrinterSignal.connect(self.addPrinter)
        self.removePrinterSignal.connect(self.removePrinter)

        self._preferences = Application.getInstance().getPreferences()

        Logger.log("d", self._preferences.getValue(Constants.MANUAL_INSTANCES).split(","))

        self._preferences.addPreference(Constants.MANUAL_INSTANCES, "")
        self._manual_instances = self._preferences.getValue(
            Constants.MANUAL_INSTANCES).split(",")
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        Application.getInstance().getOutputDeviceManager().writeStarted.connect(MKSPreview.add_preview)

    _translations = {}

    def init_translations(self):
        self._translations = {
            "connected": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "<message>{0}</message> printer connected successfully!")
        }

    addPrinterSignal = Signal()
    removePrinterSignal = Signal()
    printerListChanged = Signal()

    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        Logger.log("d", "Starting printer discovery.")
        for address in self._manual_instances:
            if address:
                self.addManualPrinter(address)

    def addManualPrinter(self, address):
        if address not in self._manual_instances:
            self._manual_instances.append(address)
            self._preferences.setValue(
                Constants.MANUAL_INSTANCES, ",".join(self._manual_instances))

        active_printer_name = Application.getInstance().getGlobalContainerStack().getName()

        instance_name = "manual:%s" % address
        properties = {
            b"name": active_printer_name.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"manual": b"true",
            b"incomplete": b"false"
        }

        if instance_name not in self._printers:
            # Add a preliminary printer instance
            self.addPrinter(instance_name, address, properties)

    def removeManualPrinter(self, key, address=None):
        if key in self._printers:
            if not address:
                address = self._printers[key].ipAddress
            self.removePrinter(key)

        if address in self._manual_instances:
            self._manual_instances.remove(address)
            self._preferences.setValue(
                Constants.MANUAL_INSTANCES, ",".join(self._manual_instances))

    def getPrinters(self):
        return self._printers

    def mks_remove_output_device(self, key):
        Logger.log("d", "mks_remove_output_device %s" % key)
        if key in self._printers:
            self._printers[key].disconnect()
            self._printers[key].connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
            self.getOutputDeviceManager().removeOutputDevice(key)
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("mkswifi/stopupdate", "True")

    def reCheckConnections(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if not active_machine:
            return
        Logger.log("d", "GlobalContainerStack change %s" %
                   active_machine.getMetaDataEntry("mks_network_key"))
        for key in self._printers:
            if key == active_machine.getMetaDataEntry("mks_network_key"):
                if not self._printers[key].isConnected:
                    Logger.log("d", "Connecting [%s]..." % key)
                    self._printers[key].connect()
                    self._printers[key].connectionStateChanged.connect(
                        self._onPrinterConnectionStateChanged)
                self._printers[key]._properties.update({b"name": Application.getInstance(
                ).getGlobalContainerStack().getName().encode("utf-8")})
            else:
                if self._printers[key].isConnected:
                    Logger.log("d", "Closing connection [%s]..." % key)
                    self._printers[key].disconnect()
                    self._printers[key].connectionStateChanged.disconnect(
                        self._onPrinterConnectionStateChanged)

    def addPrinter(self, name, address, properties):
        printer = MKSOutputDevice.MKSOutputDevice(name, address, properties)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        has_key = global_container_stack and printer.getKey(
        ) == global_container_stack.getMetaDataEntry("mks_network_key")
        # Was the printer already connected, but a re-scan forced?
        if has_key:
            Logger.log("d", "addPrinter, connecting [%s]..." % printer.getKey())
            self._printers[printer.getKey()].connect()
            printer.connectionStateChanged.connect(
                self._onPrinterConnectionStateChanged)
        self.printerListChanged.emit()

    def removePrinter(self, name):
        printer = self._printers.pop(name, None)
        if printer and printer.isConnected:
            printer.disconnect()
            printer.connectionStateChanged.disconnect(
                self._onPrinterConnectionStateChanged)
            Logger.log("d", "removePrinter, disconnecting [%s]..." % name)
        self.printerListChanged.emit()

    def _onPrinterConnectionStateChanged(self, key):
        if key not in self._printers:
            Logger.log("w", "no %s in _printers" % key)
            return
        # Logger.log("d", "mks add output device %s" % self._printers[key].())
        if self._printers[key].isConnected:
            # Logger.log("d", "mks add output device--------ok--------- %s" % self._printers[key].isConnected)
            if self._error_message:
                self._error_message.hide()
            self._error_message = Message(self._translations.get("connected").format(
                self._printers[key]._properties.get(b"name", b"").decode("utf-8")))
            self._error_message.show()
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
        else:
            global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
            if global_container_stack:
                meta_data = global_container_stack.getMetaData()
                if "mks_network_key" in meta_data:
                    localkey = global_container_stack.getMetaDataEntry(
                        "mks_network_key")
                    if localkey != key and key in self._printers:
                        # self.getOutputDeviceManager().connect()
                        self.getOutputDeviceManager().removeOutputDevice(key)
