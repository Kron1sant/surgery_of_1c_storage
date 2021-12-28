import click
import os


@click.group()
@click.option('--config-file', type=click.Path(), default='config.ini', help='Конфигурационный файл')
@click.pass_obj
def run_cli(obj, config_file):
    """Работа с внутренним форматом хранения файлов конфигурации 1С"""
    if not os.path.exists(config_file):
        return
    obj.init_config(config_file)


@run_cli.command('dump', help='Выгрузить и раскодировать внутренние файлы конфигурации')
@click.option('-o', '--path-to-files', type=click.Path(), default='ConfigFiles', help='(Output) Путь к выгрузке')
@click.option('-t', '--table-name', default='', help='Имя выгружаемой таблицы. Если не указано, то выгружаются '
                                                     'таблицы указанные в файле конфигурации')
@click.option('-f', '--file-name', default='', help='Имя выгружаемого файла. Если не указано, то выгружаются все файлы')
@click.pass_obj
def dump_inner_config_files(obj, path_to_files, table_name, file_name):
    obj.dump_inner_config_files(path_to_files, table_name, file_name)


@run_cli.command('load', help='Закодировать и загрузить внутренние файлы конфигурации')
@click.option('-i', '--path-to-files', type=click.Path(), default='ConfigFiles', help='(Input) Каталог для загрузки')
@click.option('-t', '--table-name', default='', help='Имя загружаемой таблицы. Если не указано, то загружаются все '
                                                     'таблицы из каталога для загрузки')
@click.option('-f', '--file-name', default='', help='Имя загружаемого файла. Если не указано, то загружаются все файлы')
@click.pass_obj
def load_inner_config_files(obj, path_to_files, table_name, file_name):
    obj.load_inner_config_files(path_to_files, table_name, file_name)


@run_cli.command('dump-users', help='Выгрузить и раскодировать информацию о пользователях')
@click.option('-o', '--path-to-files', type=click.Path(), default='UsersFiles', help='(Output) Путь к выгрузке')
@click.option('-U', '--user-name', default='', help='Имя пользователя')
@click.option('-a', '--only-admins', is_flag=True, help='Выгрузить только админов')
@click.pass_obj
def dump_inner_user_info(obj, path_to_files, user_name, only_admins):
    obj.dump_inner_user_info(path_to_files, user_name, only_admins)


@run_cli.command('load-users', help='Закодировать и загрузить информацию о пользователях')
@click.option('-i', '--path-to-files', type=click.Path(), default='UsersFiles', help='(Input) Каталог для загрузки')
@click.option('-U', '--user-name', default='', help='Имя пользователя')
@click.option('-a', '--only-admins', is_flag=True, help='Загрузить только админов')
@click.pass_obj
def load_inner_user_info(obj, path_to_files, user_name, only_admins):
    obj.load_inner_user_info(path_to_files, user_name, only_admins)


@run_cli.command('dump-by-sql', help='Выгрузить и раскодировать одно поле по конкретному запросу')
@click.option('-o', '--path-to-files', type=click.Path(), default='DataByQuery', help='(Output) Путь к выгрузке')
@click.option('-q', '--query-text', default='', help='Текст SQL запроса, который должен вернуть (SELECT) два поля: '
                                                     'имя файла и двоичные данные файла. Например:\n'
                                                     'SELECT ''currenschema'', currentschema FROM schemastorage WHERE '
                                                     'schemaid=0')
@click.pass_obj
def dump_inner_config_files_by_sql(obj, path_to_files, query_text):
    obj.dump_inner_config_files_by_sql(path_to_files, query_text)


@run_cli.command('load-by-sql', help='Закодировать и загрузить одно поле по конкретному запросу')
@click.option('-i', '--path-to-files', type=click.Path(), default='DataByQuery', help='(Input) Каталог для загрузки')
@click.option('-q', '--query-text', default='', help='Текст SQL запроса, который должен обновить (UPDATE) поле с '
                                                     'двоичными данными. Сами двоичные данные будут переданы через '
                                                     'параметр, обозначенный ?. Например,\n'
                                                     'UPDATE schemastorage SET currentschema = ? WHERE schemaid=0')
@click.pass_obj
def load_inner_config_files_by_sql(obj, path_to_files, query_text):
    obj.load_inner_config_files_by_sql(path_to_files, query_text)


@run_cli.command('add-admin', help='Добавить нового пользователя с полными правами')
@click.option('-U', '--user-name', default='Administrator', help='Имя пользователя')
@click.option('-P', '--user-password', default='', help='Пароль пользователя')
@click.option('-r', '--role-names', default='ПолныеПрава,АдминистраторСистемы',
              help='Имена ролей через запятую (по умолчанию ПолныеПрава,АдминистраторСистемы)')
@click.pass_obj
def load_inner_user_info(obj, user_name, user_password, role_names):
    obj.add_admin_to_base(user_name, user_password, role_names)


@run_cli.command('init-config', help='Создает шаблон конфигурационного файла')
@click.option('-t', '--db-type', default='psql', help='Тип конфигурации по СУБД: psql, mssql')
@click.option('-n', '--new-config-name', default='config_template.ini', help='Имя создаваемого конфигурационного файла')
def init_config(db_type, new_config_name):
    import config
    config.create_config_file(new_config_name, db_type)
