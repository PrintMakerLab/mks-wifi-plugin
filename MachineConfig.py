# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Application import Application

from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.MachineAction import MachineAction
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject

import os.path
import json
import time

from PyQt5.QtCore import QTimer

catalog = i18nCatalog("mksplugin")

class MachineConfig(MachineAction):
    def __init__(self, parent=None):
        super().__init__("MachineConfig", catalog.i18nc("@action", "MKS WiFi Plugin"))
        self._qml_url = os.path.join("qml", "MachineConfig.qml")
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._application = CuraApplication.getInstance()
        self._network_plugin = None
        self.__additional_components_view = None

        # Try to get version information from plugin.json
        plugin_file_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "plugin.json")
        try:
            with open(plugin_file_path, encoding="utf-8") as plugin_file:
                plugin_info = json.load(plugin_file)
                self._plugin_version = plugin_info["version"]
        except Exception as e:
            # The actual version info is not critical to have so we can continue
            self._plugin_version = "0.0"
            Logger.logException(
                "w", "Could not get version information for the plugin: " + str(e))

        # Try to get screenshot settings from screenshot.json
        screenshot_file_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "config", "screenshot.json")
        try:
            with open(screenshot_file_path, encoding="utf-8") as screenshot_file:
                self.screenshot_info = json.load(screenshot_file)
        except Exception as e:
            self.screenshot_info = []
            Logger.logException(
                "w", "Could not get information for the screenshot options: " + str(e))

        self._user_agent = ("%s/%s %s/%s" % (
            self._application.getApplicationName(),
            self._application.getVersion(),
            "MKSWifiPlugin",
            self._plugin_version
        )).encode()

        self._application.engineCreatedSignal.connect(
            self._createAdditionalComponentsView)

    printersChanged = pyqtSignal()
    printersTryToConnect = pyqtSignal()

    @pyqtProperty(str, constant=True)
    def pluginVersion(self) -> str:
        return self._plugin_version

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting printer discovery.")
            self._network_plugin = self._application.getOutputDeviceManager(
            ).getOutputDevicePlugin(self._plugin_id)
            if not self._network_plugin:
                return
            self._network_plugin.printerListChanged.connect(
                self._onPrinterDiscoveryChanged)
            self.printersChanged.emit()

    # Re-filters the list of printers.
    @pyqtSlot()
    def reset(self):
        Logger.log("d", "Reset the list of found printers.")
        self.printersChanged.emit()

    @pyqtSlot(str, str)
    def removePrinter(self, address):
        if not self._network_plugin:
            return

        key = "mks:%s" % (address)

        self._network_plugin.mks_remove_printer_from_list(key, address)

    @pyqtSlot(str, str)
    def setPrinter(self, prev_address, address):
        if prev_address == "" and address != "":
            self._network_plugin.mks_add_printer_to_list(address)

        if prev_address != "" and address != "":
            self._network_plugin.mks_edit_printer_in_list(prev_address, address)
            
    def _onPrinterDiscoveryChanged(self, *args):
        self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify=printersChanged)
    def foundDevices(self):
        if self._network_plugin:
            printers = self._network_plugin.getPrinters()
            printers.sort()
            return printers
        else:
            return []

    @pyqtSlot(str)
    def mks_disconnect_printer(self, address):
        Logger.log("d", "mks_disconnect_printer %s" % address)
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_current_ip" in meta_data:
                global_container_stack.setMetaDataEntry(
                    "mks_current_ip", None)
                global_container_stack.removeMetaDataEntry(
                    "mks_current_ip")
        if self._network_plugin:
            self._network_plugin.mks_current_ip_recheck()

    @pyqtSlot(str)
    def mks_connect_printer(self, address):
        Logger.log("d", "mks_connect_printer %s", address)
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            global_container_stack.setMetaDataEntry("mks_current_ip", address)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.mks_current_ip_recheck()

    @pyqtSlot(result=bool)
    def pluginEnabled(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_support" in meta_data:
                return True
        return False

    @pyqtSlot()
    def pluginEnable(self):
        Logger.log("d", "Try to turn MKS WiFi Plugin ON")
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_support" in meta_data:
                Logger.log("d", "Already ON")
                return
            global_container_stack.setMetaDataEntry("mks_support", "true")

    @pyqtSlot()
    def pluginDisable(self):
        Logger.log("d", "Try to turn MKS WiFi Plugin OFF")
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            global_container_stack.setMetaDataEntry("mks_support", None)
            global_container_stack.removeMetaDataEntry("mks_support")
            global_container_stack.setMetaDataEntry("mks_max_filename_len", None)
            global_container_stack.removeMetaDataEntry("mks_max_filename_len")
            global_container_stack.setMetaDataEntry("mks_screenshot_index", None)
            global_container_stack.removeMetaDataEntry("mks_screenshot_index")
            global_container_stack.setMetaDataEntry("mks_simage", None)
            global_container_stack.removeMetaDataEntry("mks_simage")
            global_container_stack.setMetaDataEntry("mks_gimage", None)
            global_container_stack.removeMetaDataEntry("mks_gimage")
            global_container_stack.setMetaDataEntry("mks_current_ip", None)
            global_container_stack.removeMetaDataEntry("mks_current_ip")
            global_container_stack.setMetaDataEntry("mks_ip_list", None)
            global_container_stack.removeMetaDataEntry("mks_ip_list")
            # It will be legacy soon
            global_container_stack.setMetaDataEntry("mks_network_key", None)
            global_container_stack.removeMetaDataEntry("mks_network_key")

    @pyqtSlot(result=bool)
    def WiFiSupportEnabled(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_ip_list" in meta_data:
                return True
        return False
    
    @pyqtSlot(result=str)
    def getMaxFilenameLen(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_max_filename_len" in meta_data:
                return global_container_stack.getMetaDataEntry("mks_max_filename_len")
        return ""

    @pyqtSlot(str)
    def setMaxFilenameLen(self, filename_len):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if filename_len != "":
                global_container_stack.setMetaDataEntry("mks_max_filename_len", filename_len)
            else:
                global_container_stack.setMetaDataEntry("mks_max_filename_len", None)
                global_container_stack.removeMetaDataEntry("mks_max_filename_len")

    @pyqtSlot(result=bool)
    def supportScreenshot(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_simage" in meta_data or "mks_gimage" in meta_data:
                return True
        return False

    @pyqtSlot(result="QVariantList")
    def getScreenshotOptions(self):
        Logger.log("d", "Trying to get screenshot options")
        options = sorted(self.screenshot_info, key=lambda k: k['index'])
        result = []
        result.append({"key": catalog.i18nc("@label", "Custom"), "value": 0})
        for option in options:
            result.append({"key": option["label"], "value": option["index"]}) 
        Logger.log("d", "Get screenshot options done")
        return result

    @pyqtSlot(str, result="QVariant")
    def getScreenshotSettings(self, label):
        Logger.log("d", "Get screenshot settings for: "+ label)
        result = {"simage": "", "gimage": ''}
        options = sorted(self.screenshot_info, key=lambda k: k['index'])
        for option in options:
            value = option["label"]
            if value == label:
                result["simage"] = option["simage"]
                result["gimage"] = option["gimage"]
        return result

    @pyqtSlot(str)
    def setScreenshotIndex(self, index):
        Logger.log("d", "Trying to set screenshot index")
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if index != "":
                global_container_stack.setMetaDataEntry("mks_screenshot_index", index)        
                Logger.log("d", "Screenshot index - updated to "+ str(index))
            else:
                global_container_stack.setMetaDataEntry("mks_screenshot_index", None)
                global_container_stack.removeMetaDataEntry("mks_screenshot_index")          
                Logger.log("d", "Screenshot index - removed")      
        Logger.log("d", "Set screenshot index - completed")

    @pyqtSlot(result=str)
    def getScreenshotIndex(self):
        Logger.log("d", "Trying to get screenshot index")
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_screenshot_index" in meta_data:
                index = global_container_stack.getMetaDataEntry("mks_screenshot_index")
                Logger.log("d", "Current screenshot index is "+ str(index))
                return index
        Logger.log("d", "Can't get screenshot settings, use default index value")
        return "0"

    @pyqtSlot(result=str)
    def getSimage(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_simage" in meta_data:
                return global_container_stack.getMetaDataEntry("mks_simage")
        return ""

    @pyqtSlot(result=str)
    def getGimage(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_gimage" in meta_data:
                return global_container_stack.getMetaDataEntry("mks_gimage")
        return ""

    @pyqtSlot(str)
    def setSimage(self, simage):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if simage != "":
                global_container_stack.setMetaDataEntry("mks_simage", simage)
            else:
                global_container_stack.setMetaDataEntry("mks_simage", None)
                global_container_stack.removeMetaDataEntry("mks_simage")

    @pyqtSlot(str)
    def setGimage(self, gimage):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if gimage != "":
                global_container_stack.setMetaDataEntry("mks_gimage", gimage)
            else:
                global_container_stack.setMetaDataEntry("mks_gimage", None)
                global_container_stack.removeMetaDataEntry("mks_gimage")

    @pyqtSlot()
    def printtest(self):
        Logger.log("d", "mks ready for click")

    @pyqtSlot(result=str)
    def getCurrentAddress(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_current_ip" in meta_data:
                return global_container_stack.getMetaDataEntry("mks_current_ip")
        return ""

    @pyqtSlot()
    def loadConfigurationFromPrinter(self):
        machine_manager = self._application.getMachineManager()
        hotend_ids = machine_manager.printerOutputDevices[0].hotendIds
        for index in range(len(hotend_ids)):
            machine_manager.printerOutputDevices[0].hotendIdChanged.emit(
                index, hotend_ids[index])
        material_ids = machine_manager.printerOutputDevices[0].materialIds
        for index in range(len(material_ids)):
            machine_manager.printerOutputDevices[0].materialIdChanged.emit(
                index, material_ids[index])

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for tft35.")

        # Create networking dialog
        path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml",  "MKSConnectBtn.qml")
        self.__additional_components_view = CuraApplication.getInstance(
        ).createQmlComponent(path, {"manager": self})
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

        # Create extra components
        self._application.addAdditionalComponent(
            "monitorButtons", self.__additional_components_view.findChild(QObject, "networkPrinterConnectButton"))
        self._application.addAdditionalComponent(
            "machinesDetailPane", self.__additional_components_view.findChild(QObject, "networkPrinterConnectionInfo"))

    def _onContainerAdded(self, container):
        # Add this action as a supported action to all machine definitions
        if isinstance(container, DefinitionContainer) and container.getMetaDataEntry(
                "type") == "machine" and container.getMetaDataEntry("supports_usb_connection"):
            self._application.getMachineActionManager(
            ).addSupportedAction(container.getId(), self.getKey())
