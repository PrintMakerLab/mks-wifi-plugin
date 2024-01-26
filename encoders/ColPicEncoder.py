# Copyright (c) 2024
# MKS Plugin is released under the terms of the AGPLv3 or higher.


def ColPic_EncodeStr(from_color16, image_width, image_height, output_data: bytearray, output_max_t_size, colors_max):
    qty = 0
    temp = 0
    str_index = 0
    hex_index = 0
    temp_byte_array = bytearray(4)
    qty = ColPicEncode(from_color16, image_width, image_height, output_data, output_max_t_size, colors_max)
    if qty == 0:
        return 0
    temp = 3 - qty % 3
    while temp > 0 and qty < output_max_t_size:
        output_data[qty] = 0
        qty += 1
        temp -= 1

    if qty * 4 / 3 >= output_max_t_size:
        return 0
    hex_index = qty
    str_index = qty * 4 / 3
    while hex_index > 0:
        hex_index -= 3
        str_index -= 4
        temp_byte_array[0] = output_data[hex_index] >> 2
        temp_byte_array[1] = output_data[hex_index] & 3
        temp_byte_array[1] <<= 4
        temp_byte_array[1] += output_data[hex_index + 1] >> 4
        temp_byte_array[2] = output_data[hex_index + 1] & 15
        temp_byte_array[2] <<= 2
        temp_byte_array[2] += output_data[hex_index + 2] >> 6
        temp_byte_array[3] = output_data[hex_index + 2] & 63
        temp_byte_array[0] += 48
        if chr(temp_byte_array[0]) == '\\':
            temp_byte_array[0] = 126
        temp_byte_array[1] += 48
        if chr(temp_byte_array[1]) == '\\':
            temp_byte_array[1] = 126
        temp_byte_array[2] += 48
        if chr(temp_byte_array[2]) == '\\':
            temp_byte_array[2] = 126
        temp_byte_array[3] += 48
        if chr(temp_byte_array[3]) == '\\':
            temp_byte_array[3] = 126
        output_data[int(str_index)] = temp_byte_array[0]
        output_data[int(str_index) + 1] = temp_byte_array[1]
        output_data[int(str_index) + 2] = temp_byte_array[2]
        output_data[int(str_index) + 3] = temp_byte_array[3]

    qty = qty * 4 / 3
    output_data[int(qty)] = 0
    return qty


def ColPicEncode(from_color16, image_width, image_height, output_data: bytearray, output_max_t_size, colors_max):
    l0 = U16HEAD()
    Head0 = ColPicHead3()
    list_u16 = []
    for i in range(1024):
        list_u16.append(U16HEAD())

    ListQty = 0
    enqty = 0
    dotsqty = image_width * image_height
    if colors_max > 1024:
        colors_max = 1024
    for i in range(dotsqty):
        ListQty = ADList0(from_color16[i], list_u16, ListQty, 1024)

    for index in range(1, ListQty):
        l0 = list_u16[index]
        for i in range(index):
            if l0.qty >= list_u16[i].qty:
                alist_u16 = blist_u16 = list_u16.copy()
                for j in range(index - i):
                    list_u16[i + j + 1] = alist_u16[i + j]

                list_u16[i] = l0
                break

    while ListQty > colors_max:
        l0 = list_u16[ListQty - 1]
        minval = 255
        fid = -1
        for i in range(colors_max):
            cha0 = list_u16[i].A0 - l0.A0
            if cha0 < 0:
                cha0 = 0 - cha0
            cha1 = list_u16[i].A1 - l0.A1
            if cha1 < 0:
                cha1 = 0 - cha1
            cha2 = list_u16[i].A2 - l0.A2
            if cha2 < 0:
                cha2 = 0 - cha2
            chall = cha0 + cha1 + cha2
            if chall < minval:
                minval = chall
                fid = i

        for i in range(dotsqty):
            if from_color16[i] == l0.colo16:
                from_color16[i] = list_u16[fid].colo16

        ListQty = ListQty - 1

    for n in range(len(output_data)):
        output_data[n] = 0

    Head0.encodever = 3
    Head0.oncelistqty = 0
    Head0.mark = 98419516
    Head0.list_data_size = ListQty * 2
    output_data[0] = 3
    output_data[12] = 60
    output_data[13] = 195
    output_data[14] = 221
    output_data[15] = 5
    output_data[16] = ListQty * 2 & 255
    output_data[17] = (ListQty * 2 & 65280) >> 8
    output_data[18] = (ListQty * 2 & 16711680) >> 16
    output_data[19] = (ListQty * 2 & 4278190080) >> 24
    size_of_ColPicHead3 = 32
    for i in range(ListQty):
        output_data[size_of_ColPicHead3 + i * 2 + 1] = (list_u16[i].colo16 & 65280) >> 8
        output_data[size_of_ColPicHead3 + i * 2 + 0] = list_u16[i].colo16 & 255

    enqty = Byte8bitEncode(
        from_color16, 
        size_of_ColPicHead3, 
        Head0.list_data_size >> 1, 
        dotsqty, 
        output_data, 
        size_of_ColPicHead3 + Head0.list_data_size, 
        output_max_t_size - size_of_ColPicHead3 - Head0.list_data_size
    )
    Head0.color_data_size = enqty
    Head0.image_width = image_width
    Head0.image_height = image_height
    output_data[4] = image_width & 255
    output_data[5] = (image_width & 65280) >> 8
    output_data[6] = (image_width & 16711680) >> 16
    output_data[7] = (image_width & 4278190080) >> 24
    output_data[8] = image_height & 255
    output_data[9] = (image_height & 65280) >> 8
    output_data[10] = (image_height & 16711680) >> 16
    output_data[11] = (image_height & 4278190080) >> 24
    output_data[20] = enqty & 255
    output_data[21] = (enqty & 65280) >> 8
    output_data[22] = (enqty & 16711680) >> 16
    output_data[23] = (enqty & 4278190080) >> 24
    return size_of_ColPicHead3 + Head0.list_data_size + Head0.color_data_size


