#!/usr/bin/env python3

import macumba

PASSWORD = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(password=PASSWORD)
    j.login()
    properties = dict(ToMachineSpec="lxc:1", NumUnits=1)
    j.deploy('keystone', properties)
