import unittest
import config


class Test(unittest.TestCase):
    """Тестирование модуля по загрузке конфигурации с параметрами"""

    def test_fail_init_config(self):
        wrong_filename = 'not_exists_config.ini'
        error_msg_pattern = f'Файл с конфигурацией не найден по указанному пути: .*{wrong_filename}'
        self.assertRaisesRegex(Exception, error_msg_pattern, config.init_config, wrong_filename)

    def test_init_config(self):
        correct_filename = 'test_config.ini'
        TEST_PARAMS = config.init_config(correct_filename)
        self.assertEqual(TEST_PARAMS['Database']['TYPE'], 'Postgres')
        self.assertEqual(TEST_PARAMS['Database']['SERVER'], 'TestSrv')
        self.assertEqual(TEST_PARAMS['Database']['USER'], 'postgres')
        self.assertEqual(TEST_PARAMS['Database']['PASSWORD'], 'postgres')
        self.assertEqual(TEST_PARAMS['Database']['BASENAME'], 'TestBase')
        self.assertEqual(TEST_PARAMS['Database']['ODBC_DRIVER'], '{ODBC_DRIVER}')
        self.assertEqual(TEST_PARAMS['InnerStructureKeys']['TABLES_WITH_CONFIG_FILE'],
                         'params,files,config,configsave,configcas,configcassave')
        self.assertEqual(TEST_PARAMS['Coder']['FILE_ENCODE_MODE'], '.encode_modes')


if __name__ == "__main__":
    unittest.main()
