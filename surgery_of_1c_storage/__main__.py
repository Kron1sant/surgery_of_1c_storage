import cli
import config
import dbexecutor
import usermanager


class SurgeryOf1CStorage:
    """Класс реализует основные функции по работе с внутренним форматом хранения файлов конфигурации 1С"""
    def __init__(self):
        self.PARAMS = None

    def init_config(self, config_file):
        self.PARAMS = config.init_config(config_file)
        self.show_welcome()

    def dump_inner_config_files(self, path_to_files, tablename='', filename=''):
        if tablename:
            tables = [tablename]
        else:
            tables = self.PARAMS['InnerStructureKeys']['TABLES_WITH_CONFIG_FILE'].split(',')
        for table_with_file in tables:
            dbexecutor.get_datafiles_from_table(path_to_files, tablename=table_with_file, certain_filename=filename)

    def load_inner_config_files(self, path_to_files, tablename='', filename=''):
        if tablename:
            tables = [tablename]
        else:
            tables = self.PARAMS['InnerStructureKeys']['TABLES_WITH_CONFIG_FILE'].split(',')
        for table_with_file in tables:
            dbexecutor.set_datafiles_in_table(path_to_files, tablename=table_with_file, certain_filename=filename)

    def dump_inner_user_info(self, path_to_files, username='', only_admins=False):
        dbexecutor.get_datafiles_from_table(path_to_files, tablename='params', certain_filename='users.usr')
        dbexecutor.get_user_info_from_v8users(path_to_files, username, only_admins)

    def load_inner_user_info(self, path_to_files, username='', only_admins=False):
        dbexecutor.set_datafiles_in_table(path_to_files, tablename='params', certain_filename='users.usr')
        dbexecutor.set_user_info_in_v8users(path_to_files, username, only_admins)

    def dump_inner_config_files_by_sql(self, path_to_files, query_text):
        dbexecutor.get_datafiles_from_table(path_to_files, query_text=query_text)

    def load_inner_config_files_by_sql(self, path_to_files, query_text):
        dbexecutor.set_datafiles_in_table(path_to_files, query_text=query_text)

    def add_admin_to_base(self, username, user_password='', role_names_str='ПолныеПрава,АдминистраторСистемы'):
        print('Выполняется поиск Полных прав в конфигурации. Может занять несколько минут...')
        role_names = role_names_str.split(',')
        full_rights_role_ids = usermanager.get_role_id_by_name(role_names)
        user_params = {'username': username,
                       'default_admin': True,
                       'roles_ids': full_rights_role_ids,
                       'password': user_password}
        print('Генерация параметров пользователя и добавление в БД...')
        usermanager.add_new_user(**user_params)
        print('Помещение пользователя в таблицы БД...')
        print(f'Пользователь {username} добавлен в базу данных')

    def show_welcome(self):
        print(f"Параметры конфигурации: Тип={self.PARAMS['Database']['TYPE']}; "
            + f"Сервер БД={self.PARAMS['Database']['SERVER']}; "
            + f"БД={self.PARAMS['Database']['BASENAME']}"
            + '\n')

if __name__ == '__main__':
    app = SurgeryOf1CStorage()
    # Запуск основного режима работы через CLI
    cli.run_cli(obj=app)
