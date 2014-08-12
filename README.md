# macumba

python3 bindings for juju

# Usage

This example demonstrates how to deploy Openstack Keystone into Juju

```python
#!/usr/bin/env python3
import sys
import macumba

JUJU_URL = 'wss://localhost:17070/'
JUJU_PASS = 'pass'

if __name__ == "__main__":
    j = macumba.JujuClient(url=JUJU_URL, password=JUJU_PASS)
    j.login()
    j.deploy('keystone')
```

# Authors

2014 Adam Stokes <adam.stokes@ubuntu.com>

# Copyright

2014 Canonical, Ltd.

# License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
