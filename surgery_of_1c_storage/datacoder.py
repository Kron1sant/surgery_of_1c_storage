import zlib


def decode_raw_datafile(filename, rawdata):
    if rawdata[0:3] == b'\xef\xbb\xbf':
        decoded_data = rawdata
        mode = 'utf'
    elif filename == 'users.usr':
        decoded_data, mask_size, mask = decode_data_by_mask(rawdata)
        mode = 'mask'
        # В режиме кодировки запомним длину маски и саму маску - эти данные нужны для обратной кодировки
        mode += '$' + str(mask_size) + '$' + mask.hex()
    else:
        decoded_data = decode_data_by_inflate(rawdata)
        mode = 'deflate'

    return decoded_data, mode


def encode_datafile(bin_data, encode_mode):
    if encode_mode.startswith('mask'):
        encode_mode, mask_size, mask = encode_mode.split('$')
        mask_size = int(mask_size)
        mask = bytes.fromhex(mask)
    if encode_mode == 'utf':
        encoded_data = bin_data
    elif encode_mode == 'mask':
        encoded_data = encode_data_by_mask(bin_data, mask_size, mask)
    elif encode_mode == 'deflate':
        encoded_data = encode_data_by_inflate(bin_data)
    else:
        raise Exception(f'Неизвестный формат кодирования {encode_mode}')

    return encoded_data


def decode_data_by_inflate(sourcedata):
    return zlib.decompress(sourcedata, -15)


def encode_data_by_inflate(sourcedata):
    compressobj = zlib.compressobj(-1, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
    return compressobj.compress(sourcedata) + compressobj.flush()


def decode_data_by_mask(sourcedata):
    mask_size = sourcedata[0]  # В первом байте длина маски
    mask_start_pos = 1  # Позиция начала маски
    mask = sourcedata[mask_start_pos: mask_start_pos + mask_size]  # Байты самой маски

    data_start_pos = mask_start_pos + mask_size  # Позиция начала данных
    index_in_mask = 0  # Номер байта в маске, для циклического прохода
    decoded_data = bytes()  # Результат декодирования
    for index_in_data in range(data_start_pos, len(sourcedata)):
        if index_in_mask == mask_size:
            # Индекс текущего байта в маске "ходит по кругу",
            # при достижении конца маски - сброс на начало
            index_in_mask = 0

        decoded_symbol = sourcedata[index_in_data] ^ mask[index_in_mask]  # Через XOR декодируем очередной байт данных
        # Так как после декодирования результат был приведен к типу int, то преобразуем его явно к bytes.
        bytes_per_symbol = 1  # Диапазон целых числ в результате декодирования всегда умещается в один байт
        decoded_byte = decoded_symbol.to_bytes(bytes_per_symbol, 'big')  # Явное выражение int в bytes
        decoded_data += decoded_byte  # Помещаем в общий результат
        index_in_mask += 1

    return decoded_data, mask_size, mask


def encode_data_by_mask(sourcedata, mask_size, mask):
    data_start_pos = 0  # Позиция начала данных
    index_in_mask = 0  # Номер байта в маске, для циклического прохода
    encoded_data = bytes()  # Результат кодирования
    for index_in_data in range(data_start_pos, len(sourcedata)):
        if index_in_mask == mask_size:
            # Индекс текущего байта в маске "ходит по кругу",
            # при достижении конца маски - сброс на начало
            index_in_mask = 0

        encoded_symbol = sourcedata[index_in_data] ^ mask[index_in_mask]  # Через XOR кодируем очередной байт данных
        # Так как после кодирования результат был приведен к типу int, то преобразуем его явно к bytes.
        bytes_per_symbol = 1  # Диапазон целых числ в результате декодирования всегда умещается в один байт
        encoded_byte = encoded_symbol.to_bytes(bytes_per_symbol, 'big')  # Явное выражение int в bytes
        encoded_data += encoded_byte  # Помещаем в общий результат
        index_in_mask += 1
    # Итоговые двоичные данные собираются по схеме: [Размер маски][Маски][Закодированные данные]
    bytes_per_symbol = 1
    encoded_data = mask_size.to_bytes(bytes_per_symbol, 'big') + mask + encoded_data
    return encoded_data
