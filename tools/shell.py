#!/usr/bin/env python3
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

from getpass import getpass

from macumba import JujuClient
import yaml 
from glob import glob
import os

jenv_files = glob(os.path.expanduser("~/.juju/environments/*.jenv"))
if len(jenv_files) == 0 or len(jenv_files) > 1:
    print("found 0 or >1 .jenv files, will ask for IP and password")
    wss_ip = input("juju api IP (with port):")
    jpass = getpass("juju password : ")
else:
    env = yaml.load(open(jenv_files[0]))
    wss_ip = env['state-servers'][0]
    jpass = env['password']

j = JujuClient(url='wss://' + wss_ip, password=jpass)

j.login()

from code import interact
interact(banner="juju client logged in. Object is named 'j',"
         " so j.status() will fetch current status as a dict.",
         local=locals())