def ADList0(val, list_u16, ListQty, maxqty):
    qty = ListQty
    if qty >= maxqty:
        return ListQty
    for i in range(qty):
        if list_u16[i].colo16 == val:
            list_u16[i].qty += 1
            return ListQty

    A0 = val >> 11 & 31
    A1 = (val & 2016) >> 5
    A2 = val & 31
    list_u16[qty].colo16 = val
    list_u16[qty].A0 = A0
    list_u16[qty].A1 = A1
    list_u16[qty].A2 = A2
    list_u16[qty].qty = 1
    ListQty = qty + 1
    return ListQty


def Byte8bitEncode(from_color16, list_u16Index, listqty, dotsqty, output_data: bytearray, output_dataIndex, decMaxBytesize):
    list_u16 = output_data
    dots = 0
    src_index = 0
    dec_index = 0
    last_id = 0
    temp = 0
    while dotsqty > 0:
        dots = 1
        for i in range(dotsqty - 1):
            if from_color16[src_index + i] != from_color16[src_index + i + 1]:
                break
            dots += 1
            if dots == 255:
                break

        temp = 0
        for i in range(listqty):
            aa = list_u16[i * 2 + 1 + list_u16Index] << 8
            aa |= list_u16[i * 2 + 0 + list_u16Index]
            if aa == from_color16[src_index]:
                temp = i
                break

        tid = int(temp % 32)
        if tid > 255:
            tid = 255
        sid = int(temp / 32)
        if sid > 255:
            sid = 255
        if last_id != sid:
            if dec_index >= decMaxBytesize:
                dotsqty = 0
                break
            output_data[dec_index + output_dataIndex] = 7
            output_data[dec_index + output_dataIndex] <<= 5
            output_data[dec_index + output_dataIndex] += sid
            dec_index += 1
            last_id = sid
        if dots <= 6:
            if dec_index >= decMaxBytesize:
                dotsqty = 0
                break
            aa = dots
            if aa > 255:
                aa = 255
            output_data[dec_index + output_dataIndex] = aa
            output_data[dec_index + output_dataIndex] <<= 5
            output_data[dec_index + output_dataIndex] += tid
            dec_index += 1
        else:
            if dec_index >= decMaxBytesize:
                dotsqty = 0
                break
            output_data[dec_index + output_dataIndex] = 0
            output_data[dec_index + output_dataIndex] += tid
            dec_index += 1
            if dec_index >= decMaxBytesize:
                dotsqty = 0
                break
            aa = dots
            if aa > 255:
                aa = 255
            output_data[dec_index + output_dataIndex] = aa
            dec_index += 1
        src_index += dots
        dotsqty -= dots

    return dec_index


class U16HEAD:

    def __init__(self):
        self.colo16 = 0
        self.A0 = 0
        self.A1 = 0
        self.A2 = 0
        self.res0 = 0
        self.res1 = 0
        self.qty = 0


class ColPicHead3:

    def __init__(self):
        self.encodever = 0
        self.res0 = 0
        self.oncelistqty = 0
        self.image_width = 0
        self.image_height = 0
        self.mark = 0
        self.list_data_size = 0
        self.color_data_size = 0
        self.res1 = 0
        self.res2 = 0