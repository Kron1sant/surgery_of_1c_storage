import unittest
import datastructure1c
from datetime import datetime

tested_data_hex = 'efbbbf7b61643164623139312d663638302d343266642d383436352d6162303738613966366632662c22d090d0b4d0bcd0b8d0bdd0b8d181d182d180d0b0d182d0bed180222c22222c22d090d0b4d0bcd0b8d0bdd0b8d181d182d180d0b0d182d0bed18020d092d0b8d0bad182d0bed180d0bed0b2d0b8d187222c30303030303030302d303030302d303030302d303030302d3030303030303030303030302c0d0a7b332c37363730326539652d666137612d346239382d626566612d6639623337646232646165302c38343966303334652d383564632d343531352d616165362d3234306331653064343664392c66646230313263392d353833612d343261662d393564612d3037306537356135383037387d2c64623461396363622d396566352d346233632d383537372d6236666535646231623632652c312c312c2c302c302c22326a6d6a376c35725377307956622f766c5741596b4b2f5942776b3d222c22326a6d6a376c35725377307956622f766c5741596b4b2f5942776b3d222c322c3235342c32303231303432343138313930392c302c302c0d0a7b307d2c302c0d0a7b307d2c317d '


class TestDataStructure1C(unittest.TestCase):
    def test_parse_text(self):
        utf_text = bytes.fromhex(tested_data_hex).decode('utf-8')
        data = datastructure1c.DataStructure1C(utf_text)
        self.assertEqual(len(data._tree), 23)
        self.assertEqual(data._tree[0].hex, 'ad1db191f68042fd8465ab078a9f6f2f')
        self.assertEqual(data._tree[1], 'Администратор')
        self.assertEqual(data._tree[3], 'Администратор Викторович')
        self.assertEqual(len(data._tree[5]), 4)
        self.assertEqual(data._tree[16], datetime.strptime('2021-04-24 18:19:09', '%Y-%m-%d %H:%M:%S'))

    def test_compose_text(self):
        utf_text = bytes.fromhex(tested_data_hex).decode('utf-8')
        data = datastructure1c.DataStructure1C(utf_text)
        data.compose_text()
        self.assertEqual(utf_text, data.to_utf())


if __name__ == "__main__":
    unittest.main()
