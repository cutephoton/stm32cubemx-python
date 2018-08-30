import json
import urllib
import logging

Log = logging.getLogger(__name__)

__ALL__ = ('MxRemoteClient', 'MxRemoteException')

class MxRemoteException(Exception): pass

class VBase(object):
    def __init__ (self, top, config, parent = None):
        #self._path = []
        self._parent = parent
        self._top = top
        self._name = config['name']
        self._config = config
        if parent is not None:
            self._path = parent._path + [self._name]
        else:
            self._path = []
    @property
    def _apiPath (self):
        return "::".join(self._path)

class VNamespace(VBase):
    def __init__ (self, *args, **argskw):
        super().__init__(*args, **argskw)
        for i in self._config['children']:
            if i['type'] == 'Namespace':
                ns = VNamespace(self._top, i, self)
                setattr(self, ns._name, ns)
            elif i['type'] == 'Caller':
                caller = VCaller(self._top, i, self)
                #self._children[ns._name] = ns._name
                setattr(self, caller._name, caller)

class VCaller(VBase):
    def __init__ (self, *args, **argskw):
        super().__init__(*args, **argskw)
    def __call__ (self, *args):
        top = self._top
        rc = top._apiReq(self._apiPath, args)
        if rc["status"] != 'success':
            raise MxRemoteException("Remote Exception: " + rc['exception'])
        else:
            return rc['result']

class MxRemoteClient(object):
    def __init__ (self, config):
        self._config = config
        self._serviceuri = self._config.server.uri
        self._schema = {}
        self._ns = None
        self._secret = config.server.secret

    def _uri (self, uri = None):
        #postfix = "?key=" + (self._secret if self._secret is not None else "")
        postfix = ""
        if uri is None:
            return self._serviceuri + postfix
        return self._serviceuri + uri + postfix

    def _simpleReq(self, uri):
        """uri = self._uri(uri)
        Log.debug ("REQ: " + uri)
        return urllib.request.urlopen(uri)"""

        uri = self._uri(uri)
        Log.debug ("SIMPLE-REQ: {}".format(uri))
        params = json.dumps({"secret" : self._secret}).encode('utf8')
        req = urllib.request.Request(uri, data=params,headers={'content-type': 'application/json'})
        return urllib.request.urlopen(req)

    def _apiReq(self, api, args):
        uri = self._uri("sessioncmd")
        Log.debug ("API-REQ: {} -> {}".format(uri, api))
        params = json.dumps({"api" : api, "args" : args,"secret" : self._secret}).encode('utf8')
        req = urllib.request.Request(uri, data=params,headers={'content-type': 'application/json'})
        response = urllib.request.urlopen(req)
        respData = response.read().decode('utf8')
        return json.loads(respData)

    def directAPI (self, api, *args):
        rc =  self._apiReq(api, args)
        if rc["status"] != 'success':
            raise MxRemoteException("Remote Exception: " + rc['exception'])
        else:
            return rc['result']

    def disconnect (self):
        with self._simpleReq("disconnect") as response:
            rc = json.loads(response.read().decode('utf8'))
            if rc['status'] != 'success':
                raise MxRemoteException("Remote Exception: " + rc['exception'])

    def shutdown (self):
        with self._simpleReq("shutdown") as response:
            rc = json.loads(response.read().decode('utf8'))
            if rc['status'] != 'success':
                raise MxRemoteException("Remote Exception: " + rc['exception'])

    def init (self):
        with self._simpleReq("schema") as response:
            rc = json.loads(response.read().decode('utf8'))
            if rc['status'] != 'success':
                raise MxRemoteException("Remote Exception: " + rc['exception'])
            self._schema = rc['result']
            self._ns = VNamespace(self,self._schema)
            #Log.info(str(self._schema))

    def usage (self):
        with self._simpleReq(None) as response:
            result = response.read().decode('utf8')
            return result

    def __getattr__(self, name):
        return getattr(self._ns, name)

        #newConditions = {"con1":40, "con2":20, "con3":99, "con4":40, "password":"1234"}
        #params = json.dumps(newConditions).encode('utf8')
        #req = urllib.request.Request(conditionsSetURL, data=params,
        #                             headers={'content-type': 'application/json'})
        #response = urllib.request.urlopen(req)
        #req = urllib.request.Request(conditionsSetURL
