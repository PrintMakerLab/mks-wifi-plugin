# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Logger import Logger

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

catalog = i18nCatalog("mksplugin")

class MKSDialog(QDialog):
    def __init__(self, parent = None):
        super(MKSDialog, self).__init__(parent)

        self.init_translations()

        self.yes_cliked = False

        self.line_edit = QLineEdit()
        self.content = QLabel("")

        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        yesbtn = QPushButton(self._translations.get("button_yes"))
        yesbtn.clicked.connect(self.yes_click)
        nobtn = QPushButton(self._translations.get("button_no"))
        nobtn.clicked.connect(self.no_click)
        hlayout.addWidget(yesbtn)
        hlayout.addWidget(nobtn)

        vlayout.addWidget(self.content)
        vlayout.addWidget(self.line_edit)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    _translations = {}

    def init_translations(self):
        self._translations = {
            "button_yes": catalog.i18nc("@action:button", "Yes"),
            "button_no": catalog.i18nc("@action:button", "No"),
        }

    def init_dialog(self, filename, label, title):
        self.line_edit.setText(filename)
        self.content.setText(label)
        self.setWindowTitle(title)        

    def get_filename(self):
        return self.line_edit.text()

    def yes_click(self):
        self.yes_cliked = True
        self.accept()

    def no_click(self):
        self.yes_cliked = False
        self.line_edit.setText("")
        self.reject()

    def accepted(self):
        return self.yes_cliked