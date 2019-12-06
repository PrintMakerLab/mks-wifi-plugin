from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.MachineAction import MachineAction
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QUrl, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager

import os.path
import json
import base64
import time

catalog = i18nCatalog("cura")

class MachineConfig(MachineAction):
    def __init__(self, parent=None):
        super().__init__("MachineConfig", catalog.i18nc("@action", "MKS WIFI"))
        self._qml_url = "MachineConfig.qml"
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._network_plugin = None

        self.__additional_components_context = None
        self.__additional_component = None
        self.__additional_components_view = None

        CuraApplication.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

        self._last_zeroconf_event_time = time.time()
        self._zeroconf_change_grace_period = 0.25  # Time to wait after a zeroconf service change before allowing a zeroconf reset

    printersChanged = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting printer discovery.")
            self._network_plugin = CuraApplication.getInstance().getOutputDeviceManager().getOutputDevicePlugin(
                "MKS Plugin")
            self._network_plugin.printerListChanged.connect(self._onPrinterDiscoveryChanged)
            self.printersChanged.emit()

    ##  Re-filters the list of printers.
    @pyqtSlot()
    def reset(self):
        Logger.log("d", "Reset the list of found printers.")
        self.printersChanged.emit()

    @pyqtSlot()
    def restartDiscovery(self):
        # Ensure that there is a bit of time after a printer has been discovered.
        # This is a work around for an issue with Qt 5.5.1 up to Qt 5.7 which can segfault if we do this too often.
        # It's most likely that the QML engine is still creating delegates, where the python side already deleted or
        # garbage collected the data.
        # Whatever the case, waiting a bit ensures that it doesn't crash.
        if time.time() - self._last_zeroconf_event_time > self._zeroconf_change_grace_period:
            if not self._network_plugin:
                self.startDiscovery()
            else:
                self._network_plugin.startDiscovery()

    @pyqtSlot(str, str)
    def removeManualPrinter(self, key, address):
        if not self._network_plugin:
            return

        self._network_plugin.removeManualPrinter(key, address)

    @pyqtSlot(str, str)
    def setManualPrinter(self, key, address):
        if key != "":
            # This manual printer replaces a current manual printer
            self._network_plugin.removeManualPrinter(key)

        if address != "":
            self._network_plugin.addManualPrinter(address)

    def _onPrinterDiscoveryChanged(self, *args):
        self._last_zeroconf_event_time = time.time()
        self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify=printersChanged)
    def foundDevices(self):
        if self._network_plugin:
            printers = list(self._network_plugin.getPrinters().values())
            printers.sort(key = lambda k: k.name)
            # printers = list(["1, 2, 3", "2, 2, 3", "3, 3, 2"])
            return printers
        else:
            return []

    @pyqtProperty("QVariantList")
    def getSDFiles(self):
        printers = list(["1, 2, 3", "2, 2, 3", "3, 3, 2"])
        return printers

    @pyqtSlot(str)
    def setKey(self, key):
        Logger.log("d", "MKS Plugin Plugin the network key of the active machine to %s", key)
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("mks_network_key", key)
                # Delete old authentication data.
                global_container_stack.removeMetaDataEntry("network_authentication_id")
                global_container_stack.removeMetaDataEntry("network_authentication_key")
            else:
                Logger.log("d", "MKS Plugin Plugin add dataEntry")
                global_container_stack.setMetaDataEntry("mks_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot()
    def printtest(self):
        Logger.log("d", "mks ready for click")

    @pyqtSlot(result=str)
    def getStoredKey(self):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_network_key" in meta_data:
                return global_container_stack.getMetaDataEntry("mks_network_key")

        return ""

    @pyqtSlot()
    def loadConfigurationFromPrinter(self):
        machine_manager = CuraApplication.getInstance().getMachineManager()
        hotend_ids = machine_manager.printerOutputDevices[0].hotendIds
        for index in range(len(hotend_ids)):
            machine_manager.printerOutputDevices[0].hotendIdChanged.emit(index, hotend_ids[index])
        material_ids = machine_manager.printerOutputDevices[0].materialIds
        for index in range(len(material_ids)):
            machine_manager.printerOutputDevices[0].materialIdChanged.emit(index, material_ids[index])

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for tft35.")

        # Create networking dialog
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MKSConnectBtn.qml")
        # self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

        # Create extra components
        CuraApplication.getInstance().addAdditionalComponent("monitorButtons",
                                                         self.__additional_components_view.findChild(QObject,
                                                                                                     "networkPrinterConnectButton"))
        CuraApplication.getInstance().addAdditionalComponent("machinesDetailPane",
                                                         self.__additional_components_view.findChild(QObject,
                                                                                                     "networkPrinterConnectionInfo"))

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry(
                "type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            CuraApplication.getInstance().getMachineActionManager().addSupportedAction(container.getId(), self.getKey())