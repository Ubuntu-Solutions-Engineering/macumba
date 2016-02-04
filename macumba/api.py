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

import time
import os.path as path
import requests
import logging
import threading
from .errors import (LoginError,
                     CharmNotFoundError,
                     RequestTimeout,
                     ServerError,
                     BadResponseError,
                     MacumbaError)
from .ws import JujuWS
from .jobs import Jobs

log = logging.getLogger('macumba')


def query_cs(charm):
    """ This helper routine will query the charm store to pull latest revisions
    and charmstore url for the api.

    :param str charm: charm name, can be in the form of 'precise/<charm>' to
                      specify an alternate series.
    """
    try:
        series, charm = charm.split('/')
    except ValueError:
        series = 'trusty'
    charm_store_url = 'https://manage.jujucharms.com/api/3/charm'
    url = path.join(charm_store_url, series, charm)
    r = requests.get(url)
    if r.status_code != 200:
        log.error("could not find charm store URL for charm '{}'".format(url))
        rj = r.json()
        raise CharmNotFoundError("{type} {charm_id}".format(**rj))

    return r.json()


class Base:
    """ Base api class
    """
    FACADE_VERSIONS = {}

    def __init__(self, url, password, user='user-admin'):
        """ init

        Params:
        url: URL in form of wss://{api-endpoint}/model/{uuid}/api
        password: Password for user
        user: juju user with access to endpoint
        """
        self.url = url
        self.password = password
        self.connlock = threading.RLock()
        with self.connlock:
            self.conn = JujuWS(url, password)

        self.creds = {'Type': 'Admin',
                      'Version': 2,
                      'Request': 'Login',
                      'RequestId': 1,
                      'Params': {'auth-tag': user,
                                 'credentials': password}}

    def _prepare_strparams(self, d):
        r = {}
        for k, v in d.items():
            r[k] = str(v)
        return r

    def _prepare_constraints(self, constraints):
        for k in ['cpu-cores', 'cpu-power', 'mem', 'root-disk']:
            if constraints.get(k):
                constraints[k] = int(constraints[k])
        return constraints

    def login(self):
        """Connect and log in to juju websocket endpoint.

        block other threads until done.
        """
        with self.connlock:
            req_id = self.conn.do_connect(self.creds)
            try:
                res = self.receive(req_id)
                if 'Error' in res:
                    raise LoginError(res['ErrorCode'])
            except Exception as e:
                raise LoginError(str(e))

    def reconnect(self):
        with self.connlock:
            self.close()
            start_id = self.conn.get_current_request_id() + 1
            self.conn = JujuWS(self.url,
                               self.password,
                               start_reqid=start_id)
            self.login()

    def close(self):
        """ Closes connection to juju websocket """
        with self.connlock:
            self.conn.do_close()

    def receive(self, request_id, timeout=None):
        """receives expected message.

        returns parsed response object.

        if timeout is set, raises RequestTimeout after 'timeout' seconds
        with no received message.

        """
        res = None
        start_time = time.time()
        while res is None:
            with self.connlock:
                res = self.conn.do_receive(request_id)
            if res is None:
                time.sleep(0.1)
                if timeout and (time.time() - start_time > timeout):
                    raise RequestTimeout(request_id)

        if 'Error' in res:
            raise ServerError(res['Error'], res)

        try:
            return res['Response']
        except:
            raise BadResponseError("Failed to parse response: {}".format(res))

    def call(self, params, timeout=None):
        """ Get json data from juju api daemon.

        :params params: Additional params to be passed into request
        :type params: dict
        """
        if params['Type'] in self.FACADE_VERSIONS:
            params.update({'Version': self.FACADE_VERSIONS[params['Type']]})
        else:
            raise MacumbaError(
                'Unknown facade type: {}'.format(params['Type']))
        print(params)
        with self.connlock:
            req_id = self.conn.do_send(params)

        return self.receive(req_id, timeout)

    def info(self):
        """ Returns Juju environment state """
        return self.call(dict(Type="Client",
                              Request="EnvironmentInfo"))

    def status(self):
        """ Returns status of juju environment """
        return self.call(dict(Type="Client",
                              Request="FullStatus"),
                         timeout=60)

    def get_watcher(self):
        """ Returns watcher """
        return self.call(dict(Type="Client",
                              Request="WatchAll"))

    def get_watched_tasks(self, watcher_id):
        """ Returns a list of all watches for Id """
        return self.call(dict(Type="AllWatcher",
                              Request="Next",
                              Id=watcher_id))

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
        try:
            rv = self.call(dict(Type="Client",
                                Request="AddRelation",
                                Params=dict(Endpoints=[endpoint_a,
                                                       endpoint_b])))
        except ServerError as e:
            # do not treat pre-existing relations as exceptions:
            if 'relation already exists' in e.response['Error']:
                rv = e.response
            else:
                raise e

        return rv

    def remove_relation(self, endpoint_a, endpoint_b):
        """ Removes relation """
        return self.call(dict(Type="Client",
                              Request="DestroyRelaiton",
                              Params=dict(Endpoints=[endpoint_a,
                                                     endpoint_b])))

    def deploy(self, charm, service_name, num_units=1, config_yaml="",
               constraints=None, machine_spec=""):
        """ Deploy a charm to an instance

        :param str charm: Name of charm
        :param str service_name: name of service
        :param int num_units: number of units
        :param str config_yaml: charm configuration options
        :param dict constraints: deploy constraints
        :param str machine_spec: Type of machine to deploy to
        :returns: Deployed charm status
        """
        params = {'ServiceName': service_name}

        _url = query_cs(charm)
        params['CharmUrl'] = _url['charm']['url']
        params['NumUnits'] = num_units
        params['ConfigYAML'] = config_yaml

        if constraints:
            params['Constraints'] = self._prepare_constraints(
                constraints)
        if machine_spec:
            params['ToMachineSpec'] = machine_spec
        return self.call(dict(Type="Service",
                              Request="ServiceDeploy",
                              Params=dict(params)))

    def set_config(self, service_name, config_keys):
        """ Sets machine config """
        return self.call(dict(Type="Service",
                              Request="ServiceSet",
                              Params=dict(ServiceName=service_name,
                                          Options=config_keys)))

    def unset_config(self, service_name, config_keys):
        """ Unsets machine config """
        return self.call(dict(Type="Service",
                              Request="ServiceUnset",
                              Params=dict(ServiceName=service_name,
                                          Options=config_keys)))

    def set_charm(self, service_name, charm_url, force=0):
        return self.call(dict(Type="Service",
                              Request="ServiceSetCharm",
                              Params=dict(ServiceName=service_name,
                                          CharmUrl=charm_url,
                                          Force=force)))

    def get_service(self, service_name):
        """ Get charm, config, constraits for srevice"""
        return self.call(dict(Type="Service",
                              Request="ServiceGet",
                              Params=dict(ServiceName=service_name)))

    def get_config(self, service_name):
        """ Get service configuration """
        svc = self.get_service(service_name)
        return svc['Config']

    def get_constraints(self, service_name):
        """ Get service constraints """
        return self.call(dict(Type="Service",
                              Request="GetServiceConstraints",
                              Params=dict(ServiceName=service_name)))

    def set_constraints(self, service_name, constraints):
        """ Sets service level constraints """
        return self.call(dict(Type="Service",
                              Request="SetServiceConstraints",
                              Params=dict(ServiceName=service_name,
                                          Constraints=constraints)))

    def update_service(self, service_name, charm_url, force_charm_url=0,
                       min_units=1, settings={}, constraints={}):
        """ Update service """
        return self.call(dict(Type="Service",
                              Request="SetServiceConstraints",
                              Params=dict(ServiceName=service_name,
                                          CharmUrl=charm_url,
                                          MinUnits=min_units,
                                          SettingsStrings=settings,
                                          Constraints=constraints)))

    def destroy_service(self, service_name):
        """ Destroy a service """
        return self.call(dict(Type="Service",
                              Request="ServiceDestroy",
                              Params=dict(ServiceName=service_name)))

    def expose(self, service_name):
        """ Expose a service """
        return self.call(dict(Type="Service",
                              Request="ServiceExpose",
                              Params=dict(ServiceName=service_name)))

    def unexpose(self, service_name):
        """ Unexpose service """
        return self.call(dict(Type="Service",
                              Request="ServiceUnexpose",
                              Params=dict(ServiceName=service_name)))

    def valid_relation_name(self, service_name):
        """ All possible relation names for service """
        return self.call(dict(Type="Service",
                              Request="ServiceCharmRelations",
                              Params=dict(ServiceName=service_name)))

    def add_unit(self, service_name, num_units=1, machine_spec=""):
        """ Add unit

        :param str service_name: Name of charm
        :param int num_units: Number of units
        :param str machine_spec: Type of machine to deploy to
        :returns dict: Units added
        """
        params = {}
        params['ServiceName'] = service_name
        params['NumUnits'] = num_units
        if machine_spec:
            params['ToMachineSpec'] = machine_spec

        return self.call(dict(Type="Service",
                              Request="AddServiceUnits",
                              Params=dict(params)))

    def remove_unit(self, unit_names):
        """ Removes unit """
        return self.call(dict(Type="Service",
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

    def set_annotations(self, entity, entity_type, annotation):
        """ Sets annotations.
        :param dict annotation: dict with string pairs.
        """
        return self.call(dict(Type="Client",
                              Request="SetAnnotations",
                              Params=dict(Tag="%s-%s" % (entity_type, entity),
                                          Pairs=annotation)))

    def get_annotations(self, entity, entity_type):
        """ Gets annotations """
        return self.call(dict(Type="Client",
                              Request="GetAnnotations",
                              Params=dict(Tag="%s-%s" % (entity_type,
                                                         entity))))
