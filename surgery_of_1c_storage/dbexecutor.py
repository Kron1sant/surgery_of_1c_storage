import dbconnector
import os
import config
import datacoder
import usermanager
from datastructure1c import DataStructure1C


def get_datafiles_from_table(path_to_files, **kwargs):
    """ Нужно указать либо tablename, либо query
    query должен представляться собой текст SQL запроса на выборку данных (SELECT),
    в качестве полей выборки должны быть указаны: ИмяФайла и ДвоичныеДанные для декодирования.
    Например, SELECT 'currenschema', currentschema FROM schemastorage WHERE schemaid=0;"""

    tablename = kwargs.get('tablename')
    certain_filename = kwargs.get('certain_filename')
    query = kwargs.get('query_text')
    if tablename:
        directory = os.path.join(path_to_files, tablename)
        if certain_filename:
            query = f"SELECT filename, binarydata FROM {tablename} WHERE filename='{certain_filename}'"
        else:
            query = f"SELECT filename, binarydata FROM {tablename}"
    else:
        directory = path_to_files
        if not query:
            raise Exception('Для вызова процедуры нужно указать либо имя таблицы, либо текст SQL запроса')

    directory_exists = os.path.exists(directory)
    file_decode_modes = None
    count = 0
    fault_count = 0
    list_of_files = []
    with dbconnector.get_connector() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            fetched_data = cursor.fetchone()
            while fetched_data:
                filename = fetched_data[0]
                raw_bin_data = get_binary_data(fetched_data[1])
                try:
                    bin_data, decode_mode = datacoder.decode_raw_datafile(filename, raw_bin_data)
                except Exception as e:
                    print(f'Не удалось раскодировать файл {filename}\n{e}')
                    fault_count += 1
                    fetched_data = cursor.fetchone()
                    continue

                if not directory_exists:
                    os.makedirs(directory)
                    directory_exists = True

                if not file_decode_modes:
                    filename_decode_modes = config.PARAMS['Coder']['FILE_ENCODE_MODE']
                    file_decode_modes = open(os.path.join(directory, filename_decode_modes), 'w')

                path_to_file = os.path.join(directory, filename)
                with open(path_to_file, 'wb') as f:
                    f.write(bin_data)
                    file_decode_modes.write(f'{filename}\t{decode_mode}\n')
                    print(f'Сохранен файл {path_to_file}')
                    count += 1
                    list_of_files.append(path_to_file)
                fetched_data = cursor.fetchone()
    print(f'Всего из таблицы {tablename} загружено {count} файлов. Ошибок распаковки {fault_count}\n')
    if file_decode_modes and not file_decode_modes.closed:
        file_decode_modes.close()
    if count == 1:
        return list_of_files[0]
    else:
        return list_of_files


def set_datafiles_in_table(path_to_files, **kwargs):
    """ Нужно указать либо tablename, либо query
    query должен представляться собой текст SQL запроса на обновление данных (UPDATE),
    Сами двоичные данные будут переданы через параметр, обозначенный ?
    Например, UPDATE schemastorage SET currentschema = ? WHERE schemaid=0"""

    tablename = kwargs.get('tablename')
    certain_filename = kwargs.get('certain_filename')
    query = kwargs.get('query_text')
    if tablename:
        directory = os.path.join(path_to_files, tablename)
    else:
        directory = path_to_files
        if not query:
            raise Exception('Для вызова процедуры нужно указать либо имя таблицы, либо текст SQL запроса')

    if not os.path.exists(directory):
        print(f'Нет каталога для загрузки {directory}')
        return

    filename_encode_modes = config.PARAMS['Coder']['FILE_ENCODE_MODE']
    if filename_encode_modes not in os.listdir(directory):
        print(f'В каталоге нет файла с описанием внутренних фалйов и способа их кодирования:  {filename_encode_modes}')
        return

    count = 0
    encoded_files = open(os.path.join(directory, filename_encode_modes), 'r')
    with dbconnector.get_connector() as conn:
        with conn.cursor() as cursor:
            line = encoded_files.readline()
            while line:
                filename, encode_mode = line.strip().split('\t')
                if certain_filename and filename.strip().lower() != certain_filename.strip().lower():
                    continue
                path_to_file = os.path.join(directory, filename)
                with open(path_to_file, 'rb') as f:
                    bin_data = f.read()
                    raw_bin_data = datacoder.encode_datafile(bin_data, encode_mode)
                    if dbconnector.get_db_type() == 'postgres':
                        param_name = '%s'
                    else:
                        param_name = '?'
                    if tablename:
                        query = f"UPDATE {tablename} SET binarydata = {param_name} WHERE filename='{filename}'"
                    else:
                        query = query.replace('?', param_name)
                    cursor.execute(query, (raw_bin_data,))
                    print(f'Загружен файл {filename} в таблицу {tablename} базы данных')
                    count += 1
                line = encoded_files.readline()
    encoded_files.close()
    print(f'Всего в таблицу {tablename} загружено {count} файлов\n')


