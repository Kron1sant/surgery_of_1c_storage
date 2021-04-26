import psycopg2
import pyodbc
import config


def get_db_type():
    return str(config.PARAMS['Database']['TYPE']).lower()


def get_connector():
    db_type = get_db_type()
    init_params = config.PARAMS['Database']
    # Коннектор для PostgreSQL
    if db_type == 'postgres':
        return psycopg2.connect(
            host=init_params['SERVER'],
            database=init_params['BASENAME'],
            user=init_params['USER'],
            password=init_params['PASSWORD'])
    # Коннектор для MS SQL (через ODBC)
    elif db_type == 'mssql':
        return pyodbc.connect(
            f"DRIVER={init_params['ODBC_DRIVER']};"
            f"SERVER=tcp:{init_params['SERVER']};"
            f"DATABASE={init_params['BASENAME']};"
            f"UID={init_params['USER']};"
            f"PWD={init_params['PASSWORD']}")
    else:
        raise Exception('Данная СУБД не поддерживается')

