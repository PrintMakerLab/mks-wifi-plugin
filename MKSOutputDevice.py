# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Message import Message
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.CuraApplication import CuraApplication

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
from UM.PluginRegistry import PluginRegistry
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.SettingDefinitionsModel import SettingDefinitionsModel
from UM.Settings.InstanceContainer import InstanceContainer
from cura.Machines.ContainerTree import ContainerTree

from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QFileDialog

from cura.PrinterOutput.GenericOutputController import GenericOutputController

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QTcpSocket
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot, QCoreApplication, Qt, QObject, QByteArray
from queue import Queue

from . import utils

import UM

import re  # For escaping characters in the settings.
import json
import copy
import os.path
import time
import base64
import sys
from enum import IntEnum
from UM.Preferences import Preferences

from typing import cast, Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode  # For typing.
    from UM.FileHandler.FileHandler import FileHandler  # For typing.

from UM.Resources import Resources
from . import Constants, MKSDialog

Resources.addSearchPath(
    os.path.join(os.path.abspath(
        os.path.dirname(__file__))))  # Plugin translation file import

catalog = i18nCatalog("mksplugin")

if catalog.hasTranslationLoaded():
    Logger.log("i", "MKS WiFi Plugin translation loaded!")

class UnifiedConnectionState(IntEnum):
    try:
        Closed = ConnectionState.Closed
        Connecting = ConnectionState.Connecting
        Connected = ConnectionState.Connected
        Busy = ConnectionState.Busy
        Error = ConnectionState.Error
    except AttributeError:
        Closed = ConnectionState.closed  # type: ignore
        Connecting = ConnectionState.connecting  # type: ignore
        Connected = ConnectionState.connected  # type: ignore
        Busy = ConnectionState.busy  # type: ignore
        Error = ConnectionState.error  # type: ignore


