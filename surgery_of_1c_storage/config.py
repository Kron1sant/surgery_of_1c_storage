import configparser
import os

PARAMS = configparser.ConfigParser()


def init_config(config_file_name):
    if not os.path.exists(config_file_name):
        full_path = os.path.abspath(config_file_name)
        raise Exception(f'Файл с конфигурацией не найден по указанному пути: {full_path}')
    PARAMS.read(config_file_name)
    return PARAMS
