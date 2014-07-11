#!/usr/bin/env python3

import macumba
import os

PASSWORD = 'pass'
CHARMCONF = os.path.abspath(os.path.join(__file__,
                                         '../../data/charmconf.yaml'))

if __name__ == "__main__":
    j = macumba.JujuClient(password=PASSWORD)
    j.login()
    j.deploy('keystone',
             dict(ConfigYAML=CHARMCONF,
                  NumUnits=1))
