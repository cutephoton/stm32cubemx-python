import logging
import json
import argparse
from pathlib import Path
import sys
import re
#Ugh... I need to rework the configuration section...
from ..config import Config
from ..native import MxConnection, Namespace, Caller

__ALL__ = ('Metadata', 'Command', 'Scanner')

RE_COMMAND_MANAGER_ADD = re.compile(r'CommandLineManager\.addCommand\s*\(\s*["\'](.*?)["\']\s*,\s*["\'](.*?)["\']\s*,\s*(.*?),')

class Metadata (object):
    def __init__ (self, file, start, end, content):
        self.file = file
        self.start = start
        self.end = end
        self.content = content

class Command (object):
    def __init__ (self, name, description, arguments, meta):
        self._name = name
        self.description = description
        self.argcount = arguments
        self.meta = meta
        self.path = name.split(' ')
        self.pathstr = '::'.join(self.path)

    @property
    def namespace (self):
        return self.path[0:-1]

    @property
    def name (self):
        return self.path[-1]

    def __str__ (self):
        return "Command({self.pathstr}, '{self.description}', argCount={self.argcount})".format(self=self)

class Scanner (object):
    def __init__ (self):
        self._searchpaths = []
        self._files = []
        self._commands = []

    def addPath (self, path):
        self._searchpaths.append(Path(path))

    def start (self):
        for i in self._searchpaths:
            for javafiles in i.rglob("*.java"):
                self._scan(javafiles.resolve())

    def _scan(self, javafile):
        self._files.append(javafile)
        with open(javafile, 'r') as fd:
            src = fd.read()
            for i in RE_COMMAND_MANAGER_ADD.finditer(src):
                meta = Metadata(javafile, i.start(), i.end(), i.group(0))
                self._commands.append(Command(i.group(1), i.group(2), int(i.group(3)), meta))

    @property
    def commands(self):
        return self._commands

    def createConfig (self):
        c = Config()
        mx = MxConnection(c)
        for i in self._commands:
            ns = mx._makeNamespace(i.namespace)
            caller = Caller(i.name, i.argcount, help=i.description)
            ns._addChild(caller)
            caller.set_top(mx)
        c._apiSchema = mx._ns._serialize ()
        return c
