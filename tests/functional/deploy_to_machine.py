#!/usr/bin/env python3

import macumba

PASSWORD = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(password=PASSWORD)
    j.login()
    j.deploy('mysql')
    properties = dict(ToMachineSpec="lxc:1")
    j.deploy('keystone', properties)
