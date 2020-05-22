from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Signal import signalemitter
from UM.Message import Message
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from cura.CuraApplication import CuraApplication

from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
from UM.PluginRegistry import PluginRegistry
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.SettingDefinitionsModel import SettingDefinitionsModel

from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from cura.PrinterOutput.GenericOutputController import GenericOutputController

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QTcpSocket
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, pyqtProperty, pyqtSlot, QCoreApplication, Qt
from queue import Queue

from . import utils

import json
import os.path
import time
import base64
import sys
from enum import IntEnum

from typing import cast, Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode #For typing.
    from UM.FileHandler.FileHandler import FileHandler #For typing.

i18n_catalog = i18nCatalog("cura")

class UnifiedConnectionState(IntEnum):
    try:
        Closed = ConnectionState.Closed
        Connecting = ConnectionState.Connecting
        Connected = ConnectionState.Connected
        Busy = ConnectionState.Busy
        Error = ConnectionState.Error
    except AttributeError:
        Closed = ConnectionState.closed          # type: ignore
        Connecting = ConnectionState.connecting  # type: ignore
        Connected = ConnectionState.connected    # type: ignore
        Busy = ConnectionState.busy              # type: ignore
        Error = ConnectionState.error            # type: ignore

@signalemitter
class MKSOutputDevice(NetworkedPrinterOutputDevice):
    def __init__(self, instance_id: str, address: str, properties: dict, **kwargs) -> None:
        super().__init__(device_id = instance_id, address = address, properties = properties, **kwargs)
        self._address = address
        self._port = 8080
        self._key = instance_id
        self._properties = properties

        self._target_bed_temperature = 0
        self._num_extruders = 1
        self._hotend_temperatures = [0] * self._num_extruders
        self._target_hotend_temperatures = [0] * self._num_extruders

        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem4x.qml")
        # self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MonitorItem.qml")

        self.setPriority(3)  # Make sure the output device gets selected above local file output and Octoprint XD
        self._active_machine = CuraApplication.getInstance().getMachineManager().activeMachine
        self.setName(instance_id)
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "Печать через TFT"))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "Печать через TFT"))
        self.setIconName("print")
        self.setConnectionText(i18n_catalog.i18nc("@info:status", "Connected to TFT on {0}").format(self._key))
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerChanged)

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
        self._screenShot = None

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

        self._update_timer = QTimer()
        self._update_timer.setInterval(2000)  # TODO; Add preference for update interval
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._onRequestFinished)

        self._preheat_timer = QTimer()
        self._preheat_timer.setSingleShot(True)
        self._preheat_timer.timeout.connect(self.cancelPreheatBed)
        self._exception_message = None
        self._output_controller = GenericOutputController(self)
        self._number_of_extruders = 1
        self._camera_url = ""
        # Application.getInstance().getOutputDeviceManager().outputDevicesChanged.connect(self._onOutputDevicesChanged)
        CuraApplication.getInstance().getCuraSceneController().activeBuildPlateChanged.connect(self.CreateMKSController)

    def _onOutputDevicesChanged(self):
        Logger.log("d", "MKS _onOutputDevicesChanged")

    def connect(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = QTcpSocket()
        self._socket.connectToHost(self._address, self._port)
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        self.setShortDescription(i18n_catalog.i18nc("@action:button", "НАПЕЧАТАТЬ НА " + global_container_stack.getName()))
        self.setDescription(i18n_catalog.i18nc("@properties:tooltip", "НАПЕЧАТАТЬ НА " + global_container_stack.getName()))
        Logger.log("d", "MKS socket connecting ")
        # self._socket.waitForConnected(2000)
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connecting))
        self._setAcceptsCommands(True)
        self._socket.readyRead.connect(self.on_read)
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
    def printer_state(self):
        if len(self._printers) <= 0:
            return "offline"
        return self.printers[0].state

    @pyqtSlot()
    def selectfile(self):
        if self._last_file_name:
            return True
        else:
            return False

    @pyqtSlot(str)
    def deleteSDFiles(self, filename):
        # filename = "几何图.gcode"
        self._sendCommand("M30 1:/" + filename)
        self.sdFiles.remove(filename)
        self._sendCommand("M20")

    @pyqtSlot(str)
    def printSDFiles(self, filename):
        self._sendCommand("M23 "+filename)
        self._sendCommand("M24")

    @pyqtSlot()
    def selectFileToUplload(self):
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("mkswifi/autoprint", "True")
        preferences.addPreference("mkswifi/savepath", "")
        filename,_ = QFileDialog.getOpenFileName(None, "Выберите файл", preferences.getValue("mkswifi/savepath"), "Gcode(*.gcode;*.g;*.goc)")
        preferences.setValue("mkswifi/savepath", filename)
        self._uploadpath = filename
        if ".g" in filename.lower():
            # Logger.log("d", "selectfile:"+filename)
            if filename in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует! Вы хотите переименовать?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Название файла слишком длинное!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Название файла слишком длинное! Переименуйте, пожалуйста:")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "Файл нельзя передавать во время печати!"))
                self._exception_message.show()
                return
            self.uploadfunc(filename)

    def closeMDialog(self):
        if self._mdialog:
            self._mdialog.close()
    
    def renameupload(self, filename):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = filename[:filename.rfind("/")]+"/"+self._mfilename.text()
            if self._mfilename.text() in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует! Вы хотите переименовать?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Название файла слишком длинное!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(lambda : self.renameupload(filename))
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Название файла слишком длинное! Переименуйте, пожалуйста:")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "Файл нельзя передавать во время печати!"))
                self._exception_message.show()
                return
            self._mdialog.close()
            self.uploadfunc(filename)
        
        
    
    def uploadfunc(self, filename):
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("mkswifi/autoprint", "True")
        preferences.addPreference("mkswifi/savepath", "")
        self._update_timer.stop()
        self._isSending = True
        self._preheat_timer.stop()
        single_string_file_data = ""
        try:
            f = open(self._uploadpath, "r")
            single_string_file_data = f.read()
            file_name = filename[filename.rfind("/")+1:]
            self._last_file_name = file_name
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Отправка файла"), 0, False, -1,
                                        i18n_catalog.i18nc("@info:title", "Отправка файла на принтер..."), option_text=i18n_catalog.i18nc("@label", "поставить на печать")
                                        , option_state=preferences.getValue("mkswifi/autoprint"))
            self._progress_message.addAction(i18n_catalog.i18nc("@action:button", "ОТМЕНА"), None, "")
            self._progress_message.actionTriggered.connect(self._cancelSendGcode)
            self._progress_message.optionToggled.connect(self._onOptionStateChanged)
            self._progress_message.show()
            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
            self._post_part = QHttpPart()
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                                      "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._post_part.setBody(single_string_file_data.encode())
            self._post_multi_part.append(self._post_part)
            post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
            post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
            post_request.setRawHeader(b'Connection', b'keep-alive')
            self._post_reply = self._manager.post(post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.sslErrors.connect(self._onUploadError)
            self._gcode = None
        except IOError as e:
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Не удалось передать файл!"))
            self._error_message.show()
            self._update_timer.start()
        except Exception as e:
            self._update_timer.start()
            self._progress_message.hide()
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))
            

    @pyqtProperty("QVariantList")
    def getSDFiles(self):
        self._sendCommand("M20")
        return list(self.sdFiles)


    def _setTargetBedTemperature(self, temperature):
        if not self._updateTargetBedTemperature(temperature):
            return
        self._sendCommand(["M140 S%s" % temperature])

    @pyqtSlot(str)
    def sendCommand(self, cmd):
        self._sendCommand(cmd)

    def _sendCommand(self, cmd):
        # Logger.log("d", "_sendCommand %s" % str(cmd))
        if self._socket and self._socket.state() == 2 or self._socket.state() == 3:
            if isinstance(cmd, str):
                self._command_queue.put(cmd + "\r\n")
            elif isinstance(cmd, list):
                for eachCommand in cmd:
                    self._command_queue.put(eachCommand + "\r\n")

    def disconnect(self):
        # self._updateJobState("")
        self._isConnect = False
        self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Closed))
        if self._socket is not None:
            self._socket.readyRead.disconnect(self.on_read)
            self._socket.close()
        if self._progress_message:
            self._progress_message.hide()
        if self._error_message:
            self._error_message.hide()
        self._update_timer.stop()

    def isConnected(self):
        return self._isConnect

    def isBusy(self):
        return self._isPrinting or self._isPause

    def requestWrite(self, node, file_name=None, filter_by_machine=False, file_handler=None, **kwargs):
        self.writeStarted.emit(self)
        self._update_timer.stop()
        self._isSending = True
        # imagebuff = self._gl.glReadPixels(0, 0, 800, 800, self._gl.GL_RGB,
        #                                   self._gl.GL_UNSIGNED_BYTE)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = CuraApplication.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", None)
        if not gcode_dict:
            return
        self._gcode = gcode_dict.get(active_build_plate, None)
        # Logger.log("d", "mks ready for print")
        self.startPrint()

    def startPrint(self):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return
        if self._error_message:
            self._error_message.hide()
            self._error_message = None

        if self._progress_message:
            self._progress_message.hide()
            self._progress_message = None

        if self.isBusy():
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Отправка файла"), 0, False, -1,
                                         i18n_catalog.i18nc("@info:title", "Отправка файла на принтер..."))
            self._error_message.show()
            return
        job_name = Application.getInstance().getPrintInformation().jobName.strip()
        if job_name is "":
            job_name = "untitled_print"
            job_name = "cura_file"
        filename = "%s.gcode" % job_name
        if filename in self.sdFiles:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует!")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            nobtn = QPushButton("Отмена")
            yesbtn = QPushButton("Ок")
            yesbtn.clicked.connect(self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует! Вы хотите переименовать?")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(nobtn)
            dialoghbox.addWidget(yesbtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        if len(filename[filename.rfind("/")+1:]) >= 30:
            if self._mdialog:
                self._mdialog.close()
            self._mdialog = QDialog()
            self._mdialog.setWindowTitle("Название файла слишком длинное!")
            dialogvbox = QVBoxLayout()
            dialoghbox = QHBoxLayout()
            nobtn = QPushButton("Отмена")
            yesbtn = QPushButton("Ок")
            yesbtn.clicked.connect(self.recheckfilename)
            nobtn.clicked.connect(self.closeMDialog)
            content = QLabel("Название файла слишком длинное! Переименуйте, пожалуйста:")
            self._mfilename = QLineEdit()
            self._mfilename.setText(filename[filename.rfind("/")+1:])
            dialoghbox.addWidget(nobtn)
            dialoghbox.addWidget(yesbtn)
            dialogvbox.addWidget(content)
            dialogvbox.addWidget(self._mfilename)
            dialogvbox.addLayout(dialoghbox)
            self._mdialog.setLayout(dialogvbox)
            self._mdialog.exec_()
            return
        self._startPrint(filename)

    def recheckfilename(self):
        if self._mfilename and ".g" in self._mfilename.text().lower():
            filename = self._mfilename.text()
            if filename in self.sdFiles:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Файл с именем "+filename[filename.rfind("/")+1:]+" уже существует! Вы хотите переименовать?")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if len(filename[filename.rfind("/")+1:]) >= 30:
                if self._mdialog:
                    self._mdialog.close()
                self._mdialog = QDialog()
                self._mdialog.setWindowTitle("Название файла слишком длинное!")
                dialogvbox = QVBoxLayout()
                dialoghbox = QHBoxLayout()
                nobtn = QPushButton("Отмена")
                yesbtn = QPushButton("Ок")
                yesbtn.clicked.connect(self.recheckfilename)
                nobtn.clicked.connect(self.closeMDialog)
                content = QLabel("Название файла слишком длинное! Переименуйте, пожалуйста:")
                self._mfilename = QLineEdit()
                self._mfilename.setText(filename[filename.rfind("/")+1:])
                dialoghbox.addWidget(nobtn)
                dialoghbox.addWidget(yesbtn)
                dialogvbox.addWidget(content)
                dialogvbox.addWidget(self._mfilename)
                dialogvbox.addLayout(dialoghbox)
                self._mdialog.setLayout(dialogvbox)
                self._mdialog.exec_()
                return
            if self.isBusy():
                if self._exception_message:
                    self._exception_message.hide()
                self._exception_message = Message(i18n_catalog.i18nc("@info:status", "Файл нельзя передавать во время печати!"))
                self._exception_message.show()
                return
            self._mdialog.close()
            self._startPrint(filename)

    def _messageBoxCallback(self, button):
        def delayedCallback():
            if button == QMessageBox.Yes:
                self.startPrint()
            else:
                CuraApplication.getInstance().getController().setActiveStage("Подготовка")

    def _startPrint(self, file_name="cura_file.gcode"):
        self._preheat_timer.stop()
        self._screenShot = utils.take_screenshot()
        try:
            preferences = Application.getInstance().getPreferences()
            preferences.addPreference("mkswifi/autoprint", "True")
            preferences.addPreference("mkswifi/savepath", "")
            # CuraApplication.getInstance().showPrintMonitor.emit(True)
            self._progress_message = Message(i18n_catalog.i18nc("@info:status", "Отправка файла"), 0, False, -1,
                                         i18n_catalog.i18nc("@info:title", "Отправка файла на принтер..."), option_text=i18n_catalog.i18nc("@label", "поставить на печать")
                                         , option_state=preferences.getValue("mkswifi/autoprint"))
            self._progress_message.addAction("Cancel", i18n_catalog.i18nc("@action:button", "ОТМЕНА"), None, "")
            self._progress_message.actionTriggered.connect(self._cancelSendGcode)
            self._progress_message.optionToggled.connect(self._onOptionStateChanged)
            self._progress_message.show()
            # job_name = Application.getInstance().getPrintInformation().jobName.strip()
            # if job_name is "":
            #     job_name = "untitled_print"
                # job_name = "cura_file"
            # file_name = "%s.gcode" % job_name
            self._last_file_name = file_name
            Logger.log("d", "mks: "+file_name + Application.getInstance().getPrintInformation().jobName.strip())

            single_string_file_data = ""
            if self._screenShot:
                single_string_file_data += utils.add_screenshot(self._screenShot, 50, 50, ";simage:")
                single_string_file_data += utils.add_screenshot(self._screenShot, 200, 200, ";;gimage:")
                single_string_file_data += "\r"
            last_process_events = time.time()
            for line in self._gcode:
                single_string_file_data += line
                if time.time() > last_process_events + 0.05:
                    QCoreApplication.processEvents()
                    last_process_events = time.time()

            self._post_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
            self._post_part = QHttpPart()
            # self._post_part.setHeader(QNetworkRequest.ContentTypeHeader, b'application/octet-stream')
            self._post_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                                      "form-data; name=\"file\"; filename=\"%s\"" % file_name)
            self._post_part.setBody(single_string_file_data.encode())
            self._post_multi_part.append(self._post_part)
            post_request = QNetworkRequest(QUrl("http://%s/upload?X-Filename=%s" % (self._address, file_name)))
            post_request.setRawHeader(b'Content-Type', b'application/octet-stream')
            post_request.setRawHeader(b'Connection', b'keep-alive')
            self._post_reply = self._manager.post(post_request, self._post_multi_part)
            self._post_reply.uploadProgress.connect(self._onUploadProgress)
            self._post_reply.sslErrors.connect(self._onUploadError)
            # Logger.log("d", "http://%s:80/upload?X-Filename=%s" % (self._address, file_name))
            self._gcode = None
        except IOError as e:
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))
            self._progress_message.hide()
            self._error_message = Message(i18n_catalog.i18nc("@info:status", "Отправка файла на принтер не произошла!"))
            self._error_message.show()
            self._update_timer.start()
        except Exception as e:
            self._update_timer.start()
            self._progress_message.hide()
            Logger.log("e", "An exception occurred in network connection: %s" % str(e))

    def _printFile(self):
        self._sendCommand("M23 " + self._last_file_name)
        self._sendCommand("M24")

    def _onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_total > 0:
            new_progress = bytes_sent / bytes_total * 100
            # Treat upload progress as response. Uploading can take more than 10 seconds, so if we don't, we can get
            # timeout responses if this happens.
            self._last_response_time = time.time()
            if new_progress > self._progress_message.getProgress():
                self._progress_message.show()  # Ensure that the message is visible.
                self._progress_message.setProgress(bytes_sent / bytes_total * 100)
        else:
            self._progress_message.setProgress(0)
            self._progress_message.hide()

    def _onUploadError(self, reply, sslerror):
        Logger.log("d", "Upload Error")

    def _setHeadPosition(self, x, y, z, speed):
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))

    def _setHeadX(self, x, speed):
        self._sendCommand("G0 X%s F%s" % (x, speed))

    def _setHeadY(self, y, speed):
        self._sendCommand("G0 Y%s F%s" % (y, speed))

    def _setHeadZ(self, z, speed):
        self._sendCommand("G0 Z%s F%s" % (z, speed))

    def _homeHead(self):
        self._sendCommand("G28 X Y")

    def _homeBed(self):
        self._sendCommand("G28 Z")

    def _moveHead(self, x, y, z, speed):
        self._sendCommand(["G91", "G0 X%s Y%s Z%s F%s" % (x, y, z, speed), "G90"])

    def _update(self):
        if self._socket is not None and (self._socket.state() == 2 or self._socket.state() == 3):
            _send_data = "M105\r\nM997\r\n"
            if self.isBusy():
                _send_data += "M994\r\nM992\r\nM27\r\n"
            while self._command_queue.qsize() > 0:
                _queue_data = self._command_queue.get()
                if "M23" in _queue_data:
                    self._socket.writeData(_queue_data.encode())
                    continue
                if "M24" in _queue_data:
                    self._socket.writeData(_queue_data.encode())
                    continue
                _send_data += _queue_data
            # Logger.log("d", "_send_data: \r\n%s" % _send_data)
            self._socket.writeData(_send_data.encode())
            self._socket.flush()
            # self._socket.waitForReadyRead()
        else:
            Logger.log("d", "MKS wifi reconnecting")
            self.disconnect()
            self.connect()

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
        self._sendCommand("M26")

    @pyqtSlot()
    def pausePrint(self):
        if self.printers[0].state == "pause":
            self._sendCommand("M24")
        else:
            self._sendCommand("M25")
        

    @pyqtSlot()
    def resumePrint(self):
        self._sendCommand("M25")

    def on_read(self):
        if not self._socket:
            self.disconnect()
            return
        try:
            if not self._isConnect:
                self._isConnect = True
            if self._connection_state != UnifiedConnectionState.Connected:
                self._sendCommand("M20")
                self.setConnectionState(cast(ConnectionState, UnifiedConnectionState.Connected))
                self.setConnectionText(i18n_catalog.i18nc("@info:status", "Подключение по TFT произошло успешно!"))
            # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # while self._socket.canReadLine():
                # ss = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
            # ss_list = ss.split("\r\n")
            if not self._printers:
                self._createPrinterList()
            printer = self.printers[0]
            while self._socket.canReadLine():
                s = str(self._socket.readLine().data(), encoding=sys.getfilesystemencoding())
                # Logger.log("d", "mks recv: "+s)
                s = s.replace("\r", "").replace("\n", "")
                # if time.time() - self.last_update_time > 10 or time.time() - self.last_update_time<-10:
                #     Logger.log("d", "mks time:"+str(self.last_update_time)+str(time.time()))
                #     self._sendCommand("M20")
                #     self.last_update_time = time.time() 
                if "T" in s and "B" in s and "T0" in s:
                    t0_temp = s[s.find("T0:") + len("T0:"):s.find("T1:")]
                    t1_temp = s[s.find("T1:") + len("T1:"):s.find("@:")]
                    bed_temp = s[s.find("B:") + len("B:"):s.find("T0:")]
                    t0_nowtemp = float(t0_temp[0:t0_temp.find("/")])
                    t0_targettemp = float(t0_temp[t0_temp.find("/") + 1:len(t0_temp)])
                    t1_nowtemp = float(t1_temp[0:t1_temp.find("/")])
                    t1_targettemp = float(t1_temp[t1_temp.find("/") + 1:len(t1_temp)])
                    bed_nowtemp = float(bed_temp[0:bed_temp.find("/")])
                    bed_targettemp = float(bed_temp[bed_temp.find("/") + 1:len(bed_temp)])
                    # cura 3.4 new api
                    printer.updateBedTemperature(bed_nowtemp)
                    printer.updateTargetBedTemperature(bed_targettemp)
                    extruder = printer.extruders[0]
                    extruder.updateTargetHotendTemperature(t0_targettemp)
                    extruder.updateHotendTemperature(t0_nowtemp)
                    # self._number_of_extruders = 1
                    # extruder = printer.extruders[1]
                    # extruder.updateHotendTemperature(t1_nowtemp)
                    # extruder.updateTargetHotendTemperature(t1_targettemp)
                    # only on lower 3.4
                    # self._setBedTemperature(bed_nowtemp)
                    # self._updateTargetBedTemperature(bed_targettemp)
                    # if self._num_extruders > 1:
                    # self._setHotendTemperature(1, t1_nowtemp)
                    # self._updateTargetHotendTemperature(1, t1_targettemp)
                    # self._setHotendTemperature(0, t0_nowtemp)
                    # self._updateTargetHotendTemperature(0, t0_targettemp)
                    continue
                if printer.activePrintJob is None:
                    print_job = PrintJobOutputModel(output_controller=self._output_controller)
                    printer.updateActivePrintJob(print_job)
                else:
                    print_job = printer.activePrintJob
                if s.startswith("M997"):
                    job_state = "offline"
                    if "IDLE" in s:
                        self._isPrinting = False
                        self._isPause = False
                        job_state = 'idle'
                    elif "PRINTING" in s:
                        self._isPrinting = True
                        self._isPause = False
                        job_state = 'printing'
                    elif "PAUSE" in s:
                        self._isPrinting = False
                        self._isPause = True
                        job_state = 'paused'
                    print_job.updateState(job_state)
                    printer.updateState(job_state)
                    # self._updateJobState(job_state)
                    continue
                # print_job.updateState('idle')
                # printer.updateState('idle')
                if s.startswith("M994"):
                    if self.isBusy() and s.rfind("/") != -1:
                        self._printing_filename = s[s.rfind("/") + 1:s.rfind(";")]
                    else:
                        self._printing_filename = ""
                    print_job.updateName(self._printing_filename)
                    # self.setJobName(self._printing_filename)
                    continue
                if s.startswith("M992"):
                    if self.isBusy():
                        tm = s[s.find("M992") + len("M992"):len(s)].replace(" ", "")
                        mms = tm.split(":")
                        self._printing_time = int(mms[0]) * 3600 + int(mms[1]) * 60 + int(mms[2])
                    else:
                        self._printing_time = 0
                    # Logger.log("d", self._printing_time)
                    print_job.updateTimeElapsed(self._printing_time)
                    # self.setTimeElapsed(self._printing_time)
                    # print_job.updateTimeTotal(self._printing_time)
                    # self.setTimeTotal(self._printing_time)
                    continue
                if s.startswith("M27"):
                    if self.isBusy():
                        self._printing_progress = float(s[s.find("M27") + len("M27"):len(s)].replace(" ", ""))
                        totaltime = self._printing_time/self._printing_progress*100
                    else:
                        self._printing_progress = 0
                        totaltime = self._printing_time * 100
                    # Logger.log("d", self._printing_time)
                    # Logger.log("d", totaltime)
                    # self.setProgress(self._printing_progress)
                    print_job.updateTimeTotal(self._printing_time)
                    print_job.updateTimeElapsed(self._printing_time*2-totaltime)
                    continue
                if 'Begin file list' in s:
                    self._sdFileList = True
                    self.sdFiles = []
                    self.last_update_time = time.time()
                    continue
                if 'End file list' in s:
                    self._sdFileList = False
                    continue
                if self._sdFileList :
                    s = s.replace("\n", "").replace("\r", "")
                    if s.lower().endswith("gcode") or s.lower().endswith("gco") or s.lower.endswith("g"):
                        self.sdFiles.append(s)
                    continue
        except Exception as e:
            print(e)

    def _updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature == temperature:
            return False
        self._target_bed_temperature = temperature
        self.targetBedTemperatureChanged.emit()
        return True

    def _updateTargetHotendTemperature(self, index, temperature):
        if self._target_hotend_temperatures[index] == temperature:
            return False
        self._target_hotend_temperatures[index] = temperature
        self.targetHotendTemperaturesChanged.emit()
        return True

    def _createPrinterList(self):
        printer = PrinterOutputModel(output_controller=self._output_controller, number_of_extruders=self._number_of_extruders)
        printer.updateName(self.name)
        self._printers = [printer]
        self.printersChanged.emit()

    def _onRequestFinished(self, reply):
        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        self._isSending = True
        self._update_timer.start()
        self._sendCommand("M20")
        preferences = Application.getInstance().getPreferences()
        preferences.addPreference("mkswifi/autoprint", "True")
        # preferences.addPreference("mkswifi/savepath", "")
        # preferences.setValue("mkswifi/autoprint", str(self._progress_message.getOptionState()))
        if preferences.getValue("mkswifi/autoprint"):
            self._printFile()
        if not http_status_code:
            return

    def _onOptionStateChanged(self, optstate):
        preferences = Application.getInstance().getPreferences()
        preferences.setValue("mkswifi/autoprint", str(optstate))

    def _cancelSendGcode(self, message_id, action_id):
        self._update_timer.start()
        self._isSending = False
        self._progress_message.hide()
        self._post_reply.abort()
    
    def CreateMKSController(self):
        Logger.log("d", "Creating additional ui components for mkscontroller.")
        # self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(self._monitor_view_qml_path, {"mkscontroller": self})
        self.__additional_components_view = Application.getInstance().createQmlComponent(self._monitor_view_qml_path, {"manager": self})
        # trlist = CuraApplication.getInstance()._additional_components
        # for comp in trlist:
        Logger.log("w", "create mkscontroller ")
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for tft35.")
            return

    def _onGlobalContainerChanged(self) -> None:
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        definitions = self._global_container_stack.definition.findDefinitions(key="cooling")
        Logger.log("d", definitions[0].label)
