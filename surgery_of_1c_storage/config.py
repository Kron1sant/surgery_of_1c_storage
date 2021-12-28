import configparser
import os

PARAMS = configparser.ConfigParser()


def init_config(config_file_name):
    if not os.path.exists(config_file_name):
        full_path = os.path.abspath(config_file_name)
        raise Exception(f'Файл с конфигурацией не найден по указанному пути: {full_path}')
    PARAMS.read(config_file_name)
    return PARAMS


def create_config_file(filename, db_type):
    with open(filename, 'w') as f:
        if db_type == 'psql':
            f.write(template_config_file_psql.strip())
        elif db_type == 'mssql':
            f.write(template_config_file_mssql.strip())
        else:
            raise Exception('Неизвестный тип СУБД')
    print(f'Шаблон конфигурационного файла для {db_type} сохранен в {filename}')


template_config_file_psql = """
[Database]
TYPE = Postgres
SERVER = host
USER = postgres
PASSWORD = postgres
BASENAME = infobase

[InnerStructureKeys]
TABLES_WITH_CONFIG_FILE = params,files,config,configsave,configcas,configcassave

[Coder]
FILE_ENCODE_MODE = .encode_modes
"""

template_config_file_mssql = """
[Database]
TYPE = MSSQL
SERVER = host
USER = USR1CV8
PASSWORD = USR1CV8
BASENAME = infobase
ODBC_DRIVER={SQL Server Native Client 11.0}

[InnerStructureKeys]
TABLES_WITH_CONFIG_FILE = params,files,config,configsave,configcas,configcassave

[Coder]
FILE_ENCODE_MODE = .encode_modes
"""