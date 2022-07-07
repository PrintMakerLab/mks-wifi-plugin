# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
import os, json

from . import MKSOutputDevicePlugin
from . import MachineConfig
from PyQt6.QtQml import qmlRegisterType
from UM.i18n import i18nCatalog
from UM.Version import Version
from UM.Application import Application
from UM.Logger import Logger

catalog = i18nCatalog("cura")


def getMetaData():
    return {}

#   \param app The application that the plug-in needs to register with.
def register(app):
    if match_version():
        qmlRegisterType(MKSOutputDevicePlugin.MKSOutputDevicePlugin, "MKSPlugin", 1, 0, "MKSOutputDevicePlugin")
        return {
            "output_device": MKSOutputDevicePlugin.MKSOutputDevicePlugin(),
            "machine_action": MachineConfig.MachineConfig()
        }
    else:
        Logger.log("w", "Plugin not loaded because of a version mismatch")
        return {}

def match_version():
    cura_version = Application.getInstance().getVersion()
    if cura_version == "master":
        Logger.log("d", "Running Cura from source. Skipping version check")
        return True
    if cura_version == "Arachne_engine_alpha":
        Logger.log("d", "Running Cura Arachne_engine_alpha. Skipping version check")
        return True
    if cura_version == "Arachne_engine_beta":
        Logger.log("d", "Running Cura Arachne_engine_beta. Skipping version check")
        return True
    if cura_version == "Arachne_engine_beta_2":
        Logger.log("d", "Running Cura Arachne_engine_beta_2. Skipping version check")
        return True
    cura_version = Version(cura_version)
    cura_version = Version([cura_version.getMajor(), cura_version.getMinor()])

    # Get version information from plugin.json
    plugin_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.json")
    try:
        with open(plugin_file_path, encoding="utf-8")  as plugin_file:
            plugin_info = json.load(plugin_file)
            minimum_cura_version = Version(plugin_info["minimum_cura_version"])
    except Exception as e:
        Logger.log("w", "Could not get version information for the plugin: "+str(e))
        return False

    if cura_version >= minimum_cura_version:
        return True
    else:
        Logger.log("d", "This version of MKS WiFi Plugin is not compatible with current version of Cura (%s). Please check for an update." % (Application.getInstance().getVersion()))
        return False
