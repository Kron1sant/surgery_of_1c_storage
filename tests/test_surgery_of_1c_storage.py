import unittest
from surgery_of_1c_storage.__main__ import SurgeryOf1CStorage
import tempfile
import os
import sys
from contextlib import contextmanager
from io import StringIO


class TestSurgeryOf1CStorage(unittest.TestCase):
    """Тест проходятся только при наличии развернутых тестовых баз на Postgres и MS SQL
    Параметры подключения должны быть указаны в файлах .test_base_conf_psql.ini и .test_base_conf_mssql.ini"""

    def setUp(self) -> None:
        self.app = SurgeryOf1CStorage()
        pass

    def _base_conf_init(self, db_type):
        test_base_config = f'.test_base_conf_{db_type}.ini'
        self.app.init_config(test_base_config)

    def _dump_inner_config_files(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            tablename = 'params'
            filename = '1a621f0f-5568-4183-bd9f-f6ef670e7090.si'
            with captured_output() as (out, err):
                self.app.dump_inner_config_files(path_to_files, tablename, filename)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего из таблицы params загружено 1 файлов. Ошибок распаковки 0'
            self.assertEqual(output.split('\n')[-1], check_msg)

            directory = os.path.join(path_to_files, tablename)
            filename_decode_modes = self.app.PARAMS['Coder']['FILE_ENCODE_MODE']
            # Проверка наличия файлов выгрузки
            self.assertTrue(os.path.exists(os.path.join(directory, filename_decode_modes)))
            self.assertTrue(os.path.exists(os.path.join(directory, filename)))

    def _load_inner_config_files(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            tablename = 'params'
            filename = '1a621f0f-5568-4183-bd9f-f6ef670e7090.si'
            with captured_output() as (out, err):
                self.app.dump_inner_config_files(path_to_files, tablename, filename)
                self.app.load_inner_config_files(path_to_files, tablename, filename)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего в таблицу params загружено 1 файлов'
            self.assertEqual(output.split('\n')[-1], check_msg)

    def _dump_inner_user_info(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            username = 'Администратор'
            with captured_output() as (out, err):
                self.app.dump_inner_user_info(path_to_files, username=username)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего выгружено пользователей 1'
            self.assertEqual(output.split('\n')[-1], check_msg)

            directory = os.path.join(path_to_files, 'params')
            filename_decode_modes = self.app.PARAMS['Coder']['FILE_ENCODE_MODE']
            # Проверка наличия файлов выгрузки
            self.assertTrue(os.path.exists(os.path.join(directory, filename_decode_modes)))
            self.assertTrue(os.path.exists(os.path.join(directory, 'users.usr')))
            self.assertTrue(os.path.exists(os.path.join(path_to_files, 'v8users')))

    def _load_inner_user_info(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            username = 'Администратор'
            with captured_output() as (out, err):
                self.app.dump_inner_user_info(path_to_files, username=username)
                self.app.load_inner_user_info(path_to_files, username=username)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего в v8users загружено пользователей 1'
            self.assertEqual(output.split('\n')[-1], check_msg)

            directory = os.path.join(path_to_files, 'params')
            filename_decode_modes = self.app.PARAMS['Coder']['FILE_ENCODE_MODE']
            # Проверка наличия файлов выгрузки
            self.assertTrue(os.path.exists(os.path.join(directory, filename_decode_modes)))
            self.assertTrue(os.path.exists(os.path.join(directory, 'users.usr')))
            self.assertTrue(os.path.exists(os.path.join(path_to_files, 'v8users')))

    def _dump_inner_config_files_by_sql(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            query = "SELECT 'currenschema', currentschema FROM schemastorage WHERE schemaid=0;"
            with captured_output() as (out, err):
                self.app.dump_inner_config_files_by_sql(path_to_files, query)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего из таблицы None загружено 1 файлов. Ошибок распаковки 0'
            self.assertEqual(output.split('\n')[-1], check_msg)

            # Проверка наличия файлов выгрузки
            filename_decode_modes = self.app.PARAMS['Coder']['FILE_ENCODE_MODE']
            self.assertTrue(os.path.exists(os.path.join(path_to_files, filename_decode_modes)))
            self.assertTrue(os.path.exists(os.path.join(path_to_files, 'currenschema')))

    def _load_inner_config_files_by_sql(self, db_type):
        self._base_conf_init(db_type)
        with tempfile.TemporaryDirectory() as path_to_files:
            query_dump = "SELECT 'currenschema', currentschema FROM schemastorage WHERE schemaid=0;"
            query_load = "UPDATE schemastorage SET currentschema = ? WHERE schemaid=0"
            with captured_output() as (out, err):
                self.app.dump_inner_config_files_by_sql(path_to_files, query_dump)
                self.app.load_inner_config_files_by_sql(path_to_files, query_load)
            output = out.getvalue().strip()
            # Проверка сообщения из StdOut
            check_msg = 'Всего в таблицу None загружено 1 файлов'
            self.assertEqual(output.split('\n')[-1], check_msg)

            # Проверка наличия файлов выгрузки
            filename_decode_modes = self.app.PARAMS['Coder']['FILE_ENCODE_MODE']
            self.assertTrue(os.path.exists(os.path.join(path_to_files, filename_decode_modes)))
            self.assertTrue(os.path.exists(os.path.join(path_to_files, 'currenschema')))


class TestSurgeryOf1CStorageCommon(TestSurgeryOf1CStorage):
    def test_init_config(self):
        correct_filename = 'test_config.ini'
        self.app.init_config(correct_filename)
        self.assertGreater(len(self.app.PARAMS), 0)


class TestSurgeryOf1CStoragePostgres(TestSurgeryOf1CStorage):
    def test_dump_inner_config_files(self):
        self._dump_inner_config_files('psql')

    def test_load_inner_config_files(self):
        self._load_inner_config_files('psql')

    def test_dump_inner_user_info(self):
        self._dump_inner_user_info('psql')

    def test_load_inner_user_info(self):
        self._load_inner_user_info('psql')

    def test_dump_inner_config_files_by_sql(self):
        self._dump_inner_config_files_by_sql('psql')

    def test_load_inner_config_files_by_sql(self):
        self._load_inner_config_files_by_sql('psql')


class TestSurgeryOf1CStorageMSSQL(TestSurgeryOf1CStorage):
    def test_dump_inner_config_files(self):
        self._dump_inner_config_files('mssql')

    def test_load_inner_config_files(self):
        self._load_inner_config_files('mssql')

    def test_dump_inner_user_info(self):
        self._dump_inner_user_info('mssql')

    def test_load_inner_user_info(self):
        self._load_inner_user_info('mssql')

    def test_dump_inner_config_files_by_sql(self):
        self._dump_inner_config_files_by_sql('mssql')

    def test_load_inner_config_files_by_sql(self):
        self._load_inner_config_files_by_sql('mssql')


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


if __name__ == "__main__":
    unittest.main()
