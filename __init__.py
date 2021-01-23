import os, json

from . import MKSOutputDevicePlugin
from . import MachineConfig
from UM.i18n import i18nCatalog
from PyQt5.QtQml import qmlRegisterType
from . import NetworkMJPGImage

catalog = i18nCatalog("cura")

from UM.Version import Version
from UM.Application import Application
from UM.Logger import Logger

def getMetaData():
    return {}

def register(app):
    if __matchVersion():
        qmlRegisterType(NetworkMJPGImage.NetworkMJPGImage, "MKSPlugin", 1, 0, "NetworkMJPGImage")
        return {
            "output_device": MKSOutputDevicePlugin.MKSOutputDevicePlugin(),
            "machine_action": MachineConfig.MachineConfig()
        }
    else:
        Logger.log("w", "Plugin not loaded because of a version mismatch")
        return {}

def __matchVersion():
    cura_version = Application.getInstance().getVersion()
    if cura_version == "master":
        Logger.log("d", "Running Cura from source; skipping version check")
        return True
    cura_version = Version(cura_version)
    cura_version = Version([cura_version.getMajor(), cura_version.getMinor()])

    # Get version information from plugin.json
    plugin_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.json")
    try:
        with open(plugin_file_path, encoding="utf-8")  as plugin_file:
            plugin_info = json.load(plugin_file)
            minimum_cura_version = Version(plugin_info["minimum_cura_version"])
            maximum_cura_version = Version(plugin_info["maximum_cura_version"])
    except Exception as e:
        Logger.log("w", "Could not get version information for the plugin: "+str(e))
        return False

    if cura_version >= minimum_cura_version and cura_version <= maximum_cura_version:
        return True
    else:
        Logger.log("d", "This version of the plugin is not compatible with this version of Cura. Please check for an update.")
        return False