def get_user_info_from_v8users(path_to_files, certain_username, only_admins):
    # Поля таблицы v8users
    fields = usermanager.get_v8users_fields()
    # Формируем запрос на выборку в зависимости от входных параметров функции
    if certain_username:
        query = f"SELECT {','.join(fields)} " \
                f"FROM v8users WHERE name='{certain_username}'"
    elif only_admins:
        query = f"SELECT {','.join(fields)} FROM v8users " \
                f"WHERE admrole"
    else:
        query = f"SELECT {','.join(fields)} FROM v8users"

    with dbconnector.get_connector() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            # Данные из выборки записываем в новый файл v8users - формат csv
            path_to_file = os.path.join(path_to_files, 'v8users')
            with open(path_to_file, 'w') as f:
                fetched_data = cursor.fetchone()
                if fetched_data:
                    # выводим шапку CSV
                    f.write(f"{';'.join(fields)};mask_size;mask\n")

                count = 0
                while fetched_data:
                    userid = ''
                    username = ''
                    boolean_fields = ['show', 'eauth', 'admrole']
                    for field_index in range(0, len(fields)):
                        if fields[field_index] == 'data':
                            # В поле data лежат закодированные данные пользователя
                            bin_data = get_binary_data(fetched_data[field_index])
                            decoded_data, mask_size, mask = datacoder.decode_data_by_mask(bin_data)
                            user_info_filename = os.path.join(path_to_files, username + '-' + userid)
                            f.write(f'см. файл "{user_info_filename}";{str(mask_size)};{mask.hex()}\n')
                            with open(user_info_filename, 'wb') as f_user:
                                f_user.write(decoded_data)
                            print(f"Выгружена информация по пользователю: {username}")
                            count += 1
                        elif fields[field_index] == 'id':
                            # В поле id хранится идентифкатор пользователя
                            userid = get_binary_data(fetched_data[field_index]).hex()
                            f.write(userid + ';')
                        elif fields[field_index] == 'name':
                            username = fetched_data[field_index]
                            if not username:
                                # Имя может быть пустым
                                username = '=@NoName@='
                            f.write(username + ';')
                        elif fields[field_index] in boolean_fields:
                            # Для булевых полей явно сделаем приведение
                            if type(fetched_data[field_index]) == bool:
                                f.write(str(fetched_data[field_index]) + ';')
                            else:
                                f.write(str(fetched_data[field_index] == b'\x01') + ';')
                        else:
                            # Остальные поля просто записываем через разделитель ;
                            f.write(str(fetched_data[field_index]) + ';')
                    fetched_data = cursor.fetchone()
    print(f'Всего выгружено пользователей {count}\n')


def set_user_info_in_v8users(path_to_files, certain_username='', only_admins=False):
    # Для загрузки используется файл v8users - сформированный при выгрузке
    path_to_file = os.path.join(path_to_files, 'v8users')
    if not os.path.exists(path_to_file):
        print(f'Не найден файл со пользователями {path_to_file}')
        return
    # Поля таблицы v8users
    fields = usermanager.get_v8users_fields()

    with dbconnector.get_connector() as conn:
        with conn.cursor() as cursor:
            count = 0
            the_first_line = True
            for line in open(path_to_file, 'r'):
                if the_first_line:
                    # В первой строке шапка CSV, пропустим ее
                    the_first_line = False
                    continue

                fields_in_line = line.split(';')
                username = fields_in_line[fields.index('name')]
                if certain_username and username != certain_username:
                    # Если указан отбор по конкретному пользователю, то пропустим остальных
                    continue
                if only_admins and fields_in_line[fields.index('admrole')] != 'True':
                    # Если указан отбор только по администраторам, то пропустим остальных
                    continue

                userid_index = fields.index('id')
                userid = fields_in_line[userid_index]
                fields_in_line[userid_index] = bytes.fromhex(userid)  # ID приведем к типу bytes

                # Получим данные о пользователях из файла
                user_info_filename = os.path.join(path_to_files, username + '-' + userid)
                with open(user_info_filename, 'br') as f_user:
                    bin_data = f_user.read()
                # используем ранее полученную при выгрузке маску для кодирования
                mask = bytes.fromhex(fields_in_line[-1].strip())
                mask_size = int(fields_in_line[-2])
                # Закодируем данные по маске
                encoded_user_data = datacoder.encode_data_by_mask(bin_data, mask_size, mask)
                data_index = fields.index('data')
                fields_in_line[data_index] = encoded_user_data  # Подменим в данных для записи
                # Для булевых полей явно сделаем приведение
                boolean_fields = ['show', 'eauth', 'admrole']
                for bool_field in boolean_fields:
                    bool_field_index = fields.index(bool_field)
                    fields_in_line[bool_field_index] = True if fields_in_line[bool_field_index] == 'True' else False

                query = "BEGIN TRANSACTION;\n"
                if dbconnector.get_db_type() == 'postgres':
                    param_name = '%s'
                    query += f"DELETE FROM v8users WHERE id='\\\\x{userid}';\n"
                else:
                    param_name = '?'
                    query += f"DELETE FROM v8users WHERE id=0x{userid};\n"
                query += f"INSERT INTO v8users ({', '.join(fields)}) VALUES " \
                         f"({', '.join([param_name] * len(fields))});\n"
                query += "COMMIT;"
                # Два последних поля содержат маску - отсечем их
                query_params = tuple(fields_in_line[:-2])
                cursor.execute(query, query_params)
                count += 1
                print(f"Загружена информация по пользователю: {username}")
    print(f'Всего в v8users загружено пользователей {count}\n')


def get_binary_data(row_field):
    # Некоторые коннекторы возвращают двоичные данные через поле obj, а другие напрямую
    if dbconnector.get_db_type() == 'postgres':
        return bytes(row_field.obj)
    else:
        return row_field
