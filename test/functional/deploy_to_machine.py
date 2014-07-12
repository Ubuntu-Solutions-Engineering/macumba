#!/usr/bin/env python3
import sys
sys.path.insert(0, '../macumba')
import macumba

JUJU_URL = 'wss://localhost:17070/'
JUJU_PASS = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(url=JUJU_URL, password=JUJU_PASS)
    j.login()
    properties = dict(ToMachineSpec="lxc:1", NumUnits=1)
    j.deploy('keystone', properties)
