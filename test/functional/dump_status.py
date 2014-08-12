#!/usr/bin/env python3
import sys
sys.path.insert(0, '../macumba')
import macumba
from pprint import pprint

JUJU_URL = 'wss://localhost:17070/'
JUJU_PASS = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(url=JUJU_URL, password=JUJU_PASS)
    j.login()
    ret = j.deploy('precise/wordpress', 'wordpress')
    pprint(ret)
