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

import logging
import os
import glob
import yaml
from .api import Base

log = logging.getLogger('macumba')

# https://github.com/juju/juju/blob/master/api/facadeversions.go
_FACADE_VERSIONS = {
    "Action":                       0,
    "Addresser":                    1,
    "Agent":                        1,
    "AllWatcher":                   0,
    "AllEnvWatcher":                1,
    "Annotations":                  1,
    "Backups":                      0,
    "Block":                        1,
    "Charms":                       1,
    "CharmRevisionUpdater":         0,
    "Client":                       0,
    "Cleaner":                      1,
    "Deployer":                     0,
    "DiskManager":                  1,
    "EntityWatcher":                1,
    "Environment":                  0,
    "EnvironmentManager":           1,
    "FilesystemAttachmentsWatcher": 1,
    "Firewaller":                   1,
    "HighAvailability":             1,
    "ImageManager":                 1,
    "ImageMetadata":                1,
    "InstancePoller":               1,
    "KeyManager":                   0,
    "KeyUpdater":                   0,
    "LeadershipService":            1,
    "Logger":                       0,
    "MachineManager":               1,
    "Machiner":                     0,
    "MetricsManager":               0,
    "Networker":                    0,
    "NotifyWatcher":                0,
    "Pinger":                       0,
    "Provisioner":                  1,
    "Reboot":                       1,
    "RelationUnitsWatcher":         0,
    "Resumer":                      1,
    "Rsyslog":                      0,
    "Service":                      1,
    "Storage":                      1,
    "Spaces":                       1,
    "Subnets":                      1,
    "StorageProvisioner":           1,
    "StringsWatcher":               0,
    "SystemManager":                1,
    "Upgrader":                     0,
    "Uniter":                       2,
    "UserManager":                  0,
    "VolumeAttachmentsWatcher":     1,
}


class JujuClient(Base):
    FACADE_VERSIONS = _FACADE_VERSIONS

    def cached_env(self, env='local'):
        """ Returns config path for a Juju environment

        Params:
        env: Optional juju environment
        """
        juju_home = os.getenv("JUJU_HOME", "~/.juju")
        jenv_pat = os.path.expanduser(os.path.join(juju_home,
                                                   "environments/*.jenv"))
        jenv_files = glob(jenv_pat)
        if len(jenv_files) == 0:
            return []
        else:
            output = [yaml.load(open(x) for x in jenv_files)]
            return output
