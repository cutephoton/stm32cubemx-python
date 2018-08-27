import sys
import os
import argparse
import json
import io
import logging

__ALL__ = ('Config','ConfigException','DefaultConfigFile','GetBaseConfig')
Log = logging.getLogger(__name__)
"""
prefix = None
stm32cubemx = None
if "STM32PATH" in os.environ:
    prefix = os.environ[STM32CUBEMX]

if "STM32CUBEMX" in os.environ:
    stm32cubemx = os.environ[STM32CUBEMX]
"""

DefaultConfigFile = os.path.join(os.path.dirname(__file__), "data/cmd_db.json")
def GetBaseConfig():
    c = Config ()
    c.loadFile(DefaultConfigFile, False)
    return c

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

def _set (conf, key, value):
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
    top [skey] = value

class ConfigException(Exception): pass

class Command (object):
    def __init__ (self, name, config, parent = None):
        self.name = name
        self._config = config
        self._parent = parent
    @property
    def command (self):
        return _get(self._config, 'command', None)
    @property
    def path(self):
        return os.path.join(self._parent.path, self.command)
    @property
    def arguments (self):
        return tuple(_get(self._config, 'arguments', tuple()))
    def __str__ (self):
        b = self.arguments
        cmd = self.path
        return "Command({} --> {} {})".format(self.name, cmd, " ".join(b))

class Tool (object):
    def __init__ (self, name, config):
        self.name = name
        self._config = config

    def commands (self):
        return _buildKVObjectSet(Command, _get(self._config, "commands", {}), parent = self)

    def command (self, cmd):
        return _buildKVObject(Command, cmd,_get(self._config, ("commands", cmd), {}), parent = self)

    @property
    def path (self):
        return _get(self._config, "path", "")

    def __str__ (self):
        return "Tool<" + self.name + " : " + self.path + ">"

class VersionDetails (object):
    def __init__ (self, config):
        self.version = config["version"] if "version" in config else "Unknown Version"
        self.author = config["author"] if "author" in config else "Unknown Author"
        self.details = config["details"] if "details" in config else "Unknown Details"
    def __str__ (self):
        return "{self.version} by {self.author} - {self.details}".format(self=self)
class Config (object):
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

    """def tool (self, name):
        t = self._get(('tools',name))
        if t is not None:
            return Tool(name, t)
        raise ConfigException("Tool " +name+ " not found.")"""\

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

    def tools (self):
        #if 'tools' not in self._config:
        #    return tuple()
        return _buildKVObjectSet(Tool, _get(self._config, "tools")) #[Tool(k, v) for k,v in self._get("tools", {}).items()]

    def tool (self,name):
        return _buildKVObject(Tool, name,_get(self._config, ("tools", name), {}))

    @property
    def commandDbVersionInfo (self):
        return VersionDetails(_get(self._config, ("command_db_version",), {}))
