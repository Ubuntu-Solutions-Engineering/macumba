#
# Copyright 2014 Canonical, Ltd.
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

from ws4py.client.threadedclient import WebSocketClient
import json
import logging
import requests
from os import path
from queue import Queue

log = logging.getLogger('macumba')

creds = {'Type': 'Admin',
         'Request': 'Login',
         'RequestId': 1,
         'Params': {'AuthTag': 'user-admin',
                    'Password': None}}


def query_cs(charm, series='trusty'):
    """ This helper routine will query the charm store to pull latest revisions
    and charmstore url for the api.

    :param str charm: charm name
    :param str series: series, defaults. trusty
    """
    charm_store_url = 'https://manage.jujucharms.com/api/3/charm'
    url = path.join(charm_store_url, series, charm)
    r = requests.get(url)
    return r.json()


class Jobs:
    HostUnits = "JobHostUnits"
    ManageEnviron = "JobManageEnviron"
    ManageState = "JobManageState"


class JujuWS(WebSocketClient):
    def __init__(self, url, password, protocols=['https-only'],
                 extensions=None, ssl_options=None, headers=None):
        WebSocketClient.__init__(self, url, protocols, extensions,
                                 ssl_options=ssl_options, headers=headers)
        self.messages = Queue()

    def opened(self):
        self.send(json.dumps(creds))

    def received_message(self, m):
        self.messages.put(json.loads(m.data.decode('utf-8')))

    def closed(self, code, reason=None):
        self.messages.task_done()

    def receive(self):
        if self.terminated and self.messages.empty():
            return None
        message = self.messages.get()
        if message is StopIteration:
            return None
        return message


