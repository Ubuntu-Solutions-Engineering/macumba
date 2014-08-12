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
#
# Usage:
# juju bootstrap
# nose test

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
class MacumbaServiceTest(unittest.TestCase):
    def test_services(self):
        ret = c.status()['Services']
        self.assertTrue(ret)


@unittest.skipIf(not IS_CONNECTED, 'Not connected.')
class MacumbaAddUnitTest(unittest.TestCase):
    def test_add_unit(self):
        ret = c.add_unit('nova-compute')
        self.assertTrue(len(ret['Units']) == 1)
