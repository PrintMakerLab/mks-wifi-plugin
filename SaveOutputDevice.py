# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from . import utils
import os
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from UM.Application import Application
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter
from UM.Message import Message
from UM.OutputDevice import OutputDeviceError
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.i18n import i18nCatalog

catalog = i18nCatalog("mksplugin")


class SaveOutputDevice(OutputDevice):
    def __init__(self):
        super().__init__("save_with_screenshot")
        self.init_translations()
        self.setName("save_with_screenshot")
        self.setPriority(2)
        self._preferences = Application.getInstance().getPreferences()
        self.setShortDescription(self._translations.get("save_tft_button"))
        self.setDescription(self._translations.get("save_tft_tooltip"))
        self.setIconName("save")
        self._writing = False

    _translations = {}

    def init_translations(self):
        self._translations = {
            "save_tft_button": catalog.i18nc("@action:button", "Save as TFT file"),
            "save_tft_tooltip": catalog.i18nc("@properties:tooltip", "Save as TFT file"),
            "save_file_window": catalog.i18nc("@title:window", "Save to File"),
            "no_file_warning": catalog.i18nc("@info:warning", "There are no file types available to write with!"),
            "file_exists_window": catalog.i18nc("@title:window Don't translate the XML tag <filename>!", "<filename>{0}</filename> already exists."),
            "file_overwrite_label": catalog.i18nc("@label Don't translate the XML tag <filename>!", "<filename>{0}</filename> already exists. Are you sure you want to overwrite it?"),
            "file_saving_progress": catalog.i18nc("@info:progress Don't translate the XML tags <filename>!", "Saving to <filename>{0}</filename>"),
            "file_saving_title": catalog.i18nc("@info:title", "Saving"),
            "permission_denied": catalog.i18nc("@info:status Don't translate the XML tags <filename>!", "Permission denied when trying to save <filename>{0}</filename>"),
            "permission_denied2 ": catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not save to <filename>{0}</filename>: <message>{1}</message>"),
            "file_saved_status": catalog.i18nc("@info:status Don't translate the XML tags <filename>!", "Saved to <filename>{0}</filename>"),
            "file_saved_title": catalog.i18nc("@info:title", "File saved"),
            "open_folder_button": catalog.i18nc("@action:button", "Open folder"),
            "open_folder_tooltip": catalog.i18nc("@properties:tooltip", "Open the folder containing the file"),
            "file_cant_save": catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not save to <filename>{0}</filename>: <message>{1}</message>"),
            "warning": catalog.i18nc("@info:title", "Warning"),
            "error": catalog.i18nc("@info:title", "Error"),
            "file_something_wrong": catalog.i18nc("@info:status", "Something went wrong saving to <filename>{0}</filename>: <message>{1}</message>"),
        }

    def prepare_write_dialog(self):
        dialog = QFileDialog()

        dialog.setWindowTitle(self._translations.get("save_file_window"))
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        # Ensure platform never ask for overwrite confirmation since we do this ourselves
        dialog.setOption(QFileDialog.DontConfirmOverwrite)

        if sys.platform == "linux" and "KDE_FULL_SESSION" in os.environ:
            dialog.setOption(QFileDialog.DontUseNativeDialog)

        return dialog
    
    def get_file_types(self, file_handler, limit_mimetypes):
        file_types = file_handler.getSupportedFileTypesWrite()

        file_types.sort(key=lambda k: k["description"])
        if limit_mimetypes:
            file_types = list(
                filter(lambda i: i["mime_type"] in limit_mimetypes, file_types))

        file_types = [ft for ft in file_types if not ft["hide_in_file_dialog"]]

        return file_types

    def get_file_writer(self, file_handler, selected_type):
        if file_handler:
            file_writer = file_handler.getWriter(selected_type["id"])
        else:
            file_writer = Application.getInstance(
            ).getMeshFileHandler().getWriter(selected_type["id"])

        return file_writer

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=None, file_handler=None, **kwargs):
        if self._writing:
            raise OutputDeviceError.DeviceBusyError()

        # Set up and display file dialog
        dialog = self.prepare_write_dialog()

        filters = []
        mime_types = []
        selected_filter = None

        if "preferred_mimetypes" in kwargs and kwargs["preferred_mimetypes"] is not None:
            preferred_mimetypes = kwargs["preferred_mimetypes"]
        else:
            preferred_mimetypes = Application.getInstance(
            ).getPreferences().getValue("local_file/last_used_type")
        preferred_mimetype_list = preferred_mimetypes.split(";")

        if not file_handler:
            file_handler = Application.getInstance().getMeshFileHandler()

        file_types = self.get_file_types(file_handler, limit_mimetypes)

        if len(file_types) == 0:
            Logger.log("e", "There are no file types available to write with!")
            raise OutputDeviceError.WriteRequestFailedError(
                self._translations.get("no_file_warning"))

        # Find the first available preferred mime type
        preferred_mimetype = None
        for mime_type in preferred_mimetype_list:
            if any(ft["mime_type"] == mime_type for ft in file_types):
                preferred_mimetype = mime_type
                break

        for item in file_types:
            type_filter = "{0} (*.{1})".format(
                item["description"], item["extension"])
            filters.append(type_filter)
            mime_types.append(item["mime_type"])
            if preferred_mimetype == item["mime_type"]:
                selected_filter = type_filter
                if file_name:
                    file_name += "." + item["extension"]

        # CURA-6411: This code needs to be before dialog.selectFile and the filters, because otherwise in macOS (for some reason) the setDirectory call doesn't work.
        stored_directory = Application.getInstance().getPreferences().getValue(
            "local_file/dialog_save_path")
        dialog.setDirectory(stored_directory)

        # Add the file name before adding the extension to the dialog
        if file_name is not None:
            dialog.selectFile(file_name)

        dialog.setNameFilters(filters)
        if selected_filter is not None:
            dialog.selectNameFilter(selected_filter)

        if not dialog.exec_():
            raise OutputDeviceError.UserCanceledError()

        save_path = dialog.directory().absolutePath()
        Application.getInstance().getPreferences().setValue(
            "local_file/dialog_save_path", save_path)

        selected_type = file_types[filters.index(dialog.selectedNameFilter())]
        Application.getInstance().getPreferences().setValue(
            "local_file/last_used_type", selected_type["mime_type"])

        # Get file name from file dialog
        file_name = dialog.selectedFiles()[0]
        Logger.log("d", "Writing to [%s]..." % file_name)

        if os.path.exists(file_name):
            result = QMessageBox.question(None, self._translations.get("file_exists_window").format(file_name[file_name.rfind(
                "/")+1:]), self._translations.get("file_overwrite_label").format(file_name[file_name.rfind("/")+1:]))
            if result == QMessageBox.No:
                raise OutputDeviceError.UserCanceledError()

        self.writeStarted.emit(self)

        # Actually writing file
        file_writer = self.get_file_writer(file_handler, selected_type)

        try:
            mode = selected_type["mode"]
            if mode == MeshWriter.OutputMode.TextMode:
                Logger.log(
                    "d", "Writing to Local File %s in text mode", file_name)
                stream = open(file_name, "wt", encoding="utf-8")
            elif mode == MeshWriter.OutputMode.BinaryMode:
                Logger.log(
                    "d", "Writing to Local File %s in binary mode", file_name)
                stream = open(file_name, "wb")
            else:
                Logger.log("e", "Unrecognised OutputMode.")
                return None

            # Adding screeshot section
            if file_name.endswith(".gcode"):
                Logger.log("d", "Generating preview image")
                screenshot_string = utils.add_screenshot()

                if screenshot_string != "":
                    if mode == MeshWriter.OutputMode.TextMode:
                        Logger.log("d", "Writing preview image in text mode")
                        stream.write(screenshot_string)
                    elif mode == MeshWriter.OutputMode.BinaryMode:
                        Logger.log("d", "Writing preview image in binary mode not supported")
                    else:
                        Logger.log("e", "Unrecognised OutputMode.")
                        return None
            else:
                Logger.log("w", "Saving none .gcode files with preview is not supported!") 
            # End of screeshot section

            Logger.log("d", "Prepaire to save the file")
            job = WriteFileJob(file_writer, stream, nodes, mode)
            job.setFileName(file_name)
            # The file will be added into the "recent files" list upon success
            job.setAddToRecentFiles(True)
            job.progress.connect(self._onJobProgress)
            job.finished.connect(self._onWriteJobFinished)

            message = Message(self._translations.get("file_saving_progress").format(file_name),
                              0, False, -1, self._translations.get("file_saving_title"))
            message.show()

            job.setMessage(message)
            self._writing = True
            job.start()
        except PermissionError as e:
            Logger.log(
                "e", "Permission denied when trying to write to %s: %s", file_name, str(e))
            raise OutputDeviceError.PermissionDeniedError(
                self._translations.get("permission_denied").format(file_name)) from e
        except OSError as e:
            Logger.log(
                "e", "Operating system would not let us write to %s: %s", file_name, str(e))
            raise OutputDeviceError.WriteRequestFailedError(
                self._translations.get("permission_denied2").format(file_name, str(e))) from e

    def _onJobProgress(self, job, progress):
        self.writeProgress.emit(self, progress)

    def _onWriteJobFinished(self, job):
        self._writing = False
        self.writeFinished.emit(self)
        if job.getResult():
            self.writeSuccess.emit(self)
            message = Message(self._translations.get("file_saved_status").format(
                job.getFileName()), title=self._translations.get("file_saved_title"))
            message.addAction(
                "open_folder", self._translations.get("open_folder_button"), "open-folder", self._translations.get("open_folder_tooltip"))
            message._folder = os.path.dirname(job.getFileName())
            message.actionTriggered.connect(self._onMessageActionTriggered)
            message.show()
            Logger.log("d", "File saved")
        else:
            message = Message(self._translations.get("file_cant_save").format(job.getFileName(
            ), str(job.getError())), lifetime=0, title=self._translations.get("warning"))
            message.show()
            self.writeError.emit(self)
            Logger.log("d", "Can't save file: " + str(job.getError()))
        try:
            job.getStream().close()
        # When you don't have the rights to do the final flush or the disk is full.
        except (OSError, PermissionError):
            message = Message(self._translations.get("file_something_wrong").format(
                job.getFileName(), str(job.getError())), title=self._translations.get("error"))
            message.show()
            self.writeError.emit(self)

    def _onMessageActionTriggered(self, message, action):
        if action == "open_folder" and hasattr(message, "_folder"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(message._folder))
