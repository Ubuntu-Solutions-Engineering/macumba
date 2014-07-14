#!/usr/bin/env python3

import macumba
import os

PASSWORD = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(password=PASSWORD)
    j.login()
    j.deploy('keystone',
             dict(ConfigYAML=CHARMCONF,
                  NumUnits=1))

class MacumbaServiceTest(unittest.TestCase):
    def setUp(self):
        self.c = macumba.JujuClient(password=PASSWORD)
        self.c.login())

    def tearDown(self):
        self.c.close()

    def test_list_services(self):
        ret = self.c.status['Services']
        self.assertTrue(ret)

if __name__ == '__main__':
    unittest.main()
