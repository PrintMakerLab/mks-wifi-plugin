from cura.CuraApplication import CuraApplication
from UM.Math.Vector import Vector
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.Snapshot import Snapshot
from PyQt5.QtCore import Qt
import os
import string


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


def add_screenshot(img, width, height, img_type):
    result = ""
    b_image = img.scaled(width, height, Qt.KeepAspectRatio)
    # b_image.save(os.path.abspath("")+"\\test_"+str(width)+"_.png")
    # img.save(os.path.abspath("") + "\\testb_" + str(width) + "_.png")
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
            strHex = "%x" % rgb
            if len(strHex) == 3:
                strHex = '0' + strHex[0:3]
            elif len(strHex) == 2:
                strHex = '00' + strHex[0:2]
            elif len(strHex) == 1:
                strHex = '000' + strHex[0:1]
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
	
def transliterator(string):
    capital_letters = {
        u'А': u'A',
        u'Б': u'B',
        u'В': u'V',
        u'Г': u'G',
        u'Д': u'D',
        u'Е': u'E',
        u'Ё': u'E',
        u'Ж': u'Zh',
        u'З': u'Z',
        u'И': u'I',
        u'Й': u'Y',
        u'К': u'K',
        u'Л': u'L',
        u'М': u'M',
        u'Н': u'N',
        u'О': u'O',
        u'П': u'P',
        u'Р': u'R',
        u'С': u'S',
        u'Т': u'T',
        u'У': u'U',
        u'Ф': u'F',
        u'Х': u'H',
        u'Ц': u'Ts',
        u'Ч': u'Ch',
        u'Ш': u'Sh',
        u'Щ': u'Sch',
        u'Ъ': u'',
        u'Ы': u'Y',
        u'Ь': u'',
        u'Э': u'E',
        u'Ю': u'Yu',
        u'Я': u'Ya'
    }

    lower_case_letters = {
        u'а': u'a',
        u'б': u'b',
        u'в': u'v',
        u'г': u'g',
        u'д': u'd',
        u'е': u'e',
        u'ё': u'e',
        u'ж': u'zh',
        u'з': u'z',
        u'и': u'i',
        u'й': u'y',
        u'к': u'k',
        u'л': u'l',
        u'м': u'm',
        u'н': u'n',
        u'о': u'o',
        u'п': u'p',
        u'р': u'r',
        u'с': u's',
        u'т': u't',
        u'у': u'u',
        u'ф': u'f',
        u'х': u'h',
        u'ц': u'ts',
        u'ч': u'ch',
        u'ш': u'sh',
        u'щ': u'sch',
        u'ъ': u'',
        u'ы': u'y',
        u'ь': u'',
        u'э': u'e',
        u'ю': u'yu',
        u'я': u'ya',
        ' ': '_'
    }

    translit_string = ""

    for index, char in enumerate(string):
        if char in lower_case_letters.keys():
            char = lower_case_letters[char]
        elif char in capital_letters.keys():
            char = capital_letters[char]
            if len(string) > index+1:
                if string[index+1] not in lower_case_letters.keys():
                    char = char.upper()
            else:
                char = char.upper()
        translit_string += char

    return translit_string
	