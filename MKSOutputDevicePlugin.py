# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import MKSOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Logger import Logger

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty
from queue import Queue
from threading import Event, Thread

from UM.Message import Message
from UM.i18n import i18nCatalog

import time
import os

from cura.CuraApplication import CuraApplication
from . import Constants
from . import MKSPreview

catalog = i18nCatalog("mksplugin")


@signalemitter
class MKSOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self.init_translations()
        self._zero_conf = None
        self._browser = None
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

        self._service_changed_request_queue = Queue()
        self._service_changed_request_event = Event()
        self._service_changed_request_thread = Thread(target=self._handleOnServiceChangedRequests,
                                                      daemon=True)
        self._service_changed_request_thread.start()

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
        self.stop()
        if self._browser:
            self._browser.cancel()
            self._browser = None
            self._printers = {}
            self.printerListChanged.emit()
        self._zero_conf = Zeroconf()
        self._browser = ServiceBrowser(self._zero_conf, u'_mks._tcp.local.', [
                                       self._appendServiceChangedRequest])
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

    def stop(self):
        if self._zero_conf is not None:
            Logger.log("d", "zeroconf close...")
            self._zero_conf.close()

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

    def _checkInfo(self, name, info):
        type_of_device = info.properties.get(b"type", None)
        if type_of_device:
            if type_of_device == b"printer":
                address = '.'.join(map(lambda n: str(n), info.address))
                if address in self._excluded_addresses:
                    Logger.log("d",
                                "The IP address %s of the printer \'%s\' is not correct. Trying to reconnect.",
                                address, name)
                    return False  # When getting the localhost IP, then try to reconnect
                self.addPrinterSignal.emit(
                    str(name), address, info.properties)
            else:
                Logger.log("w",
                            "The type of the found device is '%s', not 'printer'! Ignoring.." % type_of_device)
        return True

    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            Logger.log("d", "Bonjour service added: %s" % name)

            # First try getting info from zeroconf cache
            info = ServiceInfo(service_type, name, properties={})
            for record in zeroconf.cache.entries_with_name(name.lower()):
                info.update_record(zeroconf, time.time(), record)

            for record in zeroconf.cache.entries_with_name(info.server):
                info.update_record(zeroconf, time.time(), record)
                if info.address:
                    break

            # Request more data if info is not complete
            if not info.address:
                Logger.log("d", "Trying to get address of %s", name)
                info = zeroconf.get_service_info(service_type, name)

            if info:
                if self._checkInfo(name, info) == False:
                    return False
            else:
                Logger.log("w", "Could not get information about %s" % name)
                return False

        elif state_change == ServiceStateChange.Removed:
            Logger.log("d", "Bonjour service removed: %s" % name)
            self.removePrinterSignal.emit(str(name))

        return True

    def _appendServiceChangedRequest(self, zeroconf, service_type, name, state_change):
        # append the request and set the event so the event handling thread can pick it up
        item = (zeroconf, service_type, name, state_change)
        self._service_changed_request_queue.put(item)
        self._service_changed_request_event.set()

    def _handleAllPendingRequests(self):
        # a list of requests that have failed so later they will get re-scheduled
        reschedule_requests = []
        while not self._service_changed_request_queue.empty():
            request = self._service_changed_request_queue.get()
            zeroconf, service_type, name, state_change = request
            try:
                result = self._onServiceChanged(
                    zeroconf, service_type, name, state_change)
                if not result:
                    reschedule_requests.append(request)
            except Exception:
                Logger.logException("e",
                                    "Failed to get service info for [%s] [%s], the request will be rescheduled",
                                    service_type, name)
                reschedule_requests.append(request)

        # re-schedule the failed requests if any
        if reschedule_requests:
            for request in reschedule_requests:
                self._service_changed_request_queue.put(request)

    def _handleOnServiceChangedRequests(self):
        while True:
            # wait for the event to be set
            self._service_changed_request_event.wait(timeout=5.0)
            # stop if the application is shutting down
            if Application.getInstance().isShuttingDown():
                return

            self._service_changed_request_event.clear()

            # handle all pending requests
            self._handleAllPendingRequests()
