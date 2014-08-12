# Copyright 2014 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import unittest
import sys
sys.path.insert(0, '../macumba')

import macumba

IS_CONNECTED = False
JUJU_URL = 'wss://localhost:17070/'
JUJU_PASS = 'pass'

c = macumba.JujuClient(url=JUJU_URL, password=JUJU_PASS)
try:
    c.login()
    IS_CONNECTED = True
except:
    pass


@unittest.skipIf(not IS_CONNECTED, 'Not connected.')
class MacumbaDeploySingleTest(unittest.TestCase):
    def tearDown(self):
        c.destroy_machines(['1'])

    def test_deploy(self):
        ret = c.deploy('mysql', 'mysql')
        self.assertTrue(not ret)

    def test_deploy_to(self):
        c.add_machine()
        ret = c.deploy('precise/wordpress', 'wordpress', machine_spec='lxc:1')
        self.assertTrue(not ret)
