"""
A RESTful API for Ceph
"""

# Global instance to share
instance = None

import json
import errno
import traceback

import api

from uuid import uuid4
from flask import Flask, request
from flask_restful import Api
from multiprocessing import Process

from helper import catch
from mgr_module import MgrModule



class Module(MgrModule):
    COMMANDS = [
            {
                "cmd": "enable_auth "
                       "name=val,type=CephChoices,strings=true|false",
                "desc": "Set whether to authenticate API access by key",
                "perm": "rw"
            },
            {
                "cmd": "auth_key_create "
                       "name=key_name,type=CephString",
                "desc": "Create an API key with this name",
                "perm": "rw"
            },
            {
                "cmd": "auth_key_delete "
                       "name=key_name,type=CephString",
                "desc": "Delete an API key with this name",
                "perm": "rw"
            },
            {
                "cmd": "auth_key_list",
                "desc": "List all API keys",
                "perm": "rw"
            },
    ]


    def __init__(self, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        global instance
        instance = self

        self.requests = []

        self.keys = {}
        self.enable_auth = True
        self.app = None
        self.api = None


    def on_completion(tag):
        pass


    def notify(self, notify_type, tag):
        if notify_type == "command":
            #self.requests.on_completion(tag)
            self.warn("tag: '%s'" % str(tag))
        else:
            self.log.debug("Unhandled notification type '%s'" % notify_type)
    #    elif notify_type in ['osd_map', 'mon_map', 'pg_summary']:
    #        self.requests.on_map(notify_type, self.get(notify_type))


    @catch
    def shutdown(self):
        self.server.terminate()


    @catch
    def serve(self):
        #self.keys = self._load_keys()
        self.enable_auth = self.get_config_json("enable_auth")
        if self.enable_auth is None:
            self.enable_auth = True

        self.app = Flask('ceph-mgr')
        self.app.config['RESTFUL_JSON'] = {
            'sort_keys': True,
            'indent': 4,
            'separators': (',', ': '),
        }
        self.api = Api(self.app)

        # Add the resources as defined in api module
        for _obj in dir(api):
            obj = getattr(api, _obj)
            try:
                _endpoint = getattr(obj, '_neverest_endpoint', None)
            except:
                _endpoint = None
            if _endpoint:
                self.api.add_resource(obj, _endpoint)

        self.log.warn('RUNNING THE SERVER')
        self.server = Process(target = self.app.run, kwargs = {
            'host': '0.0.0.0',
            'port': 8002,
        })
        self.server.start()
        self.server.join()
        self.log.warn('FINISHED RUNNING THE SERVER')


    def get_mons(self):
        mon_map_mons = self.get('mon_map')['mons']
        mon_status = json.loads(self.get('mon_status')['json'])

        # Add more information
        for mon in mon_map_mons:
            mon['in_quorum'] = mon['rank'] in mon_status['quorum']
            mon['server'] = self.get_metadata("mon", mon['name'])['hostname']
            mon['leader'] = mon['rank'] == mon_status['quorum'][0]

        return mon_map_mons


    def handle_command(self, cmd):
        self.log.info("handle_command: {0}".format(json.dumps(cmd, indent=2)))
        prefix = cmd['prefix']
        if prefix == "enable_auth":
            enable = cmd['val'] == "true"
            self.set_config_json("enable_auth", enable)
            self.enable_auth = enable
            return 0, "", ""
        elif prefix == "auth_key_create":
            if cmd['key_name'] in self.keys:
                return 0, self.keys[cmd['key_name']], ""
            else:
                self.keys[cmd['key_name']] = self._generate_key()
                self._save_keys()

            return 0, self.keys[cmd['key_name']], ""
        elif prefix == "auth_key_delete":
            if cmd['key_name'] in self.keys:
                del self.keys[cmd['key_name']]
                self._save_keys()

            return 0, "", ""
        elif prefix == "auth_key_list":
            return 0, json.dumps(self._load_keys(), indent=2), ""
        else:
            return -errno.EINVAL, "", "Command not found '{0}'".format(prefix)
