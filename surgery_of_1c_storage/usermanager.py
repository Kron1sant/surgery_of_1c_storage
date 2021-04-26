import uuid
from datetime import datetime
import os
import dbexecutor
from datastructure1c import DataStructure1C
import hashlib
import base64
import tempfile

EMPTY_UUID = uuid.UUID('00000000000000000000000000000000')


def compose_user_params_file(**kwargs):
    username = kwargs.get('username', 'Admin')
    fullname = kwargs.get('fullname', username)
    role_ids = kwargs.get('roles_ids', [])
    password = kwargs.get('password', '')
    default_admin = kwargs.get('default_admin', False)
    userid = kwargs.get('userid', None)

    user_params_template = get_user_params_template()
    if default_admin:
        make_default_admin_params(user_params_template)

    if userid:
        user_params_template[0] = userid

    user_params_template[1] = username
    if password:
        user_params_template[2] = b'\xef\xbf\xbd'.decode('utf-8')
    user_params_template[3] = fullname
    user_params_template[5] = [len(role_ids)] + role_ids
    user_params_template[12] = password_hash(password).decode('utf-8')
    user_params_template[13] = user_params_template[12]
    user_params_template[16] = datetime.now()

    data1C = DataStructure1C()
    data1C.compose_text(user_params_template)

    user_params = {'id': user_params_template[0], 'username': username, 'fullname': fullname, 'password': password,
                   'role_ids': role_ids}
    return data1C.to_utf(), user_params


def get_user_params_template():
    template = []
    template.append(uuid.uuid4())  # 00 UUID пользователя
    template.append('')  # 01 Имя пользователя
    template.append('')  # 02 ?
    template.append('')  # 03 Полное имя пользователя
    template.append(EMPTY_UUID)  # 04 ? нулевой UUID
    template.append([1, EMPTY_UUID])  # 05 Список ролей - первый элемент - это количество ролей
    template.append(EMPTY_UUID)  # 06 ? UUID чего-то / может быть нулевым
    template.append(0)  # 07 Вход в программу разрешен
    template.append(0)  # 08 Показывать в списке выбора
    template.append(None)  # 09 ИД для идентификации ОС
    template.append(0)  # 10 Аутентифкация ОС
    template.append(0)  # 11 Пользователю запрещено изменять пароль
    template.append('')  # 12 SHA1 хэш пароля в BASE64
    template.append('')  # 13 Повтор SHA1 хэш пароля в BASE64
    template.append(0)  # 14 Режим запуска (0-Обычное, 1-Управляемое, 2-Авто)
    template.append(0)  # 15 ? Способ аутентификации (4-запрещено открытие внешних обработок, 2 - разрешено)
    template.append(datetime.strptime('00010101000000', '%Y%m%d%H%M%S'))  # 16 Дата последнего изменения
    template.append(0)  # 17 ?
    template.append(0)  # 18 Индентификация по OpenID
    template.append([0])  # 19 ?
    template.append(0)  # 20 Защита от опасных действий
    template.append([0])  # 21 ?
    template.append(0)  # 22 ?
    return template


def make_default_admin_params(user_params):
    user_params[7] = 1
    user_params[8] = 1
    user_params[14] = 2
    user_params[15] = 2
    user_params[22] = 1


def password_hash(password):
    hashedpwd = hashlib.sha1(password.encode('utf-8'))
    return base64.standard_b64encode(hashedpwd.digest())


def get_role_id_by_name(role_names):
    with tempfile.TemporaryDirectory() as path_to_files:
        params_table = 'params'
        configuration_structure_file = '1a621f0f-5568-4183-bd9f-f6ef670e7090.si'  # Файл со структурой конфигурации
        filename = dbexecutor.get_datafiles_from_table(path_to_files, tablename=params_table,
                                                       certain_filename=configuration_structure_file)
        with open(filename, 'rb') as f:
            utf_text = f.read().decode('utf-8')
            config_structure = DataStructure1C().parse_text(utf_text)

    one_role = type(role_names) == str
    if one_role:
        role_names = [role_names]
    # Роли в тексте структуры конфигурации выгледят так:
    # },0,0,0e7b5458-99e2-4206-9ede-73faa7577ddd,d808b7e3-d608-41c6-91d3-b9eaf5acb7ca,8,"ПолныеПрава",
    # где первый UUID - относится к роли, второй - к корню конфигурации
    role_ids = []
    for role_name in role_names:
        try:
            # Ищем в корне второй ветке
            role_index = config_structure[2].index(role_name)
        except:
            # ToDo имеет смысл поискать вглубину по всему дереву
            raise Exception(f'В конфигуарции не обнаружена роль с именем {role_name}')

        role_id = config_structure[2][role_index-3]
        if not isinstance(role_id, uuid.UUID):
            raise Exception(f'UUID роли не был обнаружен в трех позициях слева как ожидалось. '
                            f'Вместо этого получено значение {role_id}')
        role_ids.append(role_id)

    return role_ids


def add_new_user(**kwargs):
    user_file_data, user_params = compose_user_params_file(**kwargs)
    with tempfile.TemporaryDirectory() as path_to_files:
        prepare_user_files_to_load(path_to_files, user_file_data, user_params)
        dbexecutor.set_user_info_in_v8users(path_to_files, certain_username=user_params['username'])


def prepare_user_files_to_load(path_to_files, user_file_data, user_params):
    userid_str = uuid_to_1c_format(user_params['id'].hex)
    user_info_filename = os.path.join(path_to_files, user_params['username'] + '-' + userid_str)
    with open(user_info_filename, 'wb') as f:
        f.write(user_file_data.encode('utf-8'))
    v8users_filename = os.path.join(path_to_files, 'v8users')
    with open(v8users_filename, 'w') as f:
        f.write(f"{';'.join(get_v8users_fields())};mask_size;mask\n")
        f.write(userid_str + ';')
        f.write(user_params['username'] + ';')
        f.write(user_params['fullname'] + ';')
        f.write('None;')
        cur_data = datetime.now()
        f.write(str(cur_data.year + 2000) + cur_data.strftime('-%m-%d %H:%M:%S') + ';')
        f.write('2;')
        f.write('True;')
        f.write('True;')
        f.write('True;')
        f.write('0;')
        f.write(';')
        f.write('28;')
        f.write('6e591a0fcf6db20377588a51191048679538d45193690d17ed12112b')


def get_v8users_fields():
    return ['id', 'name', 'descr', 'osname', 'changed', 'rolesid', 'show', 'eauth', 'admrole', 'ussprh', 'data']


def uuid_to_1c_format(hex_uuid):
    return hex_uuid[16:20] + hex_uuid[20:32] + hex_uuid[12:16] + hex_uuid[8:12] + hex_uuid[0:8]
