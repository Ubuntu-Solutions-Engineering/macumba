# Copyright 2014-2016 Canonical, Ltd.
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

from getpass import getpass

from .v2 import JujuClient
import yaml
import os
from code import interact


def main():
    juju_home = os.getenv("JUJU_HOME", "~/.juju")
    jenv_pat = os.path.expanduser(os.path.join(juju_home,
                                               "models/cache.yaml"))
    if not os.path.isfile(jenv_pat):
        wss_ip = input("juju api IP (with port):")
        jpass = getpass("juju password : ")
    else:
        env = yaml.load(open(jenv_pat))
        uuid = env['server-user']['local']['server-uuid']
        wss_ip = env['server-data'][uuid]['api-endpoints'][0]
        jpass = env['server-data'][uuid]['identities']['admin']

    url = os.path.join('wss://', wss_ip, 'model', uuid, 'api')
    print('Connecting using ' + url)
    j = JujuClient(url=url, password=jpass)

    j.login()

    interact(banner="juju client logged in. Object is named 'j',"
             " so j.status() will fetch current status as a dict.",
             local=locals())
