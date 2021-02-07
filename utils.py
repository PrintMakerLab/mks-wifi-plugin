# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from cura.CuraApplication import CuraApplication
from UM.Math.Vector import Vector
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.Snapshot import Snapshot
from PyQt5.QtCore import Qt
import os


def getRect():
    left = None
    front = None
    right = None
    back = None
    for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
        if node.getBoundingBoxMesh():
            if not left or node.getBoundingBox().left < left:
                left = node.getBoundingBox().left
            if not right or node.getBoundingBox().right > right:
                right = node.getBoundingBox().right
            if not front or node.getBoundingBox().front > front:
                front = node.getBoundingBox().front
            if not back or node.getBoundingBox().back < back:
                back = node.getBoundingBox().back
    if not (left and front and right and back):
        return 0
    result = max((right - left), (front - back))
    return result

def add_leading_zeros(rgb):
    strHex = "%x" % rgb
    strHexLen = len(strHex)
    if strHexLen == 3:
        strHex = '0' + strHex[0:3]
    elif strHexLen == 2:
        strHex = '00' + strHex[0:2]
    elif strHexLen == 1:
        strHex = '000' + strHex[0:1]
    return strHex

def add_screenshot_str(img, width, height, img_type):
    result = ""
    b_image = img.scaled(width, height, Qt.KeepAspectRatio)
    img_size = b_image.size()
    result += img_type
    datasize = 0
    for i in range(img_size.height()):
        for j in range(img_size.width()):
            pixel_color = b_image.pixelColor(j, i)
            r = pixel_color.red() >> 3
            g = pixel_color.green() >> 2
            b = pixel_color.blue() >> 3
            rgb = (r << 11) | (g << 5) | b
            strHex = add_leading_zeros(rgb)
            if strHex[2:4] != '':
                result += strHex[2:4]
                datasize += 2
            if strHex[0:2] != '':
                result += strHex[0:2]
                datasize += 2
            if datasize >= 50:
                datasize = 0
        # if i != img_size.height() - 1:
        result += '\rM10086 ;'
        if i == img_size.height() - 1:
            result += "\r"
    return result


def take_screenshot():
    cut_image = Snapshot.snapshot(width = 900, height = 900)
    return cut_image

def add_screenshot():
    image = take_screenshot()
    screenshot_string = ""
    if image:
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "mks_simage" in meta_data:
                simage = int(global_container_stack.getMetaDataEntry("mks_simage"))
                screenshot_string += add_screenshot_str(image, simage, simage, ";simage:")
            if "mks_gimage" in meta_data:
                gimage = int(global_container_stack.getMetaDataEntry("mks_gimage"))
                screenshot_string += add_screenshot_str(image, gimage, gimage, ";;gimage:")
            screenshot_string += "\r"
    else:
        Logger.log("d", "Skipping adding screenshot")
    return screenshot_string
