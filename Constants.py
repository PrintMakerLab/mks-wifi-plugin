# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.

# Cura
C_ACTION_BUTTON = "@action:button"
C_INFO_STATUS = "@info:status"
C_TOOLTIP = "@properties:tooltip"
C_TITLE = "@info:title"
C_LABEL = "@label"
C_WARNING_STATUS = "@warning:status"
C_PROGRESS = "@info:progress"

STOP_UPDATE = "mkswifi/stopupdate"
AUTO_PRINT = "mkswifi/autoprint"
SAVE_PATH = "mkswifi/savepath"
MANUAL_INSTANCES = "mkswifi/manual_instances"

# Don't translate the XML
DNT_MESSAGE = "Don't translate the XML tags <message>!"
DNT_FILENAME = "Don't translate the XML tags <filename>!"
DNT_BOTH = "Don't translate the XML tags <filename> or <message>!"

# DNT combined messages
C_ACTION_BUTTON_DNT1 = C_ACTION_BUTTON+" "+DNT_MESSAGE
C_INFO_STATUS_DNT1 = C_INFO_STATUS+" "+DNT_MESSAGE
C_TOOLTIP_DNT1 = C_TOOLTIP+" "+DNT_MESSAGE

# Errors
ERROR_MESSAGE1 = "Error: command can not send"
ERROR_MESSAGE2 = "Error: Another file is uploading, please try later."
EXCEPTION_MESSAGE = "An exception occurred in network connection: %s"

# Exists
EXISTS1 = "<message>{0}</message> already exists."
EXISTS2 = "<message>{0}</message> already exists, please rename it."

# File
F_TOO_LONG1= "File name is too long to upload."
F_TOO_LONG2 = "File name is too long to upload, please rename it."
F_INCLUDE1 = "File name can not include chinese."
F_INCLUDE2 = "File name can not include chinese, please rename it."
F_TRANSLATE = "File cannot be transferred during printing."
F_SEND_FAILED = "Send file to printer failed."