class JujuClient:
    def __init__(self, url='wss://localhost:17070', password='pass'):
        self.conn = JujuWS(url, password)
        self._request_id = 1
        creds['Params']['Password'] = password

    def _prepare_strparams(self, d):
        r = {}
        for k, v in d.items():
            r[k] = str(v)
        return r

    def _prepare_constraints(self, constraints):
        for k in ['cpu-cores', 'cpu-power', 'mem']:
            if constraints.get(k):
                constraints[k] = int(constraints[k])
        return constraints

    def login(self):
        self.conn.connect()
        self.conn.receive()

    def close(self):
        """ Closes connection to juju websocket """
        self.conn.close()

    def receive(self):
        res = self.conn.receive()
        return res['Response']

    def call(self, params):
        """ Get json data from juju api daemon

        :params params: Additional params to be passed into request
        :type params: dict
        """
        self._request_id = self._request_id + 1
        params['RequestId'] = self._request_id
        self.conn.send(json.dumps(params))
        return self.receive()

    def info(self):
        """ Returns Juju environment state """
        return self.call(dict(Type="Client",
                         Request="EnvironmentInfo"))

    def status(self):
        """ Returns status of juju environment """
        return self.call(dict(Type="Client",
                         Request="FullStatus"))

    def add_charm(self, charm_url):
        """ Adds charm """
        return self.call(dict(Type="Client",
                              Request="AddCharm",
                              Params=dict(URL=charm_url)))

    def get_charm(self, charm_url):
        """ Get charm """
        return self.call(dict(Type='Client',
                              Request='CharmInfo',
                              Params=dict(CharmURL=charm_url)))

    def get_env_constraints(self):
        """ Get environment constraints """
        return self.call(dict(Type="Client",
                              Request="GetEnvironmentConstraints"))

    def set_env_constraints(self, constraints):
        """ Set environment constraints """
        return self.call(dict(Type="Client",
                              Request="SetEnvironmentConstraints",
                              Params=constraints))

    def get_env_config(self):
        """ Get environment config """
        return self.call(dict(Type="Client",
                              Request="EnvironmentGet"))

    def set_env_config(self, config):
        """ Sets environment config variables """
        return self.call(dict(Type="Client",
                              Request="EnvironmentSet",
                              Params=dict(Config=config)))

    def add_machine(self, series="", constraints={},
                    machine_spec="", parent_id="", container_type=""):

        """Allocate a new machine from the iaas provider.
        """
        if machine_spec:
            err_msg = "Cant specify machine spec with container_type/parent_id"
            assert not (parent_id or container_type), err_msg
            parent_id, container_type = machine_spec.split(":", 1)

        params = dict(
            Series=series,
            ContainerType=container_type,
            ParentId=parent_id,
            Constraints=self._prepare_constraints(constraints),
            Jobs=[Jobs.HostUnits])
        return self.add_machines([params])

    def add_machines(self, machines):
        """ Add machines """
        return self.call(dict(Type="Client",
                         Request="AddMachines",
                         Params=dict(MachineParams=machines)))

    def destroy_machines(self, machine_ids, force=False):
        params = {"MachineNames": machine_ids}
        if force:
            params["Force"] = True
        return self.call(dict(Type="Client",
                              Request="DestroyMachines",
                              Params=params))

    def add_relation(self, endpoint_a, endpoint_b):
        """ Adds relation between units """
        return self.call(dict(Type="Client",
                              Request="AddRelation",
                              Params=dict(Endpoints=[endpoint_a,
                                                     endpoint_b])))

    def remove_relation(self, endpoint_a, endpoint_b):
        """ Removes relation """
        return self.call(dict(Type="Client",
                              Request="DestroyRelaiton",
                              Params=dict(Endpoints=[endpoint_a,
                                                     endpoint_b])))

    def deploy(self, service_name, settings={}):
        """ Deploy a charm to an instance

        :param str service_name: name of service
        :param dict settings: (optional) deploy settings
        """
        settings['ServiceName'] = service_name

        if not 'NumUnits' in settings:
            settings['NumUnits'] = 1

        if not 'CharmUrl' in settings:
            _url = query_cs(service_name)
            settings['CharmUrl'] = _url['charm']['url']

        if 'Constraints' in settings:
            settings['Constraints'] = self._prepare_constraints(
                settings['Constraints'])
        return self.call(dict(Type="Client",
                              Request="ServiceDeploy",
                              Params=dict(settings)))

    def set_config(self, service_name, config_keys):
        """ Sets machine config """
        return self.call(dict(Type="Client",
                              Request="ServiceSet",
                              Params=dict(ServiceName=service_name,
                                          Options=config_keys)))

    def unset_config(self, service_name, config_keys):
        """ Unsets machine config """
        return self.call(dict(Type="Client",
                              Request="ServiceUnset",
                              Params=dict(ServiceName=service_name,
                                          Options=config_keys)))

    def set_charm(self, service_name, charm_url, force=0):
        return self.call(dict(Type="Client",
                              Request="ServiceSetCharm",
                              Params=dict(ServiceName=service_name,
                                          CharmUrl=charm_url,
                                          Force=force)))

    def get_service(self, service_name):
        """ Get charm, config, constraits for srevice"""
        return self.call(dict(Type="Client",
                              Request="ServiceGet",
                              Params=dict(ServiceName=service_name)))

    def get_config(self, service_name):
        """ Get service configuration """
        svc = self.get_service(service_name)
        return svc['Config']

    def get_constraints(self, service_name):
        """ Get service constraints """
        return self.call(dict(Type="Client",
                              Request="GetServiceConstraints",
                              Params=dict(ServiceName=service_name)))

    def set_constraints(self, service_name, constraints):
        """ Sets service level constraints """
        return self.call(dict(Type="Client",
                              Request="SetServiceConstraints",
                              Params=dict(ServiceName=service_name,
                                          Constraints=constraints)))

    def update_service(self, service_name, charm_url, force_charm_url=0,
                       min_units=1, settings={}, constraints={}):
        """ Update service """
        return self.call(dict(Type="Client",
                              Request="SetServiceConstraints",
                              Params=dict(ServiceName=service_name,
                                          CharmUrl=charm_url,
                                          MinUnits=min_units,
                                          SettingsStrings=settings,
                                          Constraints=constraints)))

    def destroy_service(self, service_name):
        """ Destroy a service """
        return self.call(dict(Type="Client",
                              Request="ServiceDestroy",
                              Params=dict(ServiceName=service_name)))

    def expose(self, service_name):
        """ Expose a service """
        return self.call(dict(Type="Client",
                              Request="ServiceExpose",
                              Params=dict(ServiceName=service_name)))

    def unexpose(self, service_name):
        """ Unexpose service """
        return self.call(dict(Type="Client",
                              Request="ServiceUnexpose",
                              Params=dict(ServiceName=service_name)))

    def valid_relation_name(self, service_name):
        """ All possible relation names for service """
        return self.call(dict(Type="Client",
                              Request="ServiceCharmRelations",
                              Params=dict(ServiceName=service_name)))

    def add_units(self, service_name, num_units=1):
        """ Add units """
        return self.call(dict(Type="Client",
                              Request="AddServiceUnits",
                              Params=dict(ServiceName=service_name,
                                          NumUnits=num_units)))

    def add_unit(self, service_name, machine_spec=None, count=1):
        """ Add unit """
        return self.call(dict(Type="Client",
                              Request="AddServiceUnits",
                              Params=dict(ServiceName=service_name,
                                          ToMachineSpec=machine_spec,
                                          NumUnit=count)))

    def remove_unit(self, unit_names):
        """ Removes unit """
        return self.call(dict(Type="Client",
                              Request="DestroyServiceUnits",
                              Params=dict(UnitNames=unit_names)))

    def resolved(self, unit_name, retry=0):
        """ Resolved """
        return self.call(dict(Type="Client",
                              Request="Resolved",
                              Params=dict(UnitName=unit_name,
                                          Retry=retry)))

    def get_public_address(self, target):
        """ Gets public address of instance """
        return self.call(dict(Type="Client",
                              Request="PublicAddress",
                              Params=dict(Target=target)))

    def set_annontation(self, entity, entity_type, annotation):
        """ Sets annontation """
        return self.call(dict(Type="Client",
                              Request="SetAnnotations",
                              Params=dict(Tag="%-%s" % (entity_type, entity),
                                          Pairs=annotation)))

    def get_annotation(self, entity, entity_type):
        """ Gets annotation """
        return self.call(dict(Type="Client",
                              Request="GetAnnotation",
                              Params=dict(Tag="%-s%" % (entity_type,
                                                        entity))))
