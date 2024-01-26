# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from array import array
from UM.Application import Application
from cura.Snapshot import Snapshot
from PyQt6 import QtCore
from UM.Logger import Logger


from . import Constants
from .encoders import ColPicEncoder

def add_leading_zeros(rgb):
    str_hex = "%x" % rgb
    str_hex_len = len(str_hex)
    if str_hex_len == 3:
        str_hex = '0' + str_hex[0:3]
    elif str_hex_len == 2:
        str_hex = '00' + str_hex[0:2]
    elif str_hex_len == 1:
        str_hex = '000' + str_hex[0:1]
    return str_hex

def convert_to_rgb(image, height_pixel, width_pixel):
    pixel_color = image.pixelColor(width_pixel, height_pixel)
    r = pixel_color.red() >> 3
    g = pixel_color.green() >> 2
    b = pixel_color.blue() >> 3
    rgb = (r << 11) | (g << 5) | b
    return rgb


def default_encode(scaled_image, img_type, img_size):
    result = img_type
    datasize = 0
    for i in range(img_size.height()):
        for j in range(img_size.width()):
            rgb = convert_to_rgb(scaled_image, i, j)
            str_hex = add_leading_zeros(rgb)
            if str_hex[2:4] != '':
                result += str_hex[2:4]
                datasize += 2
            if str_hex[0:2] != '':
                result += str_hex[0:2]
                datasize += 2
            if datasize >= 50:
                datasize = 0
        result += '\rM10086 ;'
        if i == img_size.height() - 1:
            result += "\r"
    return result

def custom_encode(scaled_image, img_type, img_size):
    result = ""
    color16 = array('H')
    for i in range(img_size.height()):
        for j in range(img_size.width()):    
            rgb = convert_to_rgb(scaled_image, i, j)
            color16.append(rgb)
    max_size = img_size.height()*img_size.width()*10
    output_data = bytearray(max_size)
    resultInt = ColPicEncoder.ColPic_EncodeStr(
        color16, 
        img_size.height(), 
        img_size.width(), 
        output_data, 
        max_size, 
        1024
    )
    # legacy code, don't try to understand
    # in short - add img_type and new lines where its needed
    data_without_zeros = str(output_data).replace('\\x00', '')
    data = data_without_zeros[2:len(data_without_zeros) - 2]
    each_line_max = 1024 - 8 - 1
    max_lines = int(len(data)/each_line_max)
    length_to_append = each_line_max - 3 - int(len(data)%each_line_max)+10
    j = 0
    for i in range(len(output_data)):
        if (output_data[i] != 0):
            if j == max_lines*each_line_max:
                result += '\r;' + img_type + chr(output_data[i])
            elif j == 0:
                result += img_type + chr(output_data[i])
            elif j%each_line_max == 0:
                result += '\r' + img_type + chr(output_data[i])
            else:
                result += chr(output_data[i])
            j += 1
    result += '\r;'
    # add zeros to the end
    for m in range(length_to_append):
        result += '0'
    return result


def add_screenshot_str(img, width, height, img_type, encoded):
    result = ""
    scaled_image = img.scaled(width, height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
    img_size = scaled_image.size()
    try:
        if encoded:
            result = custom_encode(scaled_image, img_type, img_size)
        else:
            result = default_encode(scaled_image, img_type, img_size)
    except Exception as e:
        Logger.log("d", "Unable to encode screenshot: " + str(e))
    return result

def take_screenshot():
    # param width: width of the aspect ratio default 300
    # param height: height of the aspect ratio default 300
    # return: None when there is no model on the build plate otherwise it will return an image
    return Snapshot.snapshot(width = 900, height = 900)

def generate_preview(global_container_stack, image):
    screenshot_string = ""
    meta_data = global_container_stack.getMetaData()
    Logger.log("d", "Get current preview settings.")
    encoded = False
    if Constants.IS_PREVIEW_ENCODED in meta_data:
        encoded = True
    if Constants.SIMAGE in meta_data:
        simage = int(global_container_stack.getMetaDataEntry(Constants.SIMAGE))
        Logger.log("d", "mks_simage value: " + str(simage))
        screenshot_string += add_screenshot_str(image, simage, simage, ";simage:",encoded)
    if Constants.GIMAGE in meta_data:
        gimage = int(global_container_stack.getMetaDataEntry(Constants.GIMAGE))
        Logger.log("d", "mks_gimage value: " + str(gimage))
            # ;; - needed for correct colors. do not remove them.
        screenshot_string += add_screenshot_str(image, gimage, gimage, ";;gimage:",encoded)
    screenshot_string += "\r"
    return simage,gimage,screenshot_string

def add_preview(self):
    application = Application.getInstance()

    scene = application.getController().getScene()

    global_container_stack = application.getGlobalContainerStack()
    if not global_container_stack:
        return

    # If the scene does not have a gcode, do nothing
    gcode_dict = getattr(scene, "gcode_dict", {})
    if not gcode_dict:  # this also checks for an empty dict
        Logger.log("w", "Scene has no gcode to process")
        return

    dict_changed = False

    processed_marker = ";MKSPREVIEWPROCESSED\n"

    image = take_screenshot()
    screenshot_string = ""
    simage = 0
    gimage = 0

    if image:
        simage, gimage, screenshot_string = generate_preview(global_container_stack, image)
    else:
        Logger.log("d", "Skipping adding screenshot")
        return
    
    for plate_id in gcode_dict:
        gcode_list = gcode_dict[plate_id]
        if len(gcode_list) < 2:
            Logger.log("w", "Plate %s does not contain any layers", plate_id)
            continue

        if processed_marker in gcode_list[0]:
            Logger.log("d", "Plate %s has already been processed", plate_id)
            continue

        # adding to header
        gcode_list[0] += processed_marker
        gcode_list[0] += "; Postprocessed by [MKS WiFi plugin](https://github.com/PrintMakerLab/mks-wifi-plugin)\n"
        gcode_list[0] += "; simage=%d\n" % simage
        gcode_list[0] += "; gimage=%d\n" % gimage
        gcode_list[0] = screenshot_string + gcode_list[0]
        gcode_dict[plate_id] = gcode_list
        dict_changed = True

    if dict_changed:
        setattr(scene, "gcode_dict", gcode_dict)

