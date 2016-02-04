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
import yaml
from .api import Base

log = logging.getLogger('macumba')


# https://github.com/juju/juju/blob/master/api/facadeversions.go
_FACADE_VERSIONS = {
    "Action":                       1,
    "Addresser":                    2,
    "Agent":                        2,
    "AgentTools":                   1,
    "AllWatcher":                   1,
    "AllModelWatcher":              2,
    "Annotations":                  2,
    "Backups":                      1,
    "Block":                        2,
    "Charms":                       2,
    "CharmRevisionUpdater":         1,
    "Client":                       1,
    "Cleaner":                      2,
    "Controller":                   2,
    "Deployer":                     1,
    "DiskManager":                  2,
    "EntityWatcher":                2,
    "FilesystemAttachmentsWatcher": 2,
    "Firewaller":                   2,
    "HighAvailability":             2,
    "ImageManager":                 2,
    "ImageMetadata":                2,
    "InstancePoller":               2,
    "KeyManager":                   1,
    "KeyUpdater":                   1,
    "LeadershipService":            2,
    "Logger":                       1,
    "MachineManager":               2,
    "Machiner":                     1,
    "MetricsManager":               1,
    "MeterStatus":                  1,
    "MetricsAdder":                 2,
    "ModelManager":                 2,
    "Networker":                    1,
    "NotifyWatcher":                1,
    "Pinger":                       1,
    "Provisioner":                  2,
    "ProxyUpdater":                 1,
    "Reboot":                       2,
    "RelationUnitsWatcher":         1,
    "Resumer":                      2,
    "Service":                      3,
    "Storage":                      2,
    "Spaces":                       2,
    "Subnets":                      2,
    "StatusHistory":                2,
    "StorageProvisioner":           2,
    "StringsWatcher":               1,
    "Upgrader":                     1,
    "UnitAssigner":                 1,
    "Uniter":                       3,
    "UserManager":                  1,
    "VolumeAttachmentsWatcher":     2,
    "Undertaker":                   1,
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
                                                   "models/cache.yaml"))
        output = [yaml.load(open(jenv_pat))]
        return output
