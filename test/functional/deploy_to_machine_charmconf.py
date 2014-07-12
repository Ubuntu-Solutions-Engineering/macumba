#!/usr/bin/env python3
import sys
sys.path.insert(0, '../macumba')
import macumba

PASSWORD = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(password=PASSWORD)
    j.login()
    j.deploy('keystone',
             dict(ConfigYAML='keystone:\n  admin-pass: pass',
                  NumUnits=1))
