# Copyright (c) 2022
# MKS Plugin is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger

def generate_new_filename(existing_files, current_filename, max_len):
    Logger.log("d", "Starting generating new file name. Current name: %s, max len: %d, existing files on SD card: %s." % (current_filename, max_len, ", ".join(existing_files)))

    filename, file_extension = split_extension(current_filename)

    i = 1
    new_filename = truncate(filename, max_len - len(file_extension)) + file_extension
    while new_filename in existing_files:
        suffics = str(i) + file_extension
        new_filename = truncate(filename, max_len - len(suffics)) + suffics
        i += 1

    Logger.log("d", "Successfully generated new file name: %s." % new_filename)
    return new_filename

def split_extension(filename):
    last_dot_index = filename.rfind(".")
    if last_dot_index >= 0:
        name = filename[:last_dot_index]
        extension = filename[last_dot_index:]
    else:
        name = filename
        extension = ""
        
    return name, extension

def truncate(str, max_len):
    if len(str) > max_len:
        number_of_last_chars_to_remove = len(str) - max_len
        cut_str = str[:-number_of_last_chars_to_remove]
        return cut_str
    else:
        return str
