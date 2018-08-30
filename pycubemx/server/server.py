import cherrypy
import logging
from pycubemx.config import Config
from pycubemx.native import MxConnection
import io

Log = logging.getLogger(__name__)

cherrypy.config.update({
    'global': {
       'engine.autoreload.on' : False
     }
 })

class NotAuthorized (object): pass

class CubeMXApi(object):
    def __init__ (self, config):
        self._config = config
        self._secret = config.server.secret
        Log.info("Command DB Version: " + str(self._config.commandDbVersionInfo))
        self._session = MxConnection(self._config)

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type']='text/plain; charset=utf-8'
        s = io.StringIO()
        self._session.dump(lambda x: s.write(x + "\n"), includeHelp=True)
        return s.getvalue()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def schema(self):
        try:
            self.check()
            return {"status": "success", "result" : self._config._apiSchema}
        except Exception as e:
            return {"status": "failure", "exception" : str(e)}

    def check(self):
        req = cherrypy.request.json
        if self._secret is None:
            return
        secret = None
        if 'secret' in req:
            secret = req['secret']
        if secret != self._secret:
            raise Exception("Not authroized")

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def disconnect(self):
        try:
            self.check()
            req = cherrypy.request.json
            self._session.disconnect()
            return {"status": "success"}
        except Exception as e:
            return {"status": "failure", "exception" : str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def shutdown(self):
        try:
            self.check()
            cherrypy.engine.exit()
            return {"status": "success"}
        except Exception as e:
            return {"status": "failure", "exception" : str(e)}
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def sessioncmd(self):
        try:
            self.check()
            req = cherrypy.request.json
            #value = input_json["my_key"]
            if "api" in req:
                api = req ["api"].split("::")
                args = [] if "args" not in req else req["args"]
                obj = self._session._getcall(api)
                if obj is None:
                    return {"status":"failure", "exception":"API not defined."}
                elif obj._callable:
                    result = obj(*args)
                    return {"status": "success", "is_ns_call" : False, "result" : result}
                else:
                    s = io.StringIO()
                    obj._dump(lambda x: s.write(x + "\n"), includeHelp=True)
                    return {"status": "success", "is_ns_call" : True, "result" : s.getvalue().split("\n")}
            return {"status": "failure", "exception" : "Unhandled Path"}
        except Exception as e:
            return {"status": "failure", "exception" : str(e)}



def runServer (config):
    cherrypy.config.update(config.server._config)
    cherrypy.quickstart(CubeMXApi(config))
