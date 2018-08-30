import sys
import os
import argparse
import json
import io
import logging
from pathlib import Path
import shutil

__ALL__ = ('Config', 'ServerConfig', 'ConfigException',
            'ServerConfig')
Log = logging.getLogger(__name__)

DefaultDefinitionFile               = Path(os.path.dirname(__file__), "data", "cmd_db.json")
DefaultTemplateFile                 = Path(os.path.dirname(__file__), "data", "default_config.json")
DefaultLocalConfigDirectory         = Path(Path.home(), ".pycubemx")
DefaultLocalConfigFile              = Path(DefaultLocalConfigDirectory, "config.json")
"""
DefaultLocalServerConfigFile        = Path(DefaultLocalConfigDirectory, "server.json")
DefaultLocalServerDataDirectory     = Path(DefaultLocalConfigDirectory, "server-data")
"""

def _json_parse_comments (f, *args, **kwargs):
    buf = io.StringIO()
    for i in f:
        if not i.strip().startswith("//"):
            buf.write(i)
    return json.loads(buf.getvalue())

#see here -- lazy merge!
#https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge/7205107
def _merge_dicts(dict1, dict2):
    """ Recursively merges dict2 into dict1 """
    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        return dict2
    for k in dict2:
        if k in dict1:
            dict1[k] = _merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1

def _buildKVObject (xclass, name, data, **kwargs):
    if data is not None:
        return xclass (name, data, **kwargs)
    else:
        return None

def _buildKVObjectSet (xclass, table, **kwargs):
    return [_buildKVObject(xclass, k, v, **kwargs) for k,v in table.items()]

def _get (conf, key, defaultValue = None):
    s = key.split('::') if isinstance(key, str) else key
    top = conf
    for i in s:
        if isinstance(top, dict) and i in top:
            top = top[i]
        else:
            return defaultValue
    return top

def _set (conf, key, value, onlyIfUndefined=False):
    s = key.split('::') if isinstance(key, str) else key
    top = conf
    skey = s[-1]
    s = s[0:-1]
    for i in s:
        if isinstance(top, dict):
            if i not in top:
                top[i] = {}
            top = top[i]
        else:
            raise Exception("Not a dict: " + "::".join(s) + " on " + i)
    if onlyIfUndefined and skey in top:
        return
    top [skey] = value

class ConfigException(Exception): pass

class Tool (object):
    def __init__ (self, name, config):
        self.name = name
        self._config = config

    @property
    def path(self):
        return os.path.join(self.path, self.command)

    @property
    def arguments (self):
        return tuple(_get(self._config, 'arguments', tuple()))

    @property
    def command (self):
        return _get(self._config, "command", None)

    @property
    def valid (self):
        return self.command is not None

    def __str__ (self):
        return "Tool<{self.name}: Valid={self.valid} Command={self.command} Arguments={self.arguments}>".format(self=self)

class VersionDetails (object):
    def __init__ (self, config):
        self.version = config["version"] if "version" in config else "Unknown Version"
        self.author = config["author"] if "author" in config else "Unknown Author"
        self.details = config["details"] if "details" in config else "Unknown Details"
    def __str__ (self):
        return "{self.version} by {self.author} - {self.details}".format(self=self)

class ServerConfig (object):
    def __init__ (self, config):
        self._config = config
        _set(self._config, ('server.socket_port',), 8333, onlyIfUndefined=True)
        _set(self._config, ('server.socket_host',), "127.0.0.1", onlyIfUndefined=True)
    @property
    def port (self):
        return _get(self._config, ('server.socket_port',))
    @property
    def host (self):
        return _get(self._config, ('server.socket_host',))
    @property
    def secret (self):
        return _get(self._config, ('secret',))
    @property
    def uri (self):
        return "http://{self.host}:{self.port}/".format(self=self)


class Config (object):
    LocalConfigFile = str(DefaultLocalConfigFile)

    @classmethod
    def LocalConfig (cls, configFile = None, nodefaults = False):
        c = cls ()

        Log.debug ("GetLocalConfig")

        if configFile is None:
            configFile = DefaultLocalConfigFile
            if not configFile.exists():
                Log.info("Copying configuration template...")
                Log.info("... from: " + str(DefaultTemplateFile))
                Log.info("... to:   " + str(DefaultLocalConfigFile))
                os.makedirs(DefaultLocalConfigDirectory, exist_ok=True)
                shutil.copy(str(DefaultTemplateFile), str(DefaultLocalConfigFile))

        if not nodefaults:
            Log.debug("Built-in command schema: Loading")
            c.loadFile(DefaultDefinitionFile, False)
        else:
            Log.debug("Built-in command schema: Skipping")

        Log.debug("Loading user config")
        c.loadFile(configFile)

        return c

    def __init__ (self):
        self._config = {}

    def loadFile (self, filename, merge = True):
        config = self._loadFile(filename)
        if not merge:
            self._config = config
        else:
            self._config = _merge_dicts(self._config, config)

    def _loadFile (self, filename):
        try:
            with open(filename, "r") as fd:
                return _json_parse_comments(fd)
        except json.JSONDecodeError as e:
            Log.exception("Error processing file input.")
            raise ConfigException("Error in JSON file: " + str(e))
        except Exception as e:
            Log.exception("Error reading or processing file input.")
            raise ConfigException("Error reading or processing file input")

    def dump (self):
        Log.debug("Configuration:\n" + json.dumps(self._config, indent=2))

    def saveFile (self, filename):
        with open(filename, "w") as f:
            json.dump(self._config, f, indent=2)

    def _get (self, key, defaultValue = None):
        s = key.split('::') if isinstance(key, str) else key
        top = self._config
        for i in s:
            if i in top:
                if isinstance(top[i], dict):
                    top = top[i]
                else:
                    return defaultValue
            else:
                return defaultValue
        return top

    def configureLogger (self, log):
        x = _get(self._config, ("log", log.name), True)
        lvl = logging.DEBUG if x is not False else logging.CRITICAL
        #Log.info("LogLevel {} -> {}".format(log.name, lvl))
        log.setLevel(lvl)

    @property
    def _apiSchema (self):
        return _get(self._config, ("cube", "schema"))

    @_apiSchema.setter
    def _apiSchema (self, value):
        cube = _set(self._config, ("cube", "schema"), value)

    @property
    def server (self):
        return ServerConfig(_get(self._config, ("server", ), {}))

    #def tools (self):
    #    return _buildKVObjectSet(Tool, _get(self._config, "tools"))

    @property
    def STM32CubeMX (self):
        return _buildKVObject(Tool, "STM32CubeMX", _get(self._config, ("STM32CubeMX",), {}))

    @property
    def commandDbVersionInfo (self):
        return VersionDetails(_get(self._config, ("command_db_version",), {}))
"""
class ServerConfig (object):
    LocalServerData         = str(DefaultLocalServerDataDirectory)
    @property
    def serverPort (self):
        return _get(self._config, ("server","port"), 8333)

    @property
    def serverBind (self):
        return _get(self._config, ("server","bind"), ["127.0.0.1"])

    @property
    def serverDataDir (self):
        return _get(self._config, ("server","data"), LocalServerData)
"""