@signalemitter
class MKSOutputDevice(NetworkedPrinterOutputDevice):
    version = 3
    """The file format version of the serialised g-code.
    It can only read settings with the same version as the version it was
    written with. If the file format is changed in a way that breaks reverse
    compatibility, increment this version number!
    """

    escape_characters = {
        re.escape("\\"):
        "\\\\",  # The escape character.
        re.escape("\n"):
        "\\n",  # Newlines. They break off the comment.
        # Carriage return. Windows users may need this for visualisation in their editors.
        re.escape("\r"):
        "\\r"
    }
    """Dictionary that defines how characters are escaped when embedded in
    g-code.
    Note that the keys of this dictionary are regex strings. The values are
    not.
    """

    _setting_keyword = ";SETTING_"

    def __init__(self, instance_id: str, address: str, properties: dict,
                 **kwargs) -> None:
        super().__init__(device_id=instance_id,
                         address=address,
                         properties=properties,
                         **kwargs)

        self.init_translations()

        self._address = address
        self._port = 8080
        self._key = instance_id
        self._properties = properties

        self._target_bed_temperature = 0

        self._application = CuraApplication.getInstance()
        if self._application.getVersion().split(".")[0] < "4":
            self._monitor_view_qml_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "qml",
                "MonitorItem.qml")
        else:
            self._monitor_view_qml_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "qml",
                "MonitorItem4x.qml")

        # Make sure the output device gets selected above local file output and Octoprint XD
        self.setPriority(3)
        self._active_machine = CuraApplication.getInstance().getMachineManager(
        ).activeMachine
        self.setName(instance_id)
        self.setShortDescription(
            self._translations.get("print_over_tft_action_button"))
        self.setDescription(self._translations.get("print_over_tft_tooltip"))
        self.setIconName("print")
        self.setConnectionText(
            self._translations.get("connected_message").format(self._key))
        Application.getInstance().globalContainerStackChanged.connect(
            self._onGlobalContainerChanged)

        self._socket = None
        self._gl = None
        self._command_queue = Queue()
        self._isPrinting = False
        self._isPause = False
        self._isSending = False
        self._gcode = None
        self._isConnect = False
        self._printing_filename = ""
        self._printing_progress = 0
        self._printing_time = 0
        self._start_time = 0
        self._pause_time = 0
        self.last_update_time = 0
        self.angle = 10
        self._connection_state_before_timeout = None
        self._sdFileList = False
        self.sdFiles = []
        self._mdialog = None
        self._mfilename = None
        self._uploadpath = ''

        self._settings_reply = None
        self._printer_reply = None
        self._job_reply = None
        self._command_reply = None

        self._image_reply = None
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        self._post_reply = None
        self._post_multi_part = None
        self._post_part = None
        self._last_file_name = None
        self._last_file_path = None

        self._progress_message = None
        self._error_message = None
        self._connection_message = None
        self.__additional_components_view = None

        self._ischanging = False

        self._update_timer = QTimer()
        # TODO; Add preference for update interval
        self._update_timer.setInterval(2000)
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onRequestFinished)

        self._preheat_timer = QTimer()
        self._preheat_timer.setSingleShot(True)
        self._preheat_timer.timeout.connect(self.cancelPreheatBed)
        self._exception_message = None
        self._output_controller = GenericOutputController(self)
        self._number_of_extruders = CuraApplication.getInstance(
        ).getGlobalContainerStack().getProperty("machine_extruder_count",
                                                "value")
        self._camera_url = ""
        # Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        CuraApplication.getInstance().getCuraSceneController(
        ).activeBuildPlateChanged.connect(self.CreateMKSController)

    _translations = {}

    def init_translations(self):
        self._translations = {
            "button_cancel": catalog.i18nc("@action:button", "Cancel"),
            "print_over_tft_action_button": catalog.i18nc("@action:button", "Print over TFT"),
            "print_over_tft_tooltip": catalog.i18nc("@properties:tooltip", "Print over TFT"),
            "connected_message": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "Connected to TFT on <message>{0}</message>"),
            "print_over_action_button": catalog.i18nc("@action:button Don't translate the XML tags <message>!", "Print over <message>{0}</message>"),
            "print_over_tooltip": catalog.i18nc("@properties:tooltip Don't translate the XML tags <message>!", "Print over <message>{0}</message>"),
            "file_exists_title": catalog.i18nc("@info:status Don't translate the XML tags <filename>!", "<filename>{0}</filename> already exists."),
            "file_exists_label": catalog.i18nc("@info:status Don't translate the XML tags <filename>!", "<filename>{0}</filename> already exists, please rename it."),
            "file_include_chinese_title": catalog.i18nc("@info:status", "File name can not include chinese."),
            "file_include_chinese_label": catalog.i18nc("@info:status", "File name can not include chinese, please rename it."),
            "file_too_long_title": catalog.i18nc("@info:status", "File name is too long to upload."),
            "file_too_long_label": catalog.i18nc("@info:status", "File name is too long to upload, please rename it."),
            "sending_file": catalog.i18nc("@info:status", "Sending file to printer"),
            "uploading_file": catalog.i18nc("@info:status", "Uploading print job to printer"),
            "print_job_title": catalog.i18nc("@info:title", "Sending Print Job"),
            "print_job_label": catalog.i18nc("@label", "Print job"),
            "file_cant_transfer": catalog.i18nc("@info:status", "File cannot be transferred during printing."),
            "file_send_failed": catalog.i18nc("@info:status", "Send file to printer failed."),
            "file_send_failed2": catalog.i18nc("@info:status", "Now is printing. Send file to printer failed."),
            "file_send_success": catalog.i18nc("@info:status", "Print job was successfully sent to the printer."),
            "gcode_prepare": catalog.i18nc("@warning:status", "Please prepare G-code before exporting."),
            "connected": catalog.i18nc("@info:status", "TFT Connect succeed"),
            "error_1": catalog.i18nc("@info:status", "Error: command can not send"),
            "error_2": catalog.i18nc("@info:status", "Error: Another file is uploading, please try later."),
            "choose_file": catalog.i18nc("@info:title", "Choose file"),
            "gcode": catalog.i18nc("@label", "G-code"),
            "all": catalog.i18nc("@label", "All"),
        }

    def _onOutputDevicesChanged(self):
        Logger.log("d", "MKS _onOutputDevicesChanged")

    def connect(self):
        if self._socket is not None:
            self._socket.close()
            self._socket.abort()
            self._socket = None
        self._socket = QTcpSocket()
        self._socket.connectToHost(self._address, self._port)
        global_container_stack = CuraApplication.getInstance(
        ).getGlobalContainerStack()
        self.setShortDescription(
            self._translations.get("print_over_action_button").format(
                global_container_stack.getName()))
        self.setDescription(self._translations.get("print_over_tooltip").format(
            global_container_stack.getName()))
        Logger.log("d", "MKS socket connecting ")
        self.setConnectionState(
            cast(ConnectionState, UnifiedConnectionState.Connecting))
        self._setAcceptsCommands(True)
        self._socket.readyRead.connect(self.on_read)
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference(Constants.STOP_UPDATE, "False")
        self._update_timer.start()

    def getProperties(self):
        return self._properties

    @pyqtSlot(str, result=str)
    def getProperty(self, key):
        key = key.encode("utf-8")
        if key in self._properties:
            return self._properties.get(key, b"").decode("utf-8")
        else:
            return ""

    @pyqtSlot(result=str)
    def getKey(self):
        return self._key

    @pyqtProperty(str, constant=True)
    def address(self):
        return self._properties.get(b"address", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address

    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        self._setTargetBedTemperature(temperature)
        if duration > 0:
            self._preheat_timer.setInterval(duration * 1000)
            self._preheat_timer.start()
        else:
            self._preheat_timer.stop()

    @pyqtSlot()
    def cancelPreheatBed(self):
        self._setTargetBedTemperature(0)
        self._preheat_timer.stop()

    @pyqtSlot()
    def printtest(self):
        self.sendCommand("M104 S0\r\n M140 S0\r\n M106 S255")

    @pyqtSlot()
    def openfan(self):
        self.sendCommand("M106 S255")

    @pyqtSlot()
    def closefan(self):
        self.sendCommand("M106 S0")

    @pyqtSlot()
    def unlockmotor(self):
        self.sendCommand("M84")

    @pyqtSlot()
    def e0down(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            self.show_error_message(self._translations.get("error_1"))

    @pyqtSlot()
    def e0up(self):
        if not self._isPrinting:
            self.sendCommand("T0\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            self.show_error_message(self._translations.get("error_1"))

    @pyqtSlot()
    def e1down(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E10 F1000\r\n G90")
        else:
            self.show_error_message(self._translations.get("error_1"))

    @pyqtSlot()
    def e1up(self):
        if not self._isPrinting:
            self.sendCommand("T1\r\n G91\r\n G1 E-10 F1000\r\n G90")
        else:
            self.show_error_message(self._translations.get("error_1"))

    @pyqtSlot(result=int)
    def printer_E_num(self):
        return self._number_of_extruders

    @pyqtSlot()
    def printer_state(self):
        if len(self._printers) <= 0:
            return "offline"
        return self.printers[0].state

    @pyqtSlot()
    def isprinterprinting(self):
        if self._isPrinting:
            return "true"
        return "false"

    @pyqtSlot()
    def selectfile(self):
        if self._last_file_name:
            return True
        else:
            return False

    @pyqtSlot(str)
    def deleteSDFiles(self, filename):
        self._sendCommand("M30 1:/" + filename)
        if filename in self.sdFiles:
            self.sdFiles.remove(filename)
        self._sendCommand("M20")

    @pyqtSlot(str)
    def printSDFiles(self, filename):
        self._sendCommand("M23 " + filename)
        self._sendCommand("M24")

    @pyqtSlot()
    def selectFileToUplload(self):
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference(Constants.AUTO_PRINT, "True")
        preferences.addPreference(Constants.SAVE_PATH, "")
        if self._progress_message:
            self.show_error_message(self._translations.get("error_2"))
        else:
            filename, _ = QFileDialog.getOpenFileName(None, self._translations.get("choose_file"), preferences.getValue(Constants.SAVE_PATH), self._translations.get("gcode") + "(*.gcode *.g *.goc);;" + self._translations.get("all") + "(*.*)")
            preferences.setValue(Constants.SAVE_PATH, filename)
            self._uploadpath = filename
            if ".g" in filename.lower():
                filename = self.check_valid_filepath(filename)
                if self.isBusy():
                    self.isBusy_error_message()
                    return
                if self._progress_message:
                    self.show_error_message(self._translations.get("error_2"))
                else:
                    self.uploadfunc(filename)

    def show_dialog(self, filename, label, title):
        dialog = MKSDialog.MKSDialog()
        dialog.init_dialog(filename, label, title)
        dialog.exec_()
        new_filename = ""
        if dialog.accepted():
        	new_filename = dialog.get_filename()
        dialog.close()
        return new_filename

    def show_exists_dialog(self, filename):
        title = self._translations.get("file_exists_title").format(
            filename[filename.rfind("/") + 1:])
        label = self._translations.get("file_exists_label").format(
            filename[filename.rfind("/") + 1:])
        return self.show_dialog(filename, label, title)

    def show_contains_chinese_dialog(self, filename):
        title = self._translations.get("file_include_chinese_title")
        label = self._translations.get("file_include_chinese_label")
        return self.show_dialog(filename, label, title)

    def show_to_long_dialog(self, filename):
        title = self._translations.get("file_too_long_title")
        label = self._translations.get("file_too_long_label")
        return self.show_dialog(filename, label, title)

    def check_valid_filename(self, filename):
        if filename in self.sdFiles:
            filename = self.check_valid_filename(self.show_exists_dialog(filename))
        if len(filename) >= 30:
            filename = self.check_valid_filename(self.show_to_long_dialog(filename))
        if self.is_contains_chinese(filename):
            filename = self.check_valid_filename(self.show_contains_chinese_dialog(filename))
        return filename

    def check_valid_filepath(self, filepath):
    	filename = filepath[filepath.rfind("/") + 1:]
    	filename = self.check_valid_filename(filename);
    	return filepath[:filepath.rfind("/")] + "/" + filename

    def show_error_message(self, message):
        if self._error_message is not None:
            self._error_message.hide()
        self._error_message = Message(message)
        self._error_message.show()

    def show_progress_message(self, preferences):
        if self._application.getVersion().split(".")[0] < "4":
            Application.getInstance().showPrintMonitor.emit(True)
            status = self._translations.get("sending_file")
            self._progress_message = Message(status, 0, False, -1)
        else:
            status = self._translations.get("uploading_file")
            title = self._translations.get("print_job_title")
            self._progress_message = Message(
                status,
                0,
                False,
                -1,
                title,
                option_text=self._translations.get("print_job_label"),
                option_state=preferences.getValue(Constants.AUTO_PRINT))
            self._progress_message.addAction(
                "Cancel",  self._translations.get("button_cancel"), None, "")
            self._progress_message.actionTriggered.connect(
                self._cancelSendGcode)
            self._progress_message.optionToggled.connect(
                self._onOptionStateChanged)
        self._progress_message.show()

    def isBusy_error_message(self):
        if self._exception_message:
            self._exception_message.hide()
        self._exception_message = Message(
            self._translations.get("file_cant_transfer"))
        self._exception_message.show()

    def is_contains_chinese(self, strs):
        return False

    def uploadfunc(self, filename):
        preferences = Application.getInstance().getPreferences()
        if self._progress_message:
            self.show_error_message(self._translations.get("error_2"))
        else:
            preferences.addPreference(Constants.AUTO_PRINT, "True")
            preferences.addPreference(Constants.SAVE_PATH, "")
            # preferences.addPreference("mkswifi/uploadingfile", "True")
            self._update_timer.stop()
            self._isSending = True
            self._preheat_timer.stop()
            single_string_file_data = ""
            try:
                f = open(self._uploadpath,
                         "r",
                         encoding=sys.getfilesystemencoding())
                single_string_file_data = f.read()
                file_name = filename[filename.rfind("/") + 1:]
                self._last_file_name = filename[filename.rfind("/") + 1:]
                self._progress_message = Message(self._translations.get("uploading_file"), 0, False, -1, self._translations.get(
                    "print_job_title"), option_text=self._translations.get("print_job_label"), option_state=preferences.getValue(Constants.AUTO_PRINT))
                self._progress_message.addAction(
                    "Cancel", self._translations.get("button_cancel"), None, "")
                self._progress_message.actionTriggered.connect(
                    self._cancelSendGcode)
                self._progress_message.optionToggled.connect(
                    self._onOptionStateChanged)
                self._progress_message.show()

                data = QByteArray()
                data.append(single_string_file_data.encode())

                post_request = QNetworkRequest(
                    QUrl("http://%s/upload?X-Filename=%s" %
                         (self._address, file_name)))
                post_request.setRawHeader(b'Content-Type',
                                          b'application/octet-stream')
                post_request.setRawHeader(b'Connection', b'keep-alive')
                self._post_reply = self._manager.post(post_request, data)
                self._post_reply.uploadProgress.connect(self._onUploadProgress)
                self._post_reply.sslErrors.connect(self._onUploadError)
                self._gcode = None
            except IOError as e:
                Logger.log("e", Constants.EXCEPTION_MESSAGE % str(e))
                # preferences.setValue("mkswifi/uploadingfile", "False")
                self._progress_message.hide()
                self._progress_message = None
                self._error_message = Message(
                    self._translations.get("file_send_failed"))
                self._error_message.show()
                self._update_timer.start()
            except Exception as e:
                # preferences.setValue("mkswifi/uploadingfile", "False")
                self._update_timer.start()
                if self._progress_message is not None:
                    self._progress_message.hide()
                    self._progress_message = None
                Logger.log("e", Constants.EXCEPTION_MESSAGE % str(e))

    @ pyqtProperty("QVariantList")
    def getSDFiles(self):
        self._sendCommand("M20")
        return list(self.sdFiles)

    def _setTargetBedTemperature(self, temperature):
        if not self._updateTargetBedTemperature(temperature):
            return
        self._sendCommand(["M140 S%s" % temperature])

    @ pyqtSlot(str)
    def sendCommand(self, cmd):
        self._sendCommand(cmd)

    def _sendCommand(self, cmd):
        in_cmd = "G28" in cmd or "G0" in cmd
        if self._ischanging and in_cmd:
            return
        if self.isBusy() and "M20" in cmd:
            return
        if self._socket and self._socket.state() == 2 or self._socket.state(
        ) == 3:
            if isinstance(cmd, str):
                self._command_queue.put(cmd + "\r\n")
            elif isinstance(cmd, list):
                for each_command in cmd:
                    self._command_queue.put(each_command + "\r\n")

    def disconnect(self):
        # Logger.log("d", "disconnect--------------")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue(Constants.STOP_UPDATE):
            # Logger.log("d", "timer_update MKS wifi stopupdate-----------")
            self._error_message = Message("Printer disconneted.")
            self._error_message.show()
        # self._updateJobState("")
        self._isConnect = False
        self.setConnectionState(
            cast(ConnectionState, UnifiedConnectionState.Closed))
        if self._socket is not None:
            self._socket.readyRead.disconnect(self.on_read)
            self._socket.close()
            # self._socket.abort()
        if self._progress_message:
            self._progress_message.hide()
        if self._error_message:
            self._error_message.hide()
        self._update_timer.stop()

    def isConnected(self):
        return self._isConnect

    def isBusy(self):
        return self._isPrinting or self._isPause

    def requestWrite(self,
                     node,
                     file_name=None,
                     filter_by_machine=False,
                     file_handler=None,
                     **kwargs):
        self.writeStarted.emit(self)
        self._update_timer.stop()
        self._isSending = True
        active_build_plate = Application.getInstance().getMultiBuildPlateModel(
        ).activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):
            self.setInformation(self._translations.get("gcode_prepare"))
            return False
        self._gcode = []
        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)
        if gcode_list is not None:
            has_settings = False
            for gcode in gcode_list:
                if gcode[:len(self._setting_keyword)] == self._setting_keyword:
                    has_settings = True
                self._gcode.append(gcode)
            # Serialise the current container stack and put it at the end of the file.
            if not has_settings:
                settings = self._serialiseSettings(
                    Application.getInstance().getGlobalContainerStack())
                self._gcode.append(settings)
        else:
            self.setInformation(self._translations.get("gcode_prepare"))
            return False

        Logger.log("d", "mks ready for print")
        # preferences = Application.getInstance().getPreferences()
        # if preferences.getValue("mkswifi/uploadingfile"):
        if self._progress_message:
            self.show_error_message(self._translations.get("error_2"))
        else:
            self.startPrint()

    def startPrint(self):
        global_container_stack = CuraApplication.getInstance(
        ).getGlobalContainerStack()
        if not global_container_stack:
            return
        if self._error_message:
            self._error_message.hide()
            self._error_message = None
        if self._progress_message:
            self._progress_message.hide()
            self._progress_message = None
        if self.isBusy():
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            if self._error_message is not None:
                self._error_message.hide()
                self._error_message = None
            self._error_message = Message(
                self._translations.get("file_send_failed2"))
            self._error_message.show()
            return
        job_name = Application.getInstance().getPrintInformation(
        ).jobName.strip()
        if job_name == "":
            job_name = "cura_file"
        filename = "%s.gcode" % job_name

        filename = self.check_valid_filename(filename);

        if self.isBusy():
            self.isBusy_error_message()
            return
        if filename != "":
        	self._startPrint(filename)

    def _messageBoxCallback(self, button):
        if button == QMessageBox.Yes:
            self.startPrint()
        else:
            CuraApplication.getInstance().getController().setActiveStage(
                "PrepareStage")

    def _startPrint(self, file_name="cura_file.gcode"):
        preferences = Application.getInstance().getPreferences()
        global_container_stack = CuraApplication.getInstance(
        ).getGlobalContainerStack()
        if not global_container_stack:
            return
        if self._progress_message:
            self.show_error_message(self._translations.get("error_2"))
            return
        self._preheat_timer.stop()
        try:
            preferences.addPreference(Constants.AUTO_PRINT, "True")
            preferences.addPreference(Constants.SAVE_PATH, "")
            self.show_progress_message(preferences)
            self._last_file_name = file_name
            Logger.log(
                "d", "mks: " + file_name + Application.getInstance().
                getPrintInformation().jobName.strip())
            
            # Adding screeshot section
            single_string_file_data = utils.add_screenshot()
            # End of screeshot section

            last_process_events = time.time()
            for line in self._gcode:
                single_string_file_data += line
                if time.time() > last_process_events + 0.05:
                    QCoreApplication.processEvents()
                    last_process_events = time.time()

            data = QByteArray()
            data.append(single_string_file_data.encode())

            post_request = QNetworkRequest(
                QUrl("http://%s/upload?X-Filename=%s" %
                     (self._address, file_name)))
            post_request.setRawHeader(b'Content-Type',
                                      b'application/octet-stream')
            post_request.setRawHeader(b'Connection', b'keep-alive')
            self._post_reply = self._manager.post(post_request, data)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.sslErrors.connect(self._onUploadError)
            # Logger.log("d", "http://%s:80/upload?X-Filename=%s" % (self._address, file_name))
            self._gcode = None
        except IOError as e:
            Logger.log("e", Constants.EXCEPTION_MESSAGE % str(e))
            self._progress_message.hide()
            self._progress_message = None
            self._error_message = Message(
                self._translations.get("file_send_failed"))
            self._error_message.show()
            self._update_timer.start()
        except Exception as e:
            self._update_timer.start()
            if self._progress_message is not None:
                self._progress_message.hide()
                self._progress_message = None
            Logger.log("e", Constants.EXCEPTION_MESSAGE % str(e))

    def _printFile(self):
        self._sendCommand("M23 " + self._last_file_name)
        self._sendCommand("M24")

    def _onUploadProgress(self, bytes_sent, bytes_total):
        Logger.log("d",
                   "Upload _onUploadProgress bytes_sent %s" % str(bytes_sent))
        Logger.log(
            "d", "Upload _onUploadProgress bytes_total %s" % str(bytes_total))
        if bytes_sent == bytes_total and bytes_sent > 0:
            self._progress_message.hide()
            self._error_message = Message(
                self._translations.get("file_send_success"))
            self._error_message.show()
            CuraApplication.getInstance().getController().setActiveStage(
                "MonitorStage")
        elif bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time.time()
            if new_progress > self._progress_message.getProgress():
                # Ensure that the message is visible.
                self._progress_message.show()
                self._progress_message.setProgress(bytes_sent / bytes_total *
                                                   100)
        else:
            if self._progress_message is not None:
                self._progress_message.setProgress(0)
                self._progress_message.hide()
                self._progress_message = None

    def _onUploadError(self, reply, sslerror):
        Logger.log("d", "Upload Error")
        if self._progress_message is not None:
            self._progress_message.hide()
            self._progress_message = None
        self._error_message = Message(
            self._translations.get("file_send_failed"))
        self._error_message.show()
        self._update_timer.start()

    def _setHeadPosition(self, x, y, z, speed):
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))

    def _setHeadX(self, x, speed):
        self._sendCommand("G0 X%s F%s" % (x, speed))

    def _setHeadY(self, y, speed):
        self._sendCommand("G0 Y%s F%s" % (y, speed))

    def _setHeadZ(self, z, speed):
        self._sendCommand("G0 Z%s F%s" % (z, speed))

    def _homeHead(self):
        # Logger.log("e", "_homeHead_homeHead---------------")
        self._sendCommand("G28 X Y")

    def _homeBed(self):
        self._sendCommand("G28 Z")

    def _moveHead(self, x, y, z, speed):
        self._sendCommand(
            ["G91", "G0 X%s Y%s Z%s F%s" % (x, y, z, speed), "G90"])

    def _update(self):
        # Logger.log("d", "timer_update MKS wifi reconnecting")
        preferencess = Application.getInstance().getPreferences()
        if preferencess.getValue(Constants.STOP_UPDATE):
            self._update_timer.stop()
            return
        if self._socket is not None and (self._socket.state() == 2
                                         or self._socket.state() == 3):
            self.write_socket_data()
        else:
            Logger.log("d", "MKS wifi reconnecting")
            self.disconnect()
            self.connect()

    def write_socket_data(self):
        _send_data = ("M105\r\nM997\r\n", "")[self._command_queue.qsize() > 0]
        if self.isBusy():
            _send_data += "M994\r\nM992\r\nM27\r\n"
        while self._command_queue.qsize() > 0:
            _queue_data = self._command_queue.get()
            if "M23" in _queue_data:
                self._socket.writeData(
                    _queue_data.encode(sys.getfilesystemencoding()))
                continue
            if "M24" in _queue_data:
                self._socket.writeData(
                    _queue_data.encode(sys.getfilesystemencoding()))
                continue
            if self.isBusy() and "M20" in _queue_data:
                continue
            _send_data += _queue_data
        Logger.log("d", "_send_data: \r\n%s" % _send_data)
        self._socket.writeData(_send_data.encode(sys.getfilesystemencoding()))
        self._socket.flush()

    def _setJobState(self, job_state):
        if job_state == "abort":
            command = "M26"
        elif job_state == "print":
            if self._isPause:
                command = "M25"
            else:
                command = "M24"
        elif job_state == "pause":
            command = "M25"
        if command:
            self._sendCommand(command)

    @pyqtSlot()
    def cancelPrint(self):
        # Logger.log("e", "cancelPrint: %s" % str(self._isPause))
        self._sendCommand("M26")

    @pyqtSlot()
    def pausePrint(self):
        # if self.printers[0].state == "paused":
        # Logger.log("e", "pausePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
            self._sendCommand("M24")
        else:
            self._sendCommand("M25")

    @pyqtSlot()
    def resumePrint(self):
        # Logger.log("e", "resumePrint: %s" % str(self._isPause))
        if self._isPause:
            self._ischanging = True
        self._sendCommand("M24")

    def printer_set_connect(self):
        self._sendCommand("M20")
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connected))
        self.setConnectionText(self._translations.get("connected"))

    def get_current_temp(self, temp):
        return float(temp[0:temp.find("/")])

    def get_target_temp(self, temp):
        return float(temp[temp.find("/") + 1:len(temp)])

    def printer_info_update(self, info):
        printer = self.printers[0]
        t0_temp = info[info.find("T0:") + len("T0:"):info.find("T1:")]
        t1_temp = info[info.find("T1:") + len("T1:"):info.find("@:")]
        bed_temp = info[info.find("B:") + len("B:"):info.find("T0:")]
        printer.updateBedTemperature(self.get_current_temp(bed_temp))
        printer.updateTargetBedTemperature(self.get_target_temp(bed_temp))
        extruder0 = printer.extruders[0]
        extruder0.updateHotendTemperature(self.get_current_temp(t0_temp))
        extruder0.updateTargetHotendTemperature(self.get_target_temp(t0_temp))
        if self._number_of_extruders > 1:
            extruder1 = printer.extruders[1]
            extruder1.updateHotendTemperature(self.get_current_temp(t1_temp))
            extruder1.updateTargetHotendTemperature(self.get_target_temp(t1_temp))

    def printer_get_print_job(self):
        printer = self.printers[0]
        if printer.activePrintJob is None:
            print_job = PrintJobOutputModel(output_controller=self._output_controller)
            printer.updateActivePrintJob(print_job)
        else:
            print_job = printer.activePrintJob
        return print_job

    def printer_update_state(self, info):
        printer = self.printers[0]
        job_state = "offline"
        if "IDLE" in info:
            self._isPrinting = False
            self._isPause = False
            job_state = 'idle'
            printer.acceptsCommands = True
        elif "PRINTING" in info:
            self._isPrinting = True
            self._isPause = False
            job_state = 'printing'
            printer.acceptsCommands = False
        elif "PAUSE" in info:
            self._isPrinting = False
            self._isPause = True
            job_state = 'paused'
            printer.acceptsCommands = False
        print_job = self.printer_get_print_job()
        print_job.updateState(job_state)
        printer.updateState(job_state)
        if self._isPrinting:
            self._ischanging = False

    def printer_update_printing_filename(self, info):
        if self.isBusy() and info.rfind("/") != -1:
            self._printing_filename = info[info.rfind("/") + 1:info.rfind(";")]
        else:
            self._printing_filename = ""
        self.printer_get_print_job().updateName(self._printing_filename)

    def printer_update_printing_time(self, info):
        if self.isBusy():
            tm = info[info.find("M992") + len("M992"):len(info)].replace(" ", "")
            mms = tm.split(":")
            self._printing_time = int(mms[0]) * 3600 + int(mms[1]) * 60 + int(mms[2])
        else:
            self._printing_time = 0 
        self.printer_get_print_job().updateTimeElapsed(self._printing_time)

    def printer_update_totaltime(self, info):
        totaltime = 0
        if self.isBusy():
            self._printing_progress = int(info[info.find("M27") + len("M27"):len(info)].replace(" ", ""))
            totaltime = int(self._printing_time / self._printing_progress * 100)
            Logger.log("i", totaltime)
        else:
            self._printing_progress = 0
            totaltime = self._printing_time
        self.printer_get_print_job().updateTimeTotal(totaltime)

    def printer_file_list_parse(self, info):
        if 'Begin file list' in info:
            self._sdFileList = True
            self.sdFiles = []
            self.last_update_time = time.time()
            return True
        if 'End file list' in info:
            self._sdFileList = False
            return True
        if self._sdFileList:
            filename = info.replace("\n", "").replace("\r", "")
            if filename.lower().endswith("gcode") or filename.lower().endswith("gco") or filename.lower.endswith("g"):
                self.sdFiles.append(filename)
            return True
        return False

    def printer_upload_routine(self):
        if self._progress_message is not None:
            self._progress_message.hide()
            self._progress_message = None
        if self._error_message is not None:
            self._error_message.hide()
            self._error_message = None
        self._error_message = Message(self._translations.get("file_send_failed"))
        self._error_message.show()
        self._update_timer.start()

    def on_read(self):
        if not self._socket:
            self.disconnect()
            return
        try:
            if not self._isConnect:
                self._isConnect = True
            if self._connection_state != UnifiedConnectionState.Connected:
                self.printer_set_connect()
            if not self._printers:
                self._createPrinterList()
            while self._socket.canReadLine():
                s = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
                s = s.replace("\r", "").replace("\n", "")
                Logger.log("d", "mks recv: " + s)
                if "T" in s and "B" in s and "T0" in s:
                    self.printer_info_update(s)
                    continue
                if s.startswith("M997"):
                    self.printer_update_state(s)
                    continue
                if s.startswith("M994"):
                    self.printer_update_printing_filename(s)
                    continue
                if s.startswith("M992"):
                    self.printer_update_printing_time(s)
                    continue
                if s.startswith("M27"):
                    self.printer_update_totaltime(s)
                    continue
                if self.printer_file_list_parse(s):
                    continue
                if s.startswith("Upload"):
                    self.printer_upload_routine()
                    continue
        except Exception as e:
            print(e)

    def _updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature == temperature:
            return False
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()
        return True

    def _createPrinterList(self):
        printer = PrinterOutputModel(
            output_controller=self._output_controller,
            number_of_extruders=self._number_of_extruders)
        printer.updateName(self.name)
        self._printers = [printer]
        self.printersChanged.emit()

    def _onRequestFinished(self, reply):
        http_status_code = reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        self._isSending = True
        self._update_timer.start()
        self._sendCommand("M20")
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference(Constants.AUTO_PRINT, "True")
        if preferences.getValue(Constants.AUTO_PRINT):
            self._printFile()
        if not http_status_code:
            return

    def _onOptionStateChanged(self, optstate):
        preferences = Application.getInstance().getPreferences()
        preferences.setValue(Constants.AUTO_PRINT, str(optstate))

    def _cancelSendGcode(self, message_id, action_id):
        self._update_timer.start()
        self._isSending = False
        self._isPrinting = False
        self._progress_message.hide()
        self._post_reply.abort()

    def CreateMKSController(self):
        Logger.log("d", "Creating additional ui components for mkscontroller.")
        self.__additional_components_view = Application.getInstance(
        ).createQmlComponent(self._monitor_view_qml_path, {"manager": self})
        # trlist = CuraApplication.getInstance()._additional_components
        # for comp in trlist:
        Logger.log("w", "create mkscontroller ")
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")

    def _onGlobalContainerChanged(self) -> None:
        self._global_container_stack = Application.getInstance(
        ).getGlobalContainerStack()
        definitions = self._global_container_stack.definition.findDefinitions(
            key="cooling")
        Logger.log("d", definitions[0].label)

    def _createFlattenedContainerInstance(self, instance_container1,
                                          instance_container2):
        """Create a new container with container 2 as base and container 1 written over it."""

        flat_container = InstanceContainer(instance_container2.getName())

        # The metadata includes id, name and definition
        flat_container.setMetaData(
            copy.deepcopy(instance_container2.getMetaData()))

        if instance_container1.getDefinition():
            flat_container.setDefinition(
                instance_container1.getDefinition().getId())

        for key in instance_container2.getAllKeys():
            flat_container.setProperty(
                key, "value", instance_container2.getProperty(key, "value"))

        for key in instance_container1.getAllKeys():
            flat_container.setProperty(
                key, "value", instance_container1.getProperty(key, "value"))

        return flat_container

    def _serialiseSettings(self, stack):
        """Serialises a container stack to prepare it for writing at the end of the g-code.
        The settings are serialised, and special characters (including newline)
        are escaped.
        :param stack: A container stack to serialise.
        :return: A serialised string of the settings.
        """
        container_registry = self._application.getContainerRegistry()

        # The prefix to put before each line.
        prefix = self._setting_keyword + str(MKSOutputDevice.version) + " "
        prefix_length = len(prefix)

        quality_type = stack.quality.getMetaDataEntry("quality_type")
        container_with_profile = stack.qualityChanges
        machine_definition_id_for_quality = ContainerTree.getInstance(
        ).machines[stack.definition.getId()].quality_definition
        if container_with_profile.getId() == "empty_quality_changes":
            # If the global quality changes is empty, create a new one
            quality_name = container_registry.uniqueName(
                stack.quality.getName())
            quality_id = container_registry.uniqueName(
                (stack.definition.getId() + "_" +
                 quality_name).lower().replace(" ", "_"))
            container_with_profile = InstanceContainer(quality_id)
            container_with_profile.setName(quality_name)
            container_with_profile.setMetaDataEntry("type", "quality_changes")
            container_with_profile.setMetaDataEntry("quality_type",
                                                    quality_type)
            # For extruder stacks, the quality changes should include an intent category.
            if stack.getMetaDataEntry("position") is not None:
                container_with_profile.setMetaDataEntry(
                    "intent_category",
                    stack.intent.getMetaDataEntry("intent_category",
                                                  "default"))
            container_with_profile.setDefinition(
                machine_definition_id_for_quality)
            container_with_profile.setMetaDataEntry(
                "setting_version",
                stack.quality.getMetaDataEntry("setting_version"))

        flat_global_container = self._createFlattenedContainerInstance(
            stack.userChanges, container_with_profile)
        # If the quality changes is not set, we need to set type manually
        if flat_global_container.getMetaDataEntry("type", None) is None:
            flat_global_container.setMetaDataEntry("type", "quality_changes")

        # Ensure that quality_type is set. (Can happen if we have empty quality changes).
        if flat_global_container.getMetaDataEntry("quality_type",
                                                  None) is None:
            flat_global_container.setMetaDataEntry(
                "quality_type",
                stack.quality.getMetaDataEntry("quality_type", "normal"))

        # Get the machine definition ID for quality profiles
        flat_global_container.setMetaDataEntry(
            "definition", machine_definition_id_for_quality)

        serialized = flat_global_container.serialize()
        data = {"global_quality": serialized}

        all_setting_keys = flat_global_container.getAllKeys()
        for extruder in stack.extruderList:
            extruder_quality = extruder.qualityChanges
            if extruder_quality.getId() == "empty_quality_changes":
                # Same story, if quality changes is empty, create a new one
                quality_name = container_registry.uniqueName(
                    stack.quality.getName())
                quality_id = container_registry.uniqueName(
                    (stack.definition.getId() + "_" +
                     quality_name).lower().replace(" ", "_"))
                extruder_quality = InstanceContainer(quality_id)
                extruder_quality.setName(quality_name)
                extruder_quality.setMetaDataEntry("type", "quality_changes")
                extruder_quality.setMetaDataEntry("quality_type", quality_type)
                extruder_quality.setDefinition(
                    machine_definition_id_for_quality)
                extruder_quality.setMetaDataEntry(
                    "setting_version",
                    stack.quality.getMetaDataEntry("setting_version"))

            flat_extruder_quality = self._createFlattenedContainerInstance(
                extruder.userChanges, extruder_quality)
            # If the quality changes is not set, we need to set type manually
            if flat_extruder_quality.getMetaDataEntry("type", None) is None:
                flat_extruder_quality.setMetaDataEntry("type",
                                                       "quality_changes")

            # Ensure that extruder is set. (Can happen if we have empty quality changes).
            if flat_extruder_quality.getMetaDataEntry("position",
                                                      None) is None:
                flat_extruder_quality.setMetaDataEntry(
                    "position", extruder.getMetaDataEntry("position"))

            # Ensure that quality_type is set. (Can happen if we have empty quality changes).
            if flat_extruder_quality.getMetaDataEntry("quality_type",
                                                      None) is None:
                flat_extruder_quality.setMetaDataEntry(
                    "quality_type",
                    extruder.quality.getMetaDataEntry("quality_type",
                                                      "normal"))

            # Change the default definition
            flat_extruder_quality.setMetaDataEntry(
                "definition", machine_definition_id_for_quality)

            extruder_serialized = flat_extruder_quality.serialize()
            data.setdefault("extruder_quality", []).append(extruder_serialized)

            all_setting_keys.update(flat_extruder_quality.getAllKeys())

        # Check if there is any profiles
        if not all_setting_keys:
            Logger.log(
                "i",
                "No custom settings found, not writing settings to g-code.")
            return ""

        json_string = json.dumps(data)

        # Escape characters that have a special meaning in g-code comments.
        pattern = re.compile("|".join(
            MKSOutputDevice.escape_characters.keys()))

        # Perform the replacement with a regular expression.
        escaped_string = pattern.sub(
            lambda m: MKSOutputDevice.escape_characters[re.escape(m.group(0))],
            json_string)

        # Introduce line breaks so that each comment is no longer than 80 characters. Prepend each line with the prefix.
        result = ""

        # Lines have 80 characters, so the payload of each line is 80 - prefix.
        for pos in range(0, len(escaped_string), 80 - prefix_length):
            result += prefix + \
                escaped_string[pos: pos + 80 - prefix_length] + "\n"
        return result
