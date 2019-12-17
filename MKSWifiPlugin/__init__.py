from . import MKSOutputDevicePlugin
from . import MachineConfig
from UM.i18n import i18nCatalog
from PyQt5.QtQml import qmlRegisterType
from . import NetworkMJPGImage
catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
	qmlRegisterType(NetworkMJPGImage.NetworkMJPGImage, "MKSPlugin", 1, 0, "NetworkMJPGImage")
	return {
        "output_device": MKSOutputDevicePlugin.MKSOutputDevicePlugin(),
        "machine_action": MachineConfig.MachineConfig()
    }