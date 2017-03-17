from flask import request
from flask_restful import Resource

import json
import traceback

## We need this to access the instance of the module
#
# We can't use 'from module import instance' because
# the instance is not ready, yet (would be None)
import module

OSD_FLAGS = ('pause', 'noup', 'nodown', 'noout', 'noin', 'nobackfill', 'norecover', 'noscrub', 'nodeep-scrub')

# Catch and log the exceptions
def catch(f):
    def catcher(*args, **kwargs):
        module.instance.log.error("Calling a function")
        try:
            return f(*args, **kwargs)
        except:
            module.instance.log.error(str(traceback.format_exc()))
    return catcher



class Index(Resource):
    _neverest_endpoint = '/'

    @catch
    def get(self):
        return "Root of cluster RESTful API"



class ClusterConfig(Resource):
    _neverest_endpoint = '/cluster/config'

    @catch
    def get(self):
        return module.instance.get("config")



class ClusterConfigKey(Resource):
    _neverest_endpoint = '/cluster/config/<string:key>'

    @catch
    def get(self, key):
        return module.instance.get("config").get(key, None)



class ClusterServer(Resource):
    _neverest_endpoint = '/cluster/server'

    @catch
    def get(self):
        return module.instance.list_servers()



class ClusterServerFqdn(Resource):
    _neverest_endpoint = '/cluster/server/<string:fqdn>'

    @catch
    def get(self, fqdn):
        return module.instance.get_server(fqdn)



class ClusterMon(Resource):
    _neverest_endpoint = '/cluster/mon'

    @catch
    def get(self):
        return module.instance.get_mons()



class ClusterMonName(Resource):
    _neverest_endpoint = '/cluster/mon/<string:name>'

    @catch
    def get(self, name):
        mons = filter(lambda x: x['name'] == name, module.instance.get_mons())
        if len(mons) != 1:
                return None
        return mons[0]



class ClusterOsd(Resource):
    _neverest_endpoint = '/cluster/osd'



class ClusterOsdConfig(Resource):
    _neverest_endpoint = '/cluster/osd/config'

    @catch
    def get(self):
        return module.instance.get("osd_map")['flags']


    @catch
    def patch(self):
        attributes = json.loads(request.data)

        commands = []

        osd_map_flags = module.instance.get('osd_map')['flags']

        flags_not_implemented = set(attributes.keys()) - set(OSD_FLAGS)
        if flags_not_implemented:
            module.instance.log.error("%s not valid to set/unset" % list(flags_not_implemented))

        flags_to_set = set(k for k, v in attributes.iteritems() if v) - flags_not_implemented
        flags_to_unset = set(k for k, v in attributes.iteritems() if not v) - flags_not_implemented
        flags_that_are_set = set(osd_map_flags.split(','))

        for x in flags_to_set - flags_that_are_set:
            commands.append({
                'prefix': 'osd set',
                'key': x,
            })

        for x in flags_that_are_set & flags_to_unset:
            commands.append({
                'prefix': 'osd unset',
                'key': x,
            })

        module.instance.log.warn(str(commands))
        #module.instance.requests[]
        return commands
