#!python3
# Copyright 2015 Canonical, Ltd.
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
import sys
import time
import threading

juju_home = os.getenv("JUJU_HOME", "~/.juju")
jenv_pat = os.path.expanduser(os.path.join(juju_home, "environments/*.jenv"))
jenv_files = glob(jenv_pat)
if len(jenv_files) == 0 or len(jenv_files) > 1:
    print("found 0 or >1 .jenv files, will ask for IP and password")
    wss_ip = input("juju api IP (with port):")
    jpass = getpass("juju password : ")
else:
    env = yaml.load(open(jenv_files[0]))
    wss_ip = env['state-servers'][0]
    jpass = env['password']

print('Connecting using wss ip ' + wss_ip)
j = JujuClient(url='wss://' + wss_ip, password=jpass)

j.login()

def loop_on_status(j, i):
    print("thread {} starting".format(i))
    if i == 0:
        time.sleep(3)
        j.reconnect()
        
    for idx in range(30):
        machines = j.status()['Machines']
        print("{} ".format(i), end="", flush=True)
        #sleeptime = 1 * ((i+1) * 0.1)
        sleeptime = 0.1
        time.sleep(sleeptime)
        assert len(machines) > 0
    print("thread {} done".format(i), flush=True)

NTHREADS = int(sys.argv[1])
threads = [threading.Thread(target=loop_on_status, args=(j, i))
           for i in range(NTHREADS)]
for thread in threads:
    thread.start()
    
for thread in threads:
    thread.join()
print('done')